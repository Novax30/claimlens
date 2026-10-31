"""Run a directory of prepared cases through the ClaimLens service."""

from dataclasses import dataclass
import json
from pathlib import Path
from typing import List, Union

from .input_reader import AnalysisRequest, ReportInput
from .pipeline import AnalysisResult
from .service import ClaimLensService


@dataclass(frozen=True)
class BatchResult:
    case_id: str
    expected_assessment: str
    analysis: AnalysisResult


def _load_case(path: Path, repository_path: str) -> AnalysisRequest:
    data = json.loads(path.read_text(encoding="utf-8"))
    return AnalysisRequest(
        repository_path=Path(repository_path),
        report=ReportInput(
            title=data.get("title", ""),
            body=data.get("body", ""),
            kind=data.get("kind", "issue"),
        ),
    )


def run_batch(
    cases_dir: Union[str, Path],
    service: ClaimLensService,
    repository_path: str = "examples/sample_project",
    base_dir: Union[str, Path] = ".",
) -> List[BatchResult]:
    results: List[BatchResult] = []
    for path in sorted(Path(cases_dir).glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        request = _load_case(path, repository_path)
        results.append(
            BatchResult(
                case_id=str(data.get("case_id", path.stem)),
                expected_assessment=str(data.get("expected_assessment", "uncertain")),
                analysis=service.analyze_request(request, base_dir=base_dir),
            )
        )
    return results
