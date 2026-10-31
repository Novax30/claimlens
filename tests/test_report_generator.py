from claimlens.evidence_analyzer import EvidenceAssessment
from claimlens.evidence_collector import Evidence
from claimlens.input_reader import ReportInput
from claimlens.report_generator import render_markdown_report


def test_render_markdown_report_contains_findings_and_exact_evidence():
    report = ReportInput("Negative timeout values", "The project rejects negative values.", "pull_request")
    assessment = EvidenceAssessment(
        claim="Negative timeout values are rejected",
        assessment="supported",
        confidence="high",
        explanation="The validation rejects values below one.",
        evidence_refs=["src/config.py:12"],
    )
    evidence = [Evidence("src/config.py", 12, "if timeout <= 0:", "source")]

    markdown = render_markdown_report(report, [assessment], evidence)

    assert "# ClaimLens Assessment" in markdown
    assert "**Type:** pull_request" in markdown
    assert "**Repository commit:** `unavailable`" in markdown
    assert "`supported`" in markdown
    assert "**Execution:** `not_attempted`" in markdown
    assert "`src/config.py:12`" in markdown
    assert "if timeout <= 0:" in markdown
    assert "not an automatic decision" in markdown


def test_render_markdown_report_handles_empty_results():
    markdown = render_markdown_report(ReportInput("Empty", "No claim."), [], [])

    assert "No claims were extracted." in markdown
    assert "No relevant evidence was found." in markdown
