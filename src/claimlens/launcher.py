"""Small beginner-friendly menu for the ClaimLens command-line tool."""

from getpass import getpass
from pathlib import Path

from .github_api import GitHubClient
from .github_pr_verifier import verify_github_pull_request
from .github_queue import analyze_github_prs
from .pr_queue import render_queue_markdown
from .service import ClaimLensService


def _token_client() -> GitHubClient:
    token = getpass("GitHub token (hidden, press Enter for public access): ").strip()
    return GitHubClient(token=token or None)


def _github_queue() -> None:
    repository = input("GitHub repository (OWNER/REPOSITORY): ").strip()
    local_path = input("Local repository folder [.] : ").strip() or "."
    client = _token_client()
    items = analyze_github_prs(
        repository,
        local_path,
        ClaimLensService(offline=True),
        client,
    )
    output = Path("reports/my_github_queue.md")
    output.parent.mkdir(exist_ok=True)
    output.write_text(render_queue_markdown(items), encoding="utf-8")
    print(f"\nProcessed {len(items)} pull requests.")
    print(f"Report: {output}")


def _verify_pr() -> None:
    repository = input("GitHub repository (OWNER/REPOSITORY): ").strip()
    number = int(input("Pull-request number: ").strip())
    result = verify_github_pull_request(repository, number, _token_client())
    output = Path("reports/github_pr_verification.md")
    output.parent.mkdir(exist_ok=True)
    output.write_text(
        "# ClaimLens GitHub PR Verification\n\n"
        f"**PR:** `#{result.number}`\n\n"
        f"**Commit:** `{result.commit_sha}`\n\n"
        f"**Status:** `{result.result.status}`\n\n"
        f"**Language:** `{result.result.language}`\n\n"
        f"**Output:**\n\n```text\n{result.result.output}\n```\n",
        encoding="utf-8",
    )
    print(f"\nPR verification status: {result.result.status}")
    print(f"Report: {output}")


def main() -> int:
    while True:
        print("\nClaimLens")
        print("1. Run the offline demo")
        print("2. Review a GitHub PR queue")
        print("3. Test one GitHub PR")
        print("4. Exit")
        choice = input("Choose an option: ").strip()
        try:
            if choice == "1":
                result = ClaimLensService(offline=True).analyze_file("input/example_request.json")
                output = Path("reports/launcher_demo.md")
                output.parent.mkdir(exist_ok=True)
                output.write_text(ClaimLensService.to_markdown(result), encoding="utf-8")
                print(f"\nDemo report: {output}")
            elif choice == "2":
                _github_queue()
            elif choice == "3":
                _verify_pr()
            elif choice == "4":
                return 0
            else:
                print("Please choose 1, 2, 3, or 4.")
        except (OSError, ValueError, RuntimeError) as error:
            print(f"ClaimLens could not complete that action: {error}")


if __name__ == "__main__":
    raise SystemExit(main())
