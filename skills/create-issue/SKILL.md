---
name: create-issue
description: Creates a GitHub issue based on a prompt. Analyzes the code related to the issue, selects the correct issue template type, and opens the issue via gh CLI. Triggers on requests like "create an issue for X", "open a bug report about Y", "file a feature request for Z", "add a ticket for W".
---

# Create Issue Skill

Creates a structured GitHub issue from a natural language description. Discovers the real issue templates in the target repo, analyzes relevant code context, fills the right template, confirms with the user, and posts via `gh issue create`.

## Step-by-Step Instructions

### 1. Resolve the target repository

- Determine which repo to open the issue in:
  - If the user specifies a repo (e.g. `org/repo` or `--repo`), use that.
  - Otherwise use the repo for the current working directory: `gh repo view --json nameWithOwner -q .nameWithOwner`
- Verify `gh auth status` succeeds and issues are enabled for the repo.
- Pass `-R owner/repo` to all subsequent `gh` calls when the target differs from cwd.

### 2. Parse the user's intent

Extract from the prompt:
- **Issue type hint** — bug, feature request, improvement, question, task, etc.
- **Subject** — the feature, component, file, or behaviour being reported.
- **Extra context** — error messages, steps to reproduce, desired behaviour, affected versions.

### 3. Discover templates

Read `.github/ISSUE_TEMPLATE/` in the target repo. See `references/templates.md` for how to parse YAML issue forms and Markdown templates.

- Also read `config.yml` / `config.yaml` if present (see `references/templates.md` → Config file).
- If blank issues are **disabled** and no template matches well, fall back to `--web`.
- If no templates exist at all, proceed with a plain title + body.

### 4. Analyze relevant code (conditional)

Only when the prompt names a specific component, file, or error:

- Use `glob` / `grep` / `view` to locate relevant files and identify key symbols, error strings, or call sites.
- Summarize findings in 2–5 bullet points — **do not paste raw code or internal paths** into the issue body.

### 5. Select the best template

Rank available templates using their `name`, `about`, default `labels`, and body prompt text against the parsed intent. See `references/templates.md` → Template selection.

- Auto-select only when confidence is high (single clear match).
- If ambiguous, list the top candidates and ask the user to choose.

### 6. Draft the issue

Fill every section of the chosen template using gathered context:

- **Title** — concise, factual, imperative or declarative. No issue numbers.
- **Body** — complete each template section. For required fields that cannot be inferred, insert a clear placeholder and flag it to the user.
- **Labels / assignees / milestone** — apply only when explicitly requested or when the template's `labels:` defaults them.

For YAML issue forms with required dropdowns or checkboxes that cannot be safely inferred, fall back to `--web` rather than submitting an invalid form.

### 7. Confirm with the user

Show the full draft (title + body + metadata). Ask:
> "Shall I create this issue? Reply **yes** to confirm, **edit** to adjust, or **web** to open the form in browser."

### 8. Create the issue

Use `gh issue create` with the rendered body piped on stdin (see `references/gh-commands.md`).

On error:
- If a label/assignee/milestone is not found, retry without it and report what was omitted.
- If creation fails entirely, offer `gh issue create --web` as a fallback.

### 9. Report

Output the created issue URL and a one-line summary.
