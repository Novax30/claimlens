"""Command-line PR queue analyzer for saved GitHub payloads."""

import argparse
from pathlib import Path
from typing import Optional, Sequence

from .ollama_client import OllamaError
from .pr_queue import analyze_pr_queue, render_queue_markdown
from .service import ClaimLensService


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Rank saved pull requests for review.")
    parser.add_argument("payload_dir")
    parser.add_argument("repository_path")
    parser.add_argument("--offline", action="store_true")
    parser.add_argument("--output", default="reports/pr_queue.md")
    args = parser.parse_args(argv)

    try:
        items = analyze_pr_queue(
            args.payload_dir,
            args.repository_path,
            ClaimLensService(offline=args.offline),
        )
    except (OSError, ValueError, OllamaError) as error:
        print(f"ClaimLens error: {error}")
        return 1

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_queue_markdown(items), encoding="utf-8")
    print(f"PR queue written to {output}")
    print(f"Pull requests processed: {len(items)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
