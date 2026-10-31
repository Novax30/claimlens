"""Read repository metadata needed to make evidence traceable."""

from pathlib import Path
import subprocess
from typing import Union


def get_commit_sha(repository_path: Path, base_dir: Union[str, Path] = ".") -> str:
    """Return the analyzed Git commit, or a clear value when unavailable."""
    project_path = (Path(base_dir).resolve() / repository_path).resolve()
    try:
        result = subprocess.run(
            ["git", "-C", str(project_path), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return "unavailable"
    sha = result.stdout.strip()
    return sha if sha else "unavailable"
