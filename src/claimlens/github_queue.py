"""Connect read-only GitHub PR metadata and patches to the ClaimLens queue."""

import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List

from .github_adapter import request_from_github_payload
from .github_api import GitHubAPIError, GitHubClient
from .evidence_collector import Evidence
from .input_reader import InputValidationError
from .ollama_client import OllamaError
from .pr_queue import PRQueueItem, _classify
from .service import ClaimLensService


def _diff_evidence(files: List[Dict[str, Any]]) -> List[Evidence]:
    """Turn added/context lines from GitHub patches into traceable evidence."""
    evidence: List[Evidence] = []
    for file in files:
        filename = file.get("filename")
        patch = file.get("patch")
        if not isinstance(filename, str) or not isinstance(patch, str):
            continue
        new_line = 0
        for raw_line in patch.splitlines():
            hunk = re.match(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@", raw_line)
            if hunk:
                new_line = int(hunk.group(1))
                continue
            if raw_line.startswith("+") and not raw_line.startswith("+++"):
                evidence.append(Evidence(
                    file=f"PR diff/{filename}",
                    line=new_line or 1,
                    text=raw_line[1:].strip(),
                    category="pull_request",
                ))
                new_line += 1
            elif not raw_line.startswith("-") and not raw_line.startswith("\\"):
                new_line += 1
    return evidence


def analyze_github_prs(
    repository: str,
    repository_path: str,
    service: ClaimLensService,
    client: GitHubClient,
    state: str = "open",
    max_workers: int = 4,
) -> List[PRQueueItem]:
    if max_workers < 1:
        raise ValueError("max_workers must be positive")
    pull_requests = client.list_pull_requests(repository, state=state)

    def analyze_one(pull_request: Dict[str, Any]) -> PRQueueItem:
        payload: Dict[str, Any] = {"pull_request": pull_request}
        request = request_from_github_payload(payload, repository_path)
        number = str(pull_request.get("number", "unknown"))
        files = client.list_pull_request_files(repository, int(number))
        result = service.analyze_request(
            request,
            base_dir=".",
            extra_evidence=_diff_evidence(files),
        )
        return _classify(result, request, number)

    items: List[PRQueueItem] = []
    worker_count = min(max_workers, len(pull_requests)) or 1
    with ThreadPoolExecutor(max_workers=worker_count) as executor:
        futures = {
            executor.submit(analyze_one, pull_request): pull_request
            for pull_request in pull_requests
        }
        for future in as_completed(futures):
            pull_request = futures[future]
            try:
                items.append(future.result())
            except (GitHubAPIError, InputValidationError, OllamaError, OSError, ValueError):
                items.append(PRQueueItem(
                    number=str(pull_request.get("number", "unknown")),
                    title=str(pull_request.get("title", "Untitled PR")),
                    priority="high",
                    status="analysis_failed",
                    assessment="uncertain",
                    confidence="low",
                    missing=["automatic analysis failed; inspect this PR manually"],
                ))

    return sorted(
        items,
        key=lambda item: (
            {"high": 0, "medium": 1, "low": 2}[item.priority],
            int(item.number) if item.number.isdigit() else 0,
        ),
    )
