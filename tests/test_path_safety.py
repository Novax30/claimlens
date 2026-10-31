import json

import pytest

from claimlens.evidence_collector import EvidenceCollectionError, collect_evidence
from claimlens.input_reader import load_request


def test_evidence_collector_rejects_path_outside_base_dir(tmp_path):
    request_path = tmp_path / "request.json"
    request_path.write_text(
        json.dumps(
            {
                "repository_path": "../outside",
                "report": {"title": "Timeout", "body": "timeout"},
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(EvidenceCollectionError, match="inside base_dir"):
        collect_evidence(load_request(request_path), base_dir=tmp_path / "workspace")
