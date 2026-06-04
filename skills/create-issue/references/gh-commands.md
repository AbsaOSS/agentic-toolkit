# `gh issue create` — Command Reference

How to create GitHub issues from the CLI within this skill.

## Basic usage

```bash
# Pipe body from stdin (preferred — handles long bodies, special characters safely)
printf '%s' "$BODY" | gh issue create \
  --title "Issue title" \
  --body-file - \
  [--label "bug"] \
  [--assignee "@me"] \
  [--milestone "v2.0"] \
  [--project "Board name"] \
  [-R owner/repo]
```

## Key flags

| Flag | Description |
|------|-------------|
| `--title` / `-t` | Issue title (required) |
| `--body` / `-b` | Body as string (use for short bodies) |
| `--body-file -` | Read body from stdin (use for long / multiline bodies) |
| `--label` / `-l` | Label name (repeatable: `-l bug -l urgent`) |
| `--assignee` / `-a` | GitHub username or `@me` (repeatable) |
| `--milestone` / `-m` | Milestone title |
| `--project` / `-p` | Project board name |
| `-R owner/repo` | Target a specific repository |
| `--web` / `-w` | Open the creation form in the browser instead |

## Stdin approach (preferred)

Use `--body-file -` to avoid quoting/escaping issues with long markdown bodies:

```bash
gh issue create \
  --title "Fix null pointer in AuthService" \
  --body-file - \
  --label "bug" \
  -R owner/repo <<'EOF'
### What happened?

`AuthService.login()` throws a NullPointerException when `user.email` is null.

### Steps to reproduce

1. Call `login()` with a user object that has no email field
2. Observe the stack trace

### Expected behaviour

A validation error is returned instead of an unhandled exception.

### Environment

- Version: 1.4.2
- Platform: Linux / JDK 17
EOF
```

## Graceful degradation

Try creation; if it fails due to missing metadata, retry without it:

```bash
# First attempt (full metadata)
gh issue create --title "$TITLE" --body-file - --label "$LABEL" -R "$REPO" < body.tmp

# On label-not-found error, retry without --label
gh issue create --title "$TITLE" --body-file - -R "$REPO" < body.tmp
```

Tell the user what was omitted and suggest adding it manually via the returned issue URL.

## Web fallback

When structured form submission is risky (required fields can't be inferred, blank issues disabled, or user prefers it):

```bash
gh issue create --web -R owner/repo
```

This opens the GitHub issue creation page in the browser with templates available.

## Checking repo context

```bash
# Get the owner/repo for the current directory
gh repo view --json nameWithOwner -q .nameWithOwner

# Check auth
gh auth status

# Verify issues are enabled
gh repo view --json hasIssuesEnabled -q .hasIssuesEnabled
```

## Listing available templates

```bash
# List template files in the target repo
gh api repos/OWNER/REPO/contents/.github/ISSUE_TEMPLATE \
  --jq '.[].name'

# Read a specific template
gh api repos/OWNER/REPO/contents/.github/ISSUE_TEMPLATE/bug_report.yml \
  --jq '.content' | base64 -d
```

> **Note:** When running in the cwd repo, prefer reading template files directly with `view` / `glob` rather than the API — it's faster and avoids rate limits.
