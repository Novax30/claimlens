from claimlens.claim_extractor import Claim
from claimlens.evidence_analyzer import EvidenceAssessment
from claimlens.input_reader import load_request
from claimlens.pipeline import analyze_request


class FakeClaimExtractor:
    def extract_claims(self, report):
        return [Claim("Negative timeout values are rejected", "configuration")]


class FakeEvidenceAnalyzer:
    def analyze(self, claim, evidence):
        assert evidence
        return EvidenceAssessment(
            claim=claim.text,
            assessment="supported",
            confidence="high",
            explanation="The sample evidence supports the claim.",
            evidence_refs=["src/config.py:12"],
        )


def test_analyze_request_runs_all_core_steps():
    request = load_request("input/example_request.json")

    result = analyze_request(request, FakeClaimExtractor(), FakeEvidenceAnalyzer())

    assert len(result.claims) == 1
    assert result.evidence
    assert result.assessments[0].assessment == "supported"
