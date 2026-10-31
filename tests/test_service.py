import json

from claimlens.claim_extractor import Claim
from claimlens.evidence_analyzer import EvidenceAssessment
from claimlens.input_reader import load_request
from claimlens.service import ClaimLensService


class FakeService(ClaimLensService):
    def __init__(self):
        pass

    def analyze_request(self, request, base_dir="."):
        from claimlens.pipeline import analyze_request

        class FakeExtractor:
            def extract_claims(self, report):
                return [Claim("Negative values are rejected", "configuration")]

        class FakeAnalyzer:
            def analyze(self, claim, evidence):
                return EvidenceAssessment(
                    claim=claim.text,
                    assessment="supported",
                    confidence="high",
                    explanation="Evidence supports the claim.",
                    evidence_refs=["src/config.py:12"],
                )

        return analyze_request(request, FakeExtractor(), FakeAnalyzer(), base_dir=base_dir)


def test_service_provides_ui_independent_markdown():
    service = FakeService()
    result = service.analyze_file("input/example_request.json")

    markdown = service.to_markdown(result)

    assert "# ClaimLens Assessment" in markdown
    assert "Evidence supports the claim." in markdown
