"""Create and refresh disposable local repository checkouts for analysis."""

import os
from pathlib import Path
import shutil
import stat
import subprocess
import tempfile
from typing import Optional, Union

from .github_api import GitHubAPIError, parse_repository


def ensure_repository_checkout(
    repository: str,
    cache_dir: Union[str, Path] = ".claimlens-repos",
    refresh: bool = False,
    token: Optional[str] = None,
) -> Path:
    repo = parse_repository(repository)
    target = Path(cache_dir) / f"{repo.owner}-{repo.name}"
    remote = f"https://github.com/{repo.owner}/{repo.name}.git"

    if target.exists() and not (target / ".git").exists():
        raise GitHubAPIError(f"cache path is not a Git repository: {target}")
    if not target.exists():
        target.parent.mkdir(parents=True, exist_ok=True)
        _run_git(["clone", remote, str(target)], token=token, timeout=180)
    elif refresh:
        _run_git(["-C", str(target), "fetch", "--prune", "origin"], token=token, timeout=180)
        _run_git(["-C", str(target), "reset", "--hard", "origin/HEAD"], token=token, timeout=60)
    return target


def _run_git(command, token: Optional[str], timeout: int) -> None:
    env = os.environ.copy()
    env["GIT_TERMINAL_PROMPT"] = "0"
    askpass_dir = None
    if token:
        askpass_dir = Path(tempfile.mkdtemp(prefix="claimlens-askpass-"))
        askpass = askpass_dir / "askpass.sh"
        askpass.write_text(
            "#!/bin/sh\ncase \"$1\" in\n"
            "  *Username*) printf '%s\\n' x-access-token ;;\n"
            "  *) printf '%s\\n' \"$CLAIMLENS_GIT_TOKEN\" ;;\n"
            "esac\n",
            encoding="utf-8",
        )
        askpass.chmod(stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
        env["GIT_ASKPASS"] = str(askpass)
        env["CLAIMLENS_GIT_TOKEN"] = token
        env["GIT_USERNAME"] = "x-access-token"
    try:
        completed = subprocess.run(
            ["git", *command], env=env, capture_output=True, text=True, timeout=timeout
        )
    except (OSError, subprocess.SubprocessError) as error:
        raise GitHubAPIError(f"could not prepare local repository: {error}") from error
    finally:
        if askpass_dir:
            shutil.rmtree(askpass_dir, ignore_errors=True)
    if completed.returncode != 0:
        details = (completed.stderr or completed.stdout or "git command failed").strip()
        raise GitHubAPIError(f"could not prepare local repository: {details[-1000:]}")
