"""Analyze open GitHub pull requests without posting anything back."""

import argparse
from pathlib import Path
from typing import Optional, Sequence

from .github_api import GitHubAPIError, GitHubClient
from .github_queue import analyze_github_prs
from .ollama_client import OllamaError
from .pr_queue import render_queue_markdown
from .service import ClaimLensService


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Analyze live GitHub pull requests read-only.")
    parser.add_argument("repository", help="GitHub repository in OWNER/REPOSITORY form")
    parser.add_argument("repository_path", help="Local checkout to inspect")
    parser.add_argument("--state", choices=("open", "closed", "all"), default="open")
    parser.add_argument("--workers", type=int, default=4, help="Parallel PR workers (default: 4)")
    parser.add_argument("--offline", action="store_true")
    parser.add_argument("--output", default="reports/github_pr_queue.md")
    args = parser.parse_args(argv)

    try:
        items = analyze_github_prs(
            args.repository,
            args.repository_path,
            ClaimLensService(offline=args.offline),
            GitHubClient(),
            state=args.state,
            max_workers=args.workers,
        )
    except (GitHubAPIError, OSError, ValueError, OllamaError) as error:
        print(f"ClaimLens error: {error}")
        return 1

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_queue_markdown(items), encoding="utf-8")
    print(f"GitHub PR queue written to {output}")
    print(f"Pull requests processed: {len(items)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
