"""Run a small labeled dataset and report simple, honest metrics."""

import json
from pathlib import Path
from typing import Any, Dict, Union

from .input_reader import AnalysisRequest, ReportInput
from .service import ClaimLensService


def evaluate_dataset(
    dataset_path: Union[str, Path],
    service: ClaimLensService,
    repository_path: str = "examples/sample_project",
    base_dir: Union[str, Path] = ".",
) -> Dict[str, Any]:
    cases = json.loads(Path(dataset_path).read_text(encoding="utf-8"))
    if not isinstance(cases, list) or not cases:
        raise ValueError("evaluation dataset must be a non-empty JSON list")

    correct = 0
    cited = 0
    results = []
    for case in cases:
        request = AnalysisRequest(
            repository_path=Path(repository_path),
            report=ReportInput(
                title=case["title"],
                body=case["body"],
                kind=case.get("kind", "issue"),
            ),
        )
        result = service.analyze_request(request, base_dir=base_dir)
        finding = result.assessments[0] if result.assessments else None
        actual = finding.assessment if finding else "uncertain"
        expected = case["expected_assessment"]
        is_correct = actual == expected
        correct += int(is_correct)
        cited += int(bool(finding and finding.evidence_refs))
        results.append({"case_id": case["case_id"], "expected": expected, "actual": actual, "correct": is_correct})

    return {
        "cases": len(cases),
        "correct": correct,
        "accuracy": correct / len(cases),
        "evidence_coverage": cited / len(cases),
        "results": results,
    }
