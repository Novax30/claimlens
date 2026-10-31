"""Load and validate ClaimLens analysis requests."""

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Union


class InputValidationError(ValueError):
    """Raised when an analysis request is missing required information."""


@dataclass(frozen=True)
class ReportInput:
    title: str
    body: str
    kind: str = "issue"


@dataclass(frozen=True)
class AnalysisRequest:
    repository_path: Path
    report: ReportInput


def _require_non_empty_string(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise InputValidationError(f"{field_name} must be a non-empty string")
    return value.strip()


def load_request(path: Union[str, Path]) -> AnalysisRequest:
    """Read one JSON request and validate its required fields."""
    request_path = Path(path)
    try:
        data = json.loads(request_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise InputValidationError(f"request file not found: {request_path}") from exc
    except json.JSONDecodeError as exc:
        raise InputValidationError(f"request file is not valid JSON: {request_path}") from exc

    if not isinstance(data, dict):
        raise InputValidationError("request must be a JSON object")

    repository_path = _require_non_empty_string(data.get("repository_path"), "repository_path")
    report = data.get("report")
    if not isinstance(report, dict):
        raise InputValidationError("report must be a JSON object")

    title = _require_non_empty_string(report.get("title"), "report.title")
    body = _require_non_empty_string(report.get("body"), "report.body")
    kind = report.get("kind", "issue")
    if kind not in {"issue", "pull_request"}:
        raise InputValidationError("report.kind must be issue or pull_request")

    return AnalysisRequest(
        repository_path=Path(repository_path),
        report=ReportInput(title=title, body=body, kind=kind),
    )
