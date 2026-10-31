"""Fetch and test one GitHub pull request without writing to GitHub."""

import argparse
from pathlib import Path
from typing import Optional, Sequence

from .github_api import GitHubAPIError, GitHubClient
from .github_pr_verifier import verify_github_pull_request


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Fetch and test one GitHub PR read-only.")
    parser.add_argument("repository", help="GitHub repository in OWNER/REPOSITORY form")
    parser.add_argument("number", type=int, help="Pull-request number")
    parser.add_argument("--command", nargs="+", help="Override the detected language test command")
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--output", default="reports/github_pr_verification.md")
    args = parser.parse_args(argv)

    try:
        verification = verify_github_pull_request(
            args.repository,
            args.number,
            GitHubClient(),
            command=args.command,
            timeout_seconds=args.timeout,
        )
    except (GitHubAPIError, OSError, ValueError) as error:
        print(f"ClaimLens error: {error}")
        return 1

    result = verification.result
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        "# ClaimLens GitHub PR Verification\n\n"
        f"**PR:** `#{verification.number}`\n\n"
        f"**Commit:** `{verification.commit_sha}`\n\n"
        f"**Status:** `{result.status}`\n\n"
        f"**Language:** `{result.language}`\n\n"
        f"**Command:** `{result.command}`\n\n"
        f"**Exit code:** `{result.exit_code}`\n\n"
        f"**Duration:** `{result.duration_seconds}` seconds\n\n"
        "## Output\n\n"
        f"```text\n{result.output}\n```\n",
        encoding="utf-8",
    )
    print(f"PR #{verification.number} verification status: {result.status}")
    print(f"Report written to {output}")
    return 0 if result.status == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
