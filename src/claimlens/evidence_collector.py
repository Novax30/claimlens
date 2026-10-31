"""Collect simple, traceable evidence from a local project."""

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Iterable, List, Set, Union

from .input_reader import AnalysisRequest


class EvidenceCollectionError(ValueError):
    """Raised when the project cannot be inspected safely."""


@dataclass(frozen=True)
class Evidence:
    file: str
    line: int
    text: str
    category: str


_STOP_WORDS: Set[str] = {
    "about",
    "accepts",
    "application",
    "behaviour",
    "behavior",
    "claim",
    "continue",
    "does",
    "expected",
    "instead",
    "project",
    "should",
    "that",
    "the",
    "this",
    "value",
    "values",
    "with",
}

_TEXT_EXTENSIONS = {".md", ".py", ".txt", ".toml", ".yaml", ".yml", ".json"}


def _keywords(request: AnalysisRequest) -> Set[str]:
    return _keywords_from_text(f"{request.report.title} {request.report.body}")


def _keywords_from_text(text: str) -> Set[str]:
    text = text.lower()
    words = re.findall(r"[a-z_][a-z0-9_]{2,}", text)
    return {word for word in words if word not in _STOP_WORDS}


def _category(path: Path) -> str:
    if path.name.lower().startswith("test_") or "tests" in path.parts:
        return "test"
    if path.suffix.lower() in {".md", ".txt"}:
        return "documentation"
    return "source"


def _project_files(project_path: Path) -> Iterable[Path]:
    for path in project_path.rglob("*"):
        if not path.is_file():
            continue
        if ".git" in path.parts or "__pycache__" in path.parts:
            continue
        if path.suffix.lower() in _TEXT_EXTENSIONS:
            yield path


def collect_evidence(
    request: AnalysisRequest,
    base_dir: Union[str, Path] = ".",
    max_results: int = 50,
) -> List[Evidence]:
    """Find traceable text evidence related to a report's keywords."""
    project_path = _safe_project_path(base_dir, request.repository_path)
    if not project_path.is_dir():
        raise EvidenceCollectionError(f"project directory not found: {project_path}")

    keywords = _keywords(request)
    return _collect_from_project(project_path, keywords, max_results)


def collect_evidence_for_claim(
    request: AnalysisRequest,
    claim_text: str,
    base_dir: Union[str, Path] = ".",
    max_results: int = 20,
) -> List[Evidence]:
    """Find evidence for one claim instead of the whole report."""
    project_path = _safe_project_path(base_dir, request.repository_path)
    if not project_path.is_dir():
        raise EvidenceCollectionError(f"project directory not found: {project_path}")
    return _collect_from_project(project_path, _keywords_from_text(claim_text), max_results)


def _collect_from_project(
    project_path: Path,
    keywords: Set[str],
    max_results: int,
) -> List[Evidence]:
    if not keywords:
        return []

    results: List[Evidence] = []
    for path in _project_files(project_path):
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except (UnicodeDecodeError, OSError):
            continue

        for line_number, line in enumerate(lines, start=1):
            lower_line = line.lower()
            if any(keyword in lower_line for keyword in keywords):
                results.append(
                    Evidence(
                        file=path.relative_to(project_path).as_posix(),
                        line=line_number,
                        text=line.strip(),
                        category=_category(path),
                    )
                )
    category_priority = {"source": 0, "test": 1, "documentation": 2}
    results.sort(
        key=lambda item: (
            category_priority.get(item.category, 3),
            -sum(keyword in item.text.lower() for keyword in keywords),
            item.file,
            item.line,
        )
    )
    return results[:max_results]


def _safe_project_path(base_dir: Union[str, Path], repository_path: Path) -> Path:
    """Resolve a project path without allowing traversal outside the workspace."""
    base_path = Path(base_dir).resolve()
    project_path = (base_path / repository_path).resolve()
    if project_path != base_path and base_path not in project_path.parents:
        raise EvidenceCollectionError("repository_path must stay inside base_dir")
    return project_path
