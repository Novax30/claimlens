"""Interactive command-line chat interface for ClaimLens."""

import argparse
from pathlib import Path
from typing import Optional, Sequence

from .input_reader import AnalysisRequest, ReportInput
from .ollama_client import OllamaError
from .service import ClaimLensService


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Use ClaimLens interactively from the terminal.")
    parser.add_argument("repository_path", help="Local project folder to inspect")
    parser.add_argument("--offline", action="store_true", help="Use Python rules without Ollama")
    parser.add_argument("--output", help="Optional Markdown report path")
    return parser


def run_chat(
    repository_path: str,
    offline: bool = False,
    output: Optional[str] = None,
) -> int:
    print("ClaimLens local review")
    print("Type the issue or pull-request details. Empty title/body is not accepted.\n")
    kind = input("Type (issue/pull_request) [issue]: ").strip() or "issue"
    title = input("Title: ").strip()
    body = input("Body: ").strip()
    if kind not in {"issue", "pull_request"} or not title or not body:
        print("Please provide a valid type, title, and body.")
        return 1

    request = AnalysisRequest(
        repository_path=Path(repository_path),
        report=ReportInput(title=title, body=body, kind=kind),
    )
    try:
        result = ClaimLensService(offline=offline).analyze_request(request)
    except (OllamaError, OSError) as error:
        print(f"ClaimLens error: {error}")
        return 1

    report = ClaimLensService.to_markdown(result)
    if output:
        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(report, encoding="utf-8")
        print(f"\nReport written to {output_path}")
    else:
        print("\n" + report)
    return 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    return run_chat(args.repository_path, offline=args.offline, output=args.output)


if __name__ == "__main__":
    raise SystemExit(main())
