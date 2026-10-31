"""Run ClaimLens on a saved GitHub issue or pull-request payload."""

import argparse
import json
from pathlib import Path
from typing import Any, Optional, Sequence

from .github_adapter import request_from_github_payload
from .ollama_client import OllamaError
from .service import ClaimLensService


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Analyze a saved GitHub event payload locally.")
    parser.add_argument("payload", help="Path to a saved GitHub issue or pull-request payload")
    parser.add_argument("repository_path", help="Local project folder to inspect")
    parser.add_argument("--offline", action="store_true")
    parser.add_argument("--output", default="reports/github_analysis.md")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        payload: Any = json.loads(Path(args.payload).read_text(encoding="utf-8"))
        request = request_from_github_payload(payload, args.repository_path)
        result = ClaimLensService(offline=args.offline).analyze_request(request)
    except (OSError, ValueError, json.JSONDecodeError, OllamaError) as error:
        print(f"ClaimLens error: {error}")
        return 1

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(ClaimLensService.to_markdown(result), encoding="utf-8")
    print(f"GitHub payload analyzed; report written to {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
