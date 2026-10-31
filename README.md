# ClaimLens

ClaimLens is a local prototype for evaluating technical claims made in open-source issues and pull requests.

It reads an issue or pull request description, finds relevant lines in a local project, and produces an evidence-based Markdown report. Qwen2.5 extracts claims, DeepSeek-Coder helps explain code evidence, and Python keeps the evidence traceable.

## Local requirements

- Python 3.9 or newer
- Ollama running locally
- `qwen2.5:7b`
- `deepseek-coder:6.7b`

The project does not use cloud AI services.

## Simplest way to start

After cloning the repository, run one command:

```bash
./claimlens
```

The first run prepares the Python environment. Then choose from a small menu
to run the offline demo, review a GitHub PR queue, or test one GitHub PR. A
GitHub token is requested only when needed, hidden while typing, and is not
saved by ClaimLens.

## Run the tests

```bash
python3 -m pip install -r requirements-dev.txt
python3 -m pip install --no-deps .
python3 -m pytest
```

For an editable local installation:

```bash
python3 -m pip install -e .
```

## Run a local analysis

```bash
PYTHONPATH=src python3 -m claimlens input/example_request.json \
  --output reports/first_analysis.md
```

The report includes the claim, assessment, confidence, explanation, and exact evidence references.

Each finding also shows execution status. The current analyzer reports
`not_attempted` because it does not run contributor code yet. This is kept
separate from the claim result: a claim can be inconclusive without being false.

## Use interactive chat mode

```bash
PYTHONPATH=src python3 -m claimlens.chat_cli examples/sample_project --offline
```

The interactive mode asks for the issue or pull-request type, title, and body, then prints the report.

## Run the prepared case batch

```bash
PYTHONPATH=src python3 -m claimlens.batch_cli \
  examples/cases examples/sample_project --offline
```

This writes a summary to `reports/batch_summary.md`.

## Analyze a saved GitHub payload

```bash
PYTHONPATH=src python3 -m claimlens.github_cli \
  examples/github_issue_payload.json examples/sample_project --offline
```

This is a local adapter for future GitHub integration. It does not call GitHub or post comments.

## Triage a PR queue locally

```bash
PYTHONPATH=src python3 -m claimlens.pr_queue_cli \
  examples/pr_payloads examples/sample_project --offline
```

This processes saved pull-request payloads and ranks them for human review. It does not approve, reject, close, or comment on PRs.

## Evaluate the system on labeled examples

```bash
PYTHONPATH=src python3 -m claimlens.evaluation_cli \
  examples/evaluation_dataset.json examples/sample_project --offline
```

This reports simple accuracy and evidence coverage. It is a small demonstration
dataset, not a claim of production performance.

## Run repository tests safely

```bash
PYTHONPATH=src python3 -m claimlens.verify_cli examples/sample_project
```

ClaimLens copies the repository to a temporary workspace, creates a disposable
Python virtual environment when its test dependencies are available, removes
credentials and proxy settings, disables network-dependent package
installation, applies a timeout, and records the test result. This is a
defensive local runner, not a complete VM security boundary; high-risk code
should run in a separate disposable container or VM.

## Fetch and test one GitHub PR

With a read-only `GITHUB_TOKEN` set, ClaimLens can fetch a PR branch into a
temporary checkout and run its tests:

```bash
PYTHONPATH=src python3 -m claimlens.github_pr_verify_cli \
  OWNER/REPOSITORY 123 \
  --output reports/pr_123_verification.md
```

This performs a temporary `git clone`, `git fetch`, and detached checkout. It
never pushes, merges, comments, or changes the remote repository.

## Triage live GitHub pull requests (read-only)

Set a GitHub token in your terminal. A fine-grained token should have only
`Pull requests: Read-only` access for the target repository.

```bash
export GITHUB_TOKEN="your-token"
PYTHONPATH=src python3 -m claimlens.github_queue_cli \
  OWNER/REPOSITORY examples/sample_project --offline
```

The command reads pull-request metadata from GitHub and inspects the local
checkout. It writes a Markdown queue and never posts comments, changes labels,
approves, closes, merges, or pushes anything.

PRs are analyzed in parallel with four bounded workers by default. Change this
carefully on a smaller computer:

```bash
PYTHONPATH=src python3 -m claimlens.github_queue_cli \
  OWNER/REPOSITORY /path/to/local/repository --offline --workers 2
```

If one PR fails, ClaimLens keeps processing the other PRs and marks the failed
one for manual review.

Responses are cached locally for five minutes in `.claimlens-cache/` to reduce
repeat requests. The cache is ignored by Git and the client stops requesting
when GitHub reports that the rate limit has been reached.

## Run without local models

ClaimLens also has a conservative offline mode. It uses Python rules instead of Ollama:

```bash
PYTHONPATH=src python3 -m claimlens input/example_request.json \
  --offline --output reports/offline_analysis.md
```

Offline mode is useful when Ollama is unavailable. Model mode provides richer claim extraction and code explanations and is the mode intended for the hackathon's open-model requirement.

## Current limitations

- The live GitHub mode reads PR metadata and changed-file patches. It compares
  those patches with the local checkout; it does not modify the checkout or
  create temporary branches.
- Evidence collection is currently text-based.
- Reports assist maintainers; they do not automatically close issues, reject contributors, or post comments.
