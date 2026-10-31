import pytest

from claimlens.api_adapter import analyze_api_payload, request_from_api_payload
from claimlens.input_reader import InputValidationError
from claimlens.service import ClaimLensService


def test_api_payload_becomes_request():
    request = request_from_api_payload(
        {
            "repository_path": "examples/sample_project",
            "report": {"kind": "issue", "title": "Timeout", "body": "Negative values are accepted."},
        }
    )

    assert request.report.kind == "issue"
    assert request.report.title == "Timeout"


def test_api_payload_runs_through_offline_service():
    result = analyze_api_payload(
        {
            "repository_path": "examples/sample_project",
            "report": {"kind": "issue", "title": "Timeout", "body": "Negative values are accepted."},
        },
        ClaimLensService(offline=True),
    )

    assert result["claims"] > 0
    assert result["evidence_lines"] > 0
    assert any(item["assessment"] == "contradicted" for item in result["assessments"])
    assert all(item["execution_status"] == "not_attempted" for item in result["assessments"])


def test_api_payload_rejects_missing_report():
    with pytest.raises(InputValidationError, match="report"):
        request_from_api_payload({"repository_path": "examples/sample_project"})
