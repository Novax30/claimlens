import json

import pytest

from claimlens.input_reader import InputValidationError, load_request


def test_load_request_reads_valid_input(tmp_path):
    request_path = tmp_path / "request.json"
    request_path.write_text(
        json.dumps(
            {
                "repository_path": "examples/sample_project",
                "report": {
                    "title": "Negative timeout values are rejected",
                    "body": "The project rejects negative timeout values.",
                    "kind": "pull_request",
                },
            }
        ),
        encoding="utf-8",
    )

    request = load_request(request_path)

    assert request.repository_path.as_posix() == "examples/sample_project"
    assert request.report.title == "Negative timeout values are rejected"
    assert request.report.kind == "pull_request"


def test_load_request_rejects_empty_report(tmp_path):
    request_path = tmp_path / "request.json"
    request_path.write_text(
        json.dumps(
            {
                "repository_path": "examples/sample_project",
                "report": {"title": "", "body": ""},
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(InputValidationError, match="report.title"):
        load_request(request_path)


def test_load_request_rejects_missing_file(tmp_path):
    with pytest.raises(InputValidationError, match="not found"):
        load_request(tmp_path / "missing.json")
