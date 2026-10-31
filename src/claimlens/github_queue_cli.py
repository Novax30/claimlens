"""Analyze open GitHub pull requests without posting anything back."""

import argparse
from pathlib import Path
from typing import Optional, Sequence

from .github_api import GitHubAPIError, GitHubClient
from .github_queue import analyze_github_prs
from .repository_checkout import ensure_repository_checkout
from .ollama_client import OllamaError
from .pr_queue import render_queue_markdown
from .service import ClaimLensService


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Analyze live GitHub pull requests read-only.")
    parser.add_argument("repository", help="GitHub repository in OWNER/REPOSITORY form")
    parser.add_argument("repository_path", nargs="?", help="Optional local checkout to inspect")
    parser.add_argument("--refresh", action="store_true", help="Refresh the automatic local checkout")
    parser.add_argument("--cache-dir", default=".claimlens-repos")
    parser.add_argument("--state", choices=("open", "closed", "all"), default="open")
    parser.add_argument("--workers", type=int, default=4, help="Parallel PR workers (default: 4)")
    parser.add_argument("--no-llm", "--offline", dest="no_llm", action="store_true", help="Use deterministic rules instead of Ollama")
    parser.add_argument("--output", default="reports/github_pr_queue.md")
    args = parser.parse_args(argv)

    try:
        client = GitHubClient()
        repository_path = args.repository_path or ensure_repository_checkout(
            args.repository, cache_dir=args.cache_dir, refresh=args.refresh, token=client.token
        )
        items = analyze_github_prs(
            args.repository,
            str(repository_path),
            ClaimLensService(offline=args.no_llm),
            client,
            state=args.state,
            max_workers=args.workers,
        )
    except (GitHubAPIError, OSError, ValueError, OllamaError) as error:
        print(f"ClaimLens error: {error}")
        return 1

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_queue_markdown(items, repository=args.repository), encoding="utf-8")
    print(f"GitHub PR queue written to {output}")
    print(f"Pull requests processed: {len(items)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
