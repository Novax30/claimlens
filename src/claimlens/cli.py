"""Command-line entry point for a local ClaimLens analysis."""

import argparse
from pathlib import Path
from typing import Optional, Sequence

from .input_reader import InputValidationError
from .ollama_client import OllamaError
from .service import ClaimLensService


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Analyze an issue or pull request locally.")
    parser.add_argument("request", help="Path to a ClaimLens request JSON file")
    parser.add_argument("--base-dir", default=".", help="Base directory for the repository path")
    parser.add_argument("--output", default="reports/latest.md", help="Markdown report output path")
    parser.add_argument("--claim-model", default="qwen2.5:7b")
    parser.add_argument("--evidence-model", default="deepseek-coder:6.7b")
    parser.add_argument("--offline", action="store_true", help="Run without Ollama or local AI models")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        service = ClaimLensService(args.claim_model, args.evidence_model, offline=args.offline)
        result = service.analyze_file(args.request, base_dir=args.base_dir)
    except (InputValidationError, OllamaError, OSError) as error:
        print(f"ClaimLens error: {error}")
        return 1

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        ClaimLensService.to_markdown(result),
        encoding="utf-8",
    )
    print(f"Report written to {output_path}")
    print(f"Claims: {len(result.claims)} | Evidence lines: {len(result.evidence)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
