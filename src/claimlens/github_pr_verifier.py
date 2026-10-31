"""Fetch one GitHub PR into a temporary checkout and run its tests."""

from dataclasses import dataclass
from pathlib import Path
import subprocess
import tempfile
from typing import Sequence

from .github_api import GitHubClient, GitHubAPIError, parse_repository
from .verification_runner import VerificationResult, run_repository_tests


@dataclass(frozen=True)
class PullRequestVerification:
    number: int
    commit_sha: str
    result: VerificationResult


def verify_github_pull_request(
    repository: str,
    number: int,
    client: GitHubClient,
    command: Sequence[str] = ("python", "-m", "pytest", "-q"),
    timeout_seconds: int = 120,
) -> PullRequestVerification:
    """Read and test a PR branch in disposable directories.

    This performs a Git clone/fetch only. It never pushes, comments, merges, or
    changes the remote repository.
    """
    repo = parse_repository(repository)
    pull = client.get_pull_request(repository, number)
    head = pull.get("head")
    sha = head.get("sha") if isinstance(head, dict) else None
    if not isinstance(sha, str) or not sha:
        raise GitHubAPIError("GitHub PR did not include a head commit SHA")

    remote = f"https://github.com/{repo.owner}/{repo.name}.git"
    with tempfile.TemporaryDirectory(prefix="claimlens-pr-") as temp_name:
        checkout = Path(temp_name) / "repository"
        _run_git(["clone", "--depth", "1", remote, str(checkout)], timeout=180)
        _run_git(
            ["-C", str(checkout), "fetch", "--depth", "1", "origin", f"pull/{number}/head"],
            timeout=180,
        )
        _run_git(["-C", str(checkout), "checkout", "--detach", "FETCH_HEAD"], timeout=60)
        result = run_repository_tests(
            checkout,
            command=command,
            timeout_seconds=timeout_seconds,
        )
        return PullRequestVerification(number=number, commit_sha=sha, result=result)


def _run_git(command: Sequence[str], timeout: int) -> None:
    try:
        completed = subprocess.run(
            ["git", *command],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except (OSError, subprocess.SubprocessError) as error:
        raise GitHubAPIError(f"could not prepare PR checkout: {error}") from error
    if completed.returncode != 0:
        details = (completed.stderr or completed.stdout or "git command failed").strip()
        raise GitHubAPIError(f"could not prepare PR checkout: {details[-1000:]}")
