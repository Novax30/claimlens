"""Connect read-only GitHub PR metadata and patches to the ClaimLens queue."""

import re
from typing import Any, Dict, List

from .github_adapter import request_from_github_payload
from .github_api import GitHubClient
from .evidence_collector import Evidence
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
) -> List[PRQueueItem]:
    items: List[PRQueueItem] = []
    for pull_request in client.list_pull_requests(repository, state=state):
        payload: Dict[str, Any] = {"pull_request": pull_request}
        request = request_from_github_payload(payload, repository_path)
        number = str(pull_request.get("number", "unknown"))
        files = client.list_pull_request_files(repository, int(number))
        result = service.analyze_request(
            request,
            base_dir=".",
            extra_evidence=_diff_evidence(files),
        )
        items.append(_classify(result, request, number))

    return sorted(items, key=lambda item: {"high": 0, "medium": 1, "low": 2}[item.priority])
