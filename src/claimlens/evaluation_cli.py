"""Evaluate ClaimLens on a small labeled local dataset."""

import argparse
import json
from typing import Optional, Sequence

from .evaluation_runner import evaluate_dataset
from .ollama_client import OllamaError
from .service import ClaimLensService


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Evaluate ClaimLens on labeled examples.")
    parser.add_argument("dataset")
    parser.add_argument("repository_path")
    parser.add_argument("--offline", action="store_true")
    args = parser.parse_args(argv)
    try:
        summary = evaluate_dataset(
            args.dataset,
            ClaimLensService(offline=args.offline),
            repository_path=args.repository_path,
        )
    except (OSError, ValueError, KeyError, OllamaError) as error:
        print(f"ClaimLens error: {error}")
        return 1
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
