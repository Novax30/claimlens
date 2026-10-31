"""Run repository tests in ClaimLens's disposable verification workspace."""

import argparse
from pathlib import Path
from typing import Optional, Sequence

from .verification_runner import run_repository_tests


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Run repository tests in a disposable workspace.")
    parser.add_argument("repository_path")
    parser.add_argument("--command", nargs="+", help="Override the detected language test command")
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--output", default="reports/verification.md")
    args = parser.parse_args(argv)

    result = run_repository_tests(args.repository_path, args.command, args.timeout)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        "# ClaimLens Verification\n\n"
        f"**Status:** `{result.status}`\n\n"
        f"**Language:** `{result.language}`\n\n"
        f"**Command:** `{result.command}`\n\n"
        f"**Exit code:** `{result.exit_code}`\n\n"
        f"**Duration:** `{result.duration_seconds}` seconds\n\n"
        "## Output\n\n"
        f"```text\n{result.output}\n```\n",
        encoding="utf-8",
    )
    print(f"Verification status: {result.status}")
    print(f"Report written to {output}")
    return 0 if result.status == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
