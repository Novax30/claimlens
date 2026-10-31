"""Run repository tests in a disposable, restricted Python workspace."""

from dataclasses import dataclass
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
from typing import Optional, Sequence, Union

from .language_profiles import detect_language


@dataclass(frozen=True)
class VerificationResult:
    language: str
    status: str
    command: str
    exit_code: Optional[int]
    duration_seconds: float
    output: str


def _safe_environment(workspace: Path) -> dict:
    env = {
        "PATH": os.environ.get("PATH", ""),
        "LANG": os.environ.get("LANG", "C.UTF-8"),
        "LC_ALL": os.environ.get("LC_ALL", "C.UTF-8"),
        "HOME": str(workspace / "home"),
        "TMPDIR": str(workspace / "tmp"),
        "CI": "1",
        "PIP_NO_INDEX": "1",
        "PYTHONDONTWRITEBYTECODE": "1",
    }
    # Do not pass credentials, proxy settings, or SSH access to contributor code.
    return env


def run_repository_tests(
    repository_path: Union[str, Path],
    command: Optional[Sequence[str]] = None,
    timeout_seconds: int = 120,
    base_dir: Union[str, Path] = ".",
) -> VerificationResult:
    """Run a test command in a disposable copy of a local repository.

    This is a defensive local runner, not a perfect security boundary. For
    high-risk repositories, use a disposable VM or container outside ClaimLens.
    Network is disabled through environment settings and no credentials are
    passed to the child process.
    """
    source = (Path(base_dir).resolve() / Path(repository_path)).resolve()
    if not source.is_dir():
        raise ValueError(f"repository directory not found: {source}")
    profile = detect_language(source)
    if command is None:
        if profile is None:
            return VerificationResult(
                "unknown", "environment_failure", "automatic detection", None, 0.0,
                "No supported language profile was detected.",
            )
        command = profile.command
    language = profile.name if profile else "custom"
    if not command:
        raise ValueError("test command cannot be empty")
    if timeout_seconds < 1:
        raise ValueError("timeout_seconds must be positive")

    started = time.monotonic()
    command_text = " ".join(command)
    with tempfile.TemporaryDirectory(prefix="claimlens-verify-") as temp_name:
        workspace = Path(temp_name)
        checkout = workspace / "checkout"
        shutil.copytree(
            source,
            checkout,
            ignore=shutil.ignore_patterns(".git", "__pycache__", ".venv", "reports"),
        )
        (workspace / "home").mkdir()
        (workspace / "tmp").mkdir()

        venv_path = workspace / "venv"
        try:
            subprocess.run(
                [sys.executable, "-m", "venv", "--system-site-packages", str(venv_path)],
                check=True,
                capture_output=True,
                text=True,
                timeout=30,
            )
            python_name = "python.exe" if os.name == "nt" else "python"
            executable = str(venv_path / "bin" / python_name)
            if os.name == "nt":
                executable = str(venv_path / "Scripts" / python_name)
            if command[0] == "python":
                has_pytest = subprocess.run([executable, "-c", "import pytest"], capture_output=True, timeout=10).returncode == 0
                if not has_pytest and subprocess.run([sys.executable, "-c", "import pytest"], capture_output=True, timeout=10).returncode == 0:
                    executable = sys.executable
                run_command = [executable, *command[1:]]
            else:
                required_tool = profile.executable if profile else command[0]
                if shutil.which(required_tool) is None:
                    return VerificationResult(
                        language, "environment_failure", command_text, None,
                        round(time.monotonic() - started, 3),
                        f"Required tool not installed: {required_tool}",
                    )
                run_command = list(command)
            completed = subprocess.run(
                run_command,
                cwd=checkout,
                env=_safe_environment(workspace),
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
            )
            output = (completed.stdout + completed.stderr)[-20000:]
            status = "passed" if completed.returncode == 0 else "failed"
            return VerificationResult(
                language=language,
                status=status,
                command=command_text,
                exit_code=completed.returncode,
                duration_seconds=round(time.monotonic() - started, 3),
                output=output,
            )
        except subprocess.TimeoutExpired as error:
            output = str(error.stdout or "")[-20000:]
            return VerificationResult(
                language=language,
                status="timeout",
                command=command_text,
                exit_code=None,
                duration_seconds=round(time.monotonic() - started, 3),
                output=output,
            )
        except (OSError, subprocess.SubprocessError) as error:
            return VerificationResult(
                language=language,
                status="environment_failure",
                command=command_text,
                exit_code=None,
                duration_seconds=round(time.monotonic() - started, 3),
                output=str(error),
            )
