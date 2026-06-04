---
name: --help
description: Creates a GitHub issue from a natural language prompt using the repo's issue templates.
---

# create-issue — Help

Creates a GitHub issue from a natural language description, using the real issue templates in the target repository.

## When to use

- "Create an issue for X"
- "Open a bug report about Y"
- "File a feature request for Z"
- "Add a ticket for W"

## What it does

1. Discovers issue templates from `.github/ISSUE_TEMPLATE/` in the target repo
2. Analyzes relevant code when a component or error is mentioned
3. Selects and fills the best matching template
4. Confirms the draft with you before posting
5. Runs `gh issue create` and returns the issue URL

## Options

- Specify a different repo: "create an issue in **owner/repo** for …"
- Specify a type: "open a **bug report** / **feature request** / **task**"
- Open in browser instead: reply **web** at the confirmation prompt
