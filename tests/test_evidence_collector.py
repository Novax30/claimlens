import json

import pytest

from claimlens.evidence_collector import EvidenceCollectionError, collect_evidence
from claimlens.input_reader import load_request


def test_collect_evidence_returns_traceable_matches():
    request = load_request("input/example_request.json")

    evidence = collect_evidence(request)

    assert evidence
    assert any(item.file == "src/config.py" for item in evidence)
    assert any(item.category == "test" for item in evidence)
    assert all(item.line > 0 for item in evidence)
    assert all(item.text for item in evidence)


def test_collect_evidence_respects_max_results(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    (project / "notes.md").write_text("timeout\n" * 10, encoding="utf-8")
    request_path = tmp_path / "request.json"
    request_path.write_text(
        json.dumps(
            {
                "repository_path": "project",
                "report": {"title": "Timeout", "body": "timeout"},
            }
        ),
        encoding="utf-8",
    )

    evidence = collect_evidence(load_request(request_path), base_dir=tmp_path, max_results=3)

    assert len(evidence) == 3


def test_collect_evidence_rejects_missing_project():
    request = load_request("input/example_request.json")

    with pytest.raises(EvidenceCollectionError, match="not found"):
        collect_evidence(request, base_dir="does-not-exist")
