import pytest

from claimlens.github_adapter import request_from_github_payload
from claimlens.input_reader import InputValidationError


def test_issue_payload_becomes_issue_request():
    request = request_from_github_payload(
        {"issue": {"title": "Timeout bug", "body": "Negative timeout is accepted."}},
        "examples/sample_project",
    )

    assert request.report.kind == "issue"
    assert request.report.title == "Timeout bug"


def test_pull_request_payload_becomes_pull_request_request():
    request = request_from_github_payload(
        {"pull_request": {"title": "Fix timeout", "body": "Reject negative values."}},
        "examples/sample_project",
    )

    assert request.report.kind == "pull_request"


def test_github_adapter_rejects_unknown_payload():
    with pytest.raises(InputValidationError, match="issue or pull_request"):
        request_from_github_payload({"comment": {}}, "examples/sample_project")


def test_github_adapter_rejects_empty_body():
    with pytest.raises(InputValidationError, match="body"):
        request_from_github_payload({"issue": {"title": "Bug", "body": ""}}, "examples/sample_project")
