"""Check whether an issue or pull request contains useful investigation details."""

from dataclasses import dataclass
from typing import List

from .input_reader import ReportInput


@dataclass(frozen=True)
class ReportQuality:
    status: str
    missing: List[str]


def assess_report_quality(report: ReportInput) -> ReportQuality:
    text = f"{report.title}\n{report.body}".lower()
    missing = []

    if not any(term in text for term in ("reproduc", "steps", "command", "example")):
        missing.append("reproduction steps or an example")
    if not any(term in text for term in ("expected", "actual", "should", "instead")):
        missing.append("expected versus actual behavior")
    if not any(term in text for term in ("version", "python", "dependency", "operating system", "os: ")):
        missing.append("version or environment information")

    return ReportQuality(
        status="complete" if not missing else "incomplete",
        missing=missing,
    )
