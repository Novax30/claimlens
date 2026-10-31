"""Read-only GitHub API client used by the live PR queue."""

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import time
from typing import Any, Dict, List, Optional
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


class GitHubAPIError(RuntimeError):
    """Raised when GitHub cannot be read safely."""


@dataclass(frozen=True)
class GitHubRepository:
    owner: str
    name: str


def parse_repository(value: str) -> GitHubRepository:
    parts = value.strip().strip("/").split("/")
    if len(parts) != 2 or not all(parts):
        raise GitHubAPIError("repository must use the OWNER/REPOSITORY format")
    return GitHubRepository(owner=parts[0], name=parts[1])


class GitHubClient:
    """Fetch public or token-authorized PR metadata without writing to GitHub."""

    def __init__(
        self,
        token: Optional[str] = None,
        api_url: str = "https://api.github.com",
        cache_dir: Optional[str] = ".claimlens-cache",
        cache_ttl: int = 300,
    ):
        self.token = token or os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
        self.api_url = api_url.rstrip("/")
        self.cache_dir = Path(cache_dir) if cache_dir else None
        self.cache_ttl = max(0, cache_ttl)
        self.rate_limit_remaining: Optional[int] = None
        self.rate_limit_reset: Optional[int] = None

    def list_pull_requests(self, repository: str, state: str = "open") -> List[Dict[str, Any]]:
        repo = parse_repository(repository)
        if state not in {"open", "closed", "all"}:
            raise GitHubAPIError("state must be open, closed, or all")

        results: List[Dict[str, Any]] = []
        page = 1
        while True:
            path = (
                f"/repos/{quote(repo.owner)}/{quote(repo.name)}/pulls"
                f"?state={state}&per_page=100&page={page}"
            )
            payload = self._get_json(path)
            if not isinstance(payload, list):
                raise GitHubAPIError("GitHub returned an unexpected pull-request response")
            results.extend(item for item in payload if isinstance(item, dict))
            if len(payload) < 100:
                return results
            page += 1

    def list_pull_request_files(self, repository: str, number: int) -> List[Dict[str, Any]]:
        repo = parse_repository(repository)
        if number < 1:
            raise GitHubAPIError("pull-request number must be positive")
        results: List[Dict[str, Any]] = []
        page = 1
        while True:
            path = (
                f"/repos/{quote(repo.owner)}/{quote(repo.name)}/pulls/{number}/files"
                f"?per_page=100&page={page}"
            )
            payload = self._get_json(path)
            if not isinstance(payload, list):
                raise GitHubAPIError("GitHub returned an unexpected pull-request files response")
            results.extend(item for item in payload if isinstance(item, dict))
            if len(payload) < 100:
                return results
            page += 1

    def get_pull_request(self, repository: str, number: int) -> Dict[str, Any]:
        repo = parse_repository(repository)
        if number < 1:
            raise GitHubAPIError("pull-request number must be positive")
        payload = self._get_json(f"/repos/{quote(repo.owner)}/{quote(repo.name)}/pulls/{number}")
        if not isinstance(payload, dict):
            raise GitHubAPIError("GitHub returned an unexpected pull-request response")
        return payload

    def _get_json(self, path: str) -> Any:
        cache_path = self._cache_path(path)
        if cache_path and cache_path.exists():
            try:
                cached = json.loads(cache_path.read_text(encoding="utf-8"))
                if time.time() - float(cached["created"]) <= self.cache_ttl:
                    return cached["payload"]
            except (KeyError, TypeError, ValueError, OSError):
                pass

        if (
            self.rate_limit_remaining == 0
            and self.rate_limit_reset
            and time.time() < self.rate_limit_reset
        ):
            raise GitHubAPIError("GitHub rate limit reached; retry after the reset time")

        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "ClaimLens/0.1",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        request = Request(self.api_url + path, headers=headers, method="GET")
        try:
            with urlopen(request, timeout=20) as response:
                self._record_rate_limit(response)
                payload = json.loads(response.read().decode("utf-8"))
                if cache_path:
                    try:
                        cache_path.parent.mkdir(parents=True, exist_ok=True)
                        cache_path.write_text(
                            json.dumps({"created": time.time(), "payload": payload}),
                            encoding="utf-8",
                        )
                    except OSError:
                        pass
                return payload
        except HTTPError as error:
            if error.code in {401, 403}:
                raise GitHubAPIError(
                    "GitHub denied the request; check GITHUB_TOKEN permissions and rate limits"
                ) from error
            if error.code == 404:
                raise GitHubAPIError("repository was not found or is not accessible") from error
            raise GitHubAPIError(f"GitHub API returned HTTP {error.code}") from error
        except (URLError, TimeoutError, json.JSONDecodeError) as error:
            raise GitHubAPIError(f"could not read GitHub: {error}") from error

    def _cache_path(self, path: str) -> Optional[Path]:
        if self.cache_dir is None or self.cache_ttl == 0:
            return None
        key = hashlib.sha256((self.api_url + path).encode("utf-8")).hexdigest()
        return self.cache_dir / f"{key}.json"

    def _record_rate_limit(self, response: Any) -> None:
        headers = getattr(response, "headers", {})
        remaining = headers.get("X-RateLimit-Remaining")
        reset = headers.get("X-RateLimit-Reset")
        try:
            self.rate_limit_remaining = int(remaining) if remaining is not None else None
            self.rate_limit_reset = int(reset) if reset is not None else None
        except (TypeError, ValueError):
            self.rate_limit_remaining = None
            self.rate_limit_reset = None
