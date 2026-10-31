"""Command-line batch runner for ClaimLens test cases."""

import argparse
from pathlib import Path
from typing import Optional, Sequence

from .batch_runner import run_batch
from .ollama_client import OllamaError
from .service import ClaimLensService


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run ClaimLens over a directory of cases.")
    parser.add_argument("cases_dir")
    parser.add_argument("repository_path")
    parser.add_argument("--offline", action="store_true")
    parser.add_argument("--output", default="reports/batch_summary.md")
    return parser


def render_summary(results) -> str:
    lines = [
        "# ClaimLens Batch Summary",
        "",
        "| Case | Expected | Result | Status |",
        "| --- | --- | --- | --- |",
    ]
    for result in results:
        assessments = result.analysis.assessments
        actual = assessments[0].assessment if assessments else "no claim"
        status = "match" if actual == result.expected_assessment else "review"
        lines.append(f"| `{result.case_id}` | `{result.expected_assessment}` | `{actual}` | `{status}` |")
    lines.extend(
        [
            "",
            "`review` means the case needs human inspection; it is not an automatic judgment about a contributor.",
            "",
        ]
    )
    return "\n".join(lines)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        results = run_batch(
            args.cases_dir,
            ClaimLensService(offline=args.offline),
            repository_path=args.repository_path,
        )
    except (OllamaError, OSError, ValueError) as error:
        print(f"ClaimLens error: {error}")
        return 1

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_summary(results), encoding="utf-8")
    print(f"Batch summary written to {output}")
    print(f"Cases processed: {len(results)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
