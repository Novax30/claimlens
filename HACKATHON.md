# ClaimLens

Hacktoberfest 2026 project

## Team

- Team name: ClaimLens
- Member: Bhavay

## Selected Problem

Problem 2: Evidence-Based Open Source Issue and Pull Request Triage

## AI Models Used

- Model: Qwen2.5 7B Instruct (`qwen2.5:7b`) running locally through Ollama
- How it is used: Identify and organize technical claims written in an issue or pull request. The output will be structured data that the rest of the tool can inspect.
- Why this model was selected: It is an open-weight model that can run locally through Ollama. Its instruction-following and structured-output capabilities fit the claim-extraction part of our tool, without sending issue or source-code data to a cloud AI service.

- Model: DeepSeek-Coder 6.7B (`deepseek-coder:6.7b`) running locally through Ollama
- How it is used: Review relevant Python code snippets selected by the evidence collector and help explain how those snippets relate to a claim.
- Why this model was selected: It is designed for source-code understanding, so it is a reasonable fit for the code-evidence part of the tool. It has a separate role from Qwen2.5, and it can also run locally through Ollama.

## Project Summary

ClaimLens is a local prototype for evaluating technical claims made in open-source issues and pull requests. It will inspect a project's source code, tests, and documentation, then produce a report containing the claim, relevant evidence, an assessment, and an uncertainty label. The tool will assist maintainers; it will not automatically close issues, reject contributors, or post comments on real projects.
