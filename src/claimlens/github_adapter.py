"""Convert GitHub issue and pull-request payloads into ClaimLens requests."""

from pathlib import Path
from typing import Any, Dict

from .input_reader import AnalysisRequest, InputValidationError, ReportInput


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise InputValidationError(f"GitHub payload field {field} must be a non-empty string")
    return value.strip()


def request_from_github_payload(
    payload: Dict[str, Any],
    repository_path: str,
) -> AnalysisRequest:
    """Create a local request from an issue or pull-request payload.

    This adapter only reads payload data. It never contacts GitHub or posts
    anything back to a repository.
    """
    if not isinstance(payload, dict):
        raise InputValidationError("GitHub payload must be a JSON object")

    if isinstance(payload.get("issue"), dict):
        item = payload["issue"]
        kind = "issue"
    elif isinstance(payload.get("pull_request"), dict):
        item = payload["pull_request"]
        kind = "pull_request"
    else:
        raise InputValidationError("payload must contain issue or pull_request")

    title = _text(item.get("title"), f"{kind}.title")
    # GitHub represents a PR with no description as JSON null. Keep it
    # analyzable while preserving strict validation for explicitly empty text.
    raw_body = item.get("body")
    body = "(No description provided.)" if raw_body is None else _text(raw_body, f"{kind}.body")
    return AnalysisRequest(
        repository_path=Path(repository_path),
        report=ReportInput(title=title, body=body, kind=kind),
    )
