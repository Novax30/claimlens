"""Small beginner-friendly menu for the ClaimLens command-line tool."""

from getpass import getpass
from pathlib import Path

from .github_api import GitHubClient
from .github_pr_verifier import verify_github_pull_request
from .github_queue import analyze_github_prs
from .pr_queue import render_queue_markdown
from .repository_checkout import ensure_repository_checkout
from .service import ClaimLensService


def _token_client() -> GitHubClient:
    token = getpass("GitHub token (hidden, press Enter for public access): ").strip()
    return GitHubClient(token=token or None)


def _github_queue() -> None:
    repository = input("GitHub repository (OWNER/REPOSITORY): ").strip()
    client = _token_client()
    local_path = input("Local repository folder [download automatically]: ").strip()
    if not local_path:
        local_path = str(ensure_repository_checkout(repository, token=client.token))
    use_models = input("Use local Ollama models? [y/N]: ").strip().lower() == "y"
    items = analyze_github_prs(
        repository,
        local_path,
        ClaimLensService(offline=not use_models),
        client,
    )
    output = Path("reports/my_github_queue.md")
    output.parent.mkdir(exist_ok=True)
    output.write_text(render_queue_markdown(items, repository=repository), encoding="utf-8")
    print(f"\nProcessed {len(items)} pull requests.")
    print(f"Report: {output}")


def _verify_pr() -> None:
    print("\nTest one PR — deeper checking")
    print("1. Fetch the PR")
    print("2. Record its commit")
    print("3. Create a temporary checkout")
    print("4. Detect the programming language")
    print("5. Run the appropriate test command")
    print("6. Create a pass, fail, timeout, or environment-failure report")
    print("Docker is required for this safe execution mode.\n")
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
        print("3. Test one GitHub PR (deeper checking)")
        print("4. Exit")
        try:
            choice = input("Choose an option: ").strip()
        except EOFError:
            print("\nClaimLens closed.")
            return 0
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
