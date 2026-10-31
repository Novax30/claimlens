"""Local JSON API adapter for future chat, editor, and GitHub clients."""

import json
from pathlib import Path
from typing import Any, Dict, Union

from .input_reader import AnalysisRequest, InputValidationError, ReportInput
from .service import ClaimLensService


def request_from_api_payload(payload: Dict[str, Any]) -> AnalysisRequest:
    if not isinstance(payload, dict):
        raise InputValidationError("API payload must be a JSON object")
    repository_path = payload.get("repository_path")
    report = payload.get("report")
    if not isinstance(repository_path, str) or not repository_path.strip():
        raise InputValidationError("repository_path must be a non-empty string")
    if not isinstance(report, dict):
        raise InputValidationError("report must be a JSON object")
    kind = report.get("kind", "issue")
    title = report.get("title")
    body = report.get("body")
    if not isinstance(kind, str) or kind not in {"issue", "pull_request"}:
        raise InputValidationError("report.kind must be issue or pull_request")
    if not isinstance(title, str) or not title.strip():
        raise InputValidationError("report.title must be a non-empty string")
    if not isinstance(body, str) or not body.strip():
        raise InputValidationError("report.body must be a non-empty string")
    return AnalysisRequest(
        repository_path=Path(repository_path),
        report=ReportInput(title=title.strip(), body=body.strip(), kind=kind),
    )


def analyze_api_payload(
    payload: Dict[str, Any],
    service: ClaimLensService,
    workspace: Union[str, Path] = ".",
) -> Dict[str, Any]:
    request = request_from_api_payload(payload)
    result = service.analyze_request(request, base_dir=workspace)
    return {
        "report_markdown": service.to_markdown(result),
        "claims": len(result.claims),
        "evidence_lines": len(result.evidence),
        "repository_commit": result.repository_commit,
        "assessments": [
            {
                "claim": item.claim,
                "assessment": item.assessment,
                "confidence": item.confidence,
                "execution_status": item.execution_status,
                "evidence_refs": item.evidence_refs,
            }
            for item in result.assessments
        ],
    }
