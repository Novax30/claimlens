import json

from claimlens.claim_extractor import Claim
from claimlens.evidence_analyzer import EvidenceAnalyzer
from claimlens.evidence_collector import Evidence
from claimlens.ollama_client import OllamaClient


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def read(self):
        return json.dumps(self.payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def test_empty_evidence_is_uncertain_without_calling_model():
    def unexpected_opener(request, timeout):
        raise AssertionError("model should not be called without evidence")

    analyzer = EvidenceAnalyzer(OllamaClient("deepseek-coder:6.7b", opener=unexpected_opener))

    result = analyzer.analyze(Claim("Negative values are rejected", "configuration"), [])

    assert result.assessment == "uncertain"
    assert result.confidence == "low"


def test_evidence_analyzer_parses_model_assessment():
    def fake_opener(request, timeout):
        return FakeResponse(
            {
                "message": {
                    "content": json.dumps(
                        {
                            "assessment": "supported",
                            "confidence": "high",
                            "explanation": "The validation line rejects values below one.",
                            "evidence_refs": ["src/config.py:12"],
                        }
                    )
                }
            }
        )

    evidence = [Evidence("src/config.py", 12, "if timeout <= 0:", "source")]
    analyzer = EvidenceAnalyzer(OllamaClient("deepseek-coder:6.7b", opener=fake_opener))

    result = analyzer.analyze(Claim("Negative values are rejected", "configuration"), evidence)

    assert result.assessment == "supported"
    assert result.confidence == "high"
    assert "validation" in result.explanation
    assert result.evidence_refs == ["src/config.py:12"]


def test_invalid_model_assessment_becomes_uncertain():
    def fake_opener(request, timeout):
        return FakeResponse(
            {
                "message": {
                    "content": json.dumps(
                        {
                            "assessment": "definitely true",
                            "confidence": "certain",
                            "explanation": "",
                            "evidence_refs": ["README.md:5"],
                        }
                    )
                }
            }
        )

    evidence = [Evidence("README.md", 5, "Timeout must be positive.", "documentation")]
    analyzer = EvidenceAnalyzer(OllamaClient("deepseek-coder:6.7b", opener=fake_opener))

    result = analyzer.analyze(Claim("Timeout must be positive", "configuration"), evidence)

    assert result.assessment == "uncertain"
    assert result.confidence == "low"


def test_direct_rejection_evidence_overrides_model_mistake():
    def fake_opener(request, timeout):
        return FakeResponse(
            {
                "message": {
                    "content": json.dumps(
                        {
                            "assessment": "supported",
                            "confidence": "high",
                            "explanation": "The model made the wrong call.",
                            "evidence_refs": ["src/config.py:12"],
                        }
                    )
                }
            }
        )

    evidence = [
        Evidence("src/config.py", 12, "raise ValueError('timeout must be greater than zero')", "source")
    ]
    analyzer = EvidenceAnalyzer(OllamaClient("deepseek-coder:6.7b", opener=fake_opener))

    result = analyzer.analyze(Claim("The timeout accepts negative values", "configuration"), evidence)

    assert result.assessment == "contradicted"
    assert result.confidence == "high"
    assert "Direct validation evidence" in result.explanation
