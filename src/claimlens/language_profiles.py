"""Language detection and safe default verification commands."""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Sequence, Union


@dataclass(frozen=True)
class LanguageProfile:
    name: str
    command: Sequence[str]
    executable: str
    image: str


PROFILES = {
    "python": LanguageProfile("Python", ("python", "-m", "pytest", "-q"), "python", "python:3.11-slim"),
    "rust": LanguageProfile("Rust", ("cargo", "test", "--locked"), "cargo", "rust:1-slim"),
    "cpp": LanguageProfile("C/C++", ("sh", "-c", "cmake -S . -B build && cmake --build build && ctest --test-dir build --output-on-failure"), "cmake", "debian:bookworm-slim"),
    "javascript": LanguageProfile("JavaScript/TypeScript", ("npm", "test", "--", "--runInBand"), "npm", "node:22-bookworm-slim"),
    "go": LanguageProfile("Go", ("go", "test", "./..."), "go", "golang:1.23-bookworm"),
}


def detect_language(repository_path: Union[str, Path]) -> Optional[LanguageProfile]:
    root = Path(repository_path)
    if (root / "Cargo.toml").exists():
        return PROFILES["rust"]
    if (root / "CMakeLists.txt").exists() or any(root.glob("*.cpp")) or any(root.glob("*.c")):
        return PROFILES["cpp"]
    if (root / "package.json").exists():
        return PROFILES["javascript"]
    if (root / "go.mod").exists():
        return PROFILES["go"]
    if ((root / "pyproject.toml").exists() or (root / "requirements.txt").exists()
            or (root / "setup.py").exists() or any(root.rglob("*.py"))):
        return PROFILES["python"]
    return None
