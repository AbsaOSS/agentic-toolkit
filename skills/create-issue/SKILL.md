---
name: create-issue
description: Creates a GitHub issue from a natural language prompt. Discovers repo templates, fills the best match, posts via gh CLI. Use this skill whenever the user wants to create an issue, open a bug report, file a feature request, submit a ticket, log a bug, report a problem, track something as an issue, or add a ticket — even if they don't say "issue" explicitly.
---

# Create Issue

Two-phase: **discover** (cheap model) → **draft + post** (you).

Flags: `--confirm` (review before posting), `--web` (open in browser), `-R owner/repo` (target repo).

## Phase 1 — Discover (delegate to Haiku)

Spawn a subagent with `model: "haiku"` to handle all mechanical work. Give it this prompt, filling in the repo if the user specified one:

> Discover issue templates for a GitHub repo and return structured JSON.
>
> 1. Resolve repo: use `-R {owner/repo}` if provided, else run `gh repo view --json nameWithOwner -q .nameWithOwner`.
> 2. List `.github/ISSUE_TEMPLATE/` — locally if the repo is the cwd, else via `gh api repos/OWNER/REPO/contents/.github/ISSUE_TEMPLATE --jq '.[].name'`.
> 3. If `config.yml` or `config.yaml` exists, read it and extract `blank_issues_enabled`.
> 4. For each template file (not config), extract `name`, `about`/`description`, and `labels` from the front-matter or YAML top-level fields.
> 5. Read the full content of the template that best matches the issue type hint: `{type_hint}`.
> 6. Return ONLY a single JSON block — no commentary:
> ```json
> {
>   "repo": "owner/repo",
>   "blank_issues_enabled": true,
>   "templates": [{"file": "bug_report.yml", "name": "Bug Report", "about": "File a bug", "labels": "bug"}],
>   "selected": {"file": "bug_report.yml", "content": "<full template content>"},
>   "default_labels": "bug"
> }
> ```
> If no templates exist, return: `{"repo": "owner/repo", "blank_issues_enabled": true, "templates": [], "selected": null, "default_labels": ""}`

Replace `{type_hint}` with the issue type you parsed from the user's prompt (bug/feature/task/question).

## Phase 2 — Draft and post (you)

Using the JSON from Phase 1:

1. **Draft** title + body from user prompt and conversation context:
   - If `selected` has content, fill its template sections. See `references/templates.md` for YAML form → markdown rendering rules.
   - If `selected` is null, use plain title + body.
   - If `blank_issues_enabled` is false and no template matched, fall back to `--web`.
   - Use `<!-- TODO: fill in -->` for required fields that can't be inferred.
   - Include fix suggestions only when root cause is clear from context.
   - Match template structure — don't add extra sections.

2. **Post** (skip confirmation unless `--confirm`):
   ```
   gh issue create --title "TITLE" --body-file - [--label x] [-R repo] <<'EOF'
   BODY
   EOF
   ```
   On metadata error → retry without it, report what was dropped. On total failure → offer `--web`.

3. **Output**: issue URL + one-line summary. Nothing else.
