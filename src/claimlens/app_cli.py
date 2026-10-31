"""Unified installed CLI entry point."""

import argparse
from typing import Optional, Sequence


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(prog="claimlens", description="Evidence-based open-source triage")
    subcommands = parser.add_subparsers(dest="command", required=True)
    for name, help_text in (
        ("analyze", "Analyze one local request"),
        ("queue", "Analyze a GitHub PR queue"),
        ("verify", "Fetch and verify one GitHub PR"),
        ("evaluate", "Evaluate the labeled dataset"),
    ):
        subparser = subcommands.add_parser(name, help=help_text)
        subparser.add_argument("args", nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)

    if args.command == "analyze":
        from .cli import main as command_main
    elif args.command == "queue":
        from .github_queue_cli import main as command_main
    elif args.command == "verify":
        from .github_pr_verify_cli import main as command_main
    else:
        from .evaluation_cli import main as command_main
    return command_main(args.args)


if __name__ == "__main__":
    raise SystemExit(main())
