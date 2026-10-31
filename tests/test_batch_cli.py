from pathlib import Path

from claimlens.batch_cli import render_summary
from claimlens.batch_runner import BatchResult
from claimlens.claim_extractor import Claim
from claimlens.evidence_analyzer import EvidenceAssessment
from claimlens.input_reader import AnalysisRequest, ReportInput
from claimlens.pipeline import AnalysisResult


def test_render_summary_marks_matches_and_reviews():
    request = AnalysisRequest(Path("."), ReportInput("Title", "Body"))
    supported = AnalysisResult(
        request=request,
        claims=[Claim("Claim", "behavior")],
        evidence=[],
        assessments=[EvidenceAssessment("Claim", "supported", "high", "Explanation", [])],
    )
    uncertain = AnalysisResult(
        request=request,
        claims=[Claim("Claim", "behavior")],
        evidence=[],
        assessments=[EvidenceAssessment("Claim", "uncertain", "low", "Explanation", [])],
    )

    summary = render_summary(
        [
            BatchResult("one", "supported", supported),
            BatchResult("two", "contradicted", uncertain),
        ]
    )

    assert "| `one` | `supported` | `supported` | `match` |" in summary
    assert "| `two` | `contradicted` | `uncertain` | `review` |" in summary
