"""Render ClaimLens findings as a traceable Markdown report."""

from typing import Iterable, List

from .evidence_analyzer import EvidenceAssessment
from .evidence_collector import Evidence
from .input_reader import ReportInput
from .quality_checker import assess_report_quality


def render_markdown_report(
    report: ReportInput,
    assessments: Iterable[EvidenceAssessment],
    evidence: Iterable[Evidence],
    repository_commit: str = "unavailable",
) -> str:
    """Render a report with model findings and the original evidence lines."""
    assessment_list: List[EvidenceAssessment] = list(assessments)
    evidence_list: List[Evidence] = list(evidence)
    quality = assess_report_quality(report)
    lines = [
        "# ClaimLens Assessment",
        "",
        f"## Report\n\n**Type:** {report.kind}\n\n**Title:** {report.title}\n",
        f"**Repository commit:** `{repository_commit}`",
        "",
        report.body,
        "",
        "## Report quality",
        "",
        f"**Status:** `{quality.status}`",
        "",
    ]
    if quality.missing:
        lines.append("**Missing information:**")
        lines.append("")
        lines.extend(f"- {item}" for item in quality.missing)
        lines.append("")
    else:
        lines.extend(["No obvious investigation details are missing.", ""])
    lines.extend(
        [
        "## Findings",
        "",
        ]
    )

    if not assessment_list:
        lines.append("No claims were extracted.")
    for index, assessment in enumerate(assessment_list, start=1):
        lines.extend(
            [
                f"### Claim {index}",
                "",
                f"**Claim:** {assessment.claim}",
                "",
                f"**Assessment:** `{assessment.assessment}`",
                "",
                f"**Confidence:** `{assessment.confidence}`",
                "",
                f"**Execution:** `{assessment.execution_status}`",
                "",
                f"**Explanation:** {assessment.explanation}",
                "",
                "**Cited evidence:**",
                "",
            ]
        )
        refs = assessment.evidence_refs
        if refs:
            lines.extend(f"- `{reference}`" for reference in refs)
        else:
            lines.append("- No exact evidence reference was provided.")
        lines.append("")

    lines.extend(["## Evidence", ""])
    if not evidence_list:
        lines.append("No relevant evidence was found.")
    else:
        for item in evidence_list:
            lines.append(f"- `{item.file}:{item.line}` ({item.category}): {item.text}")

    lines.extend(
        [
            "",
            "## Review note",
            "",
            "This report assists a maintainer. It is not an automatic decision to close, reject, or publish anything.",
            "",
        ]
    )
    return "\n".join(lines)
