"""Batch triage for multiple saved GitHub pull-request payloads."""

from dataclasses import dataclass
import json
from pathlib import Path
from typing import List, Union

from .github_adapter import request_from_github_payload
from .quality_checker import assess_report_quality
from .service import ClaimLensService


@dataclass(frozen=True)
class PRQueueItem:
    number: str
    title: str
    priority: str
    status: str
    assessment: str
    confidence: str
    missing: List[str]


def _escape_table_cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ").replace("\r", " ")


def _classify(result, request, number: str) -> PRQueueItem:
    quality = assess_report_quality(request.report)
    assessments = result.assessments
    # A title is often only a label. Prefer the strongest claim finding so a
    # useful body claim is not hidden by an uncertain title claim.
    rank = {
        ("contradicted", "high"): 0,
        ("supported", "high"): 1,
        ("contradicted", "medium"): 2,
        ("supported", "medium"): 3,
        ("uncertain", "low"): 4,
    }
    strongest = min(
        assessments,
        key=lambda item: rank.get((item.assessment, item.confidence), 5),
        default=None,
    )
    assessment = strongest.assessment if strongest else "uncertain"
    confidence = strongest.confidence if strongest else "low"

    if assessment == "contradicted" and confidence == "high":
        priority, status = "high", "needs_review"
    elif quality.status == "incomplete" or assessment == "uncertain":
        priority, status = "medium", "needs_information"
    else:
        priority, status = "low", "lower_priority"

    return PRQueueItem(
        number=number,
        title=request.report.title,
        priority=priority,
        status=status,
        assessment=assessment,
        confidence=confidence,
        missing=quality.missing,
    )


def analyze_pr_queue(
    payload_dir: Union[str, Path],
    repository_path: str,
    service: ClaimLensService,
    workspace: Union[str, Path] = ".",
) -> List[PRQueueItem]:
    items: List[PRQueueItem] = []
    for path in sorted(Path(payload_dir).glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload.get("pull_request"), dict):
            continue
        request = request_from_github_payload(payload, repository_path)
        number = str(payload["pull_request"].get("number", path.stem))
        result = service.analyze_request(request, base_dir=workspace)
        items.append(_classify(result, request, number))

    return sorted(items, key=lambda item: {"high": 0, "medium": 1, "low": 2}[item.priority])


def render_queue_markdown(items: List[PRQueueItem], repository: str = "") -> str:
    lines = [
        "# ClaimLens PR Review Queue",
        "",
        f"**Repository:** `{_escape_table_cell(repository) or 'local'}`",
        "",
        "| PR | Title | Priority | Status | Assessment | Confidence | Missing details |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for item in items:
        missing = ", ".join(item.missing) if item.missing else "None detected"
        lines.append(
            f"| #{_escape_table_cell(item.number)} | {_escape_table_cell(item.title)} | "
            f"`{_escape_table_cell(item.priority)}` | `{_escape_table_cell(item.status)}` | "
            f"`{_escape_table_cell(item.assessment)}` | `{_escape_table_cell(item.confidence)}` | "
            f"{_escape_table_cell(missing)} |"
        )
    lines.extend(
        [
            "",
            "This queue is advisory. A maintainer must review the evidence before taking action.",
            "",
        ]
    )
    return "\n".join(lines)
