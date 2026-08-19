# PR Review Skill

The `pr-review` skill performs structured, risk-aware code review on pull requests and diffs. It activates automatically when you ask for PR feedback, share a diff, or ask for a sanity check on changes.

---

## What it does

The skill reads the list of files changed in a PR, selects the relevant review sections, and produces a concise review grouped by severity:

| Severity | Meaning |
|----------|---------|
| **Blocker** | Must be fixed before merge — correctness bug, security vulnerability, broken contract, credentials in code, data loss risk |
| **Important** | Should be fixed soon — increases risk, missing tests for changed logic, non-default that's hard to change later |
| **Nit** | Minor polish — style, naming, optional improvement, non-urgent edge case |

If a section has no findings, the skill writes `_None._` to show it was checked, not skipped.

---

## Sections

The skill always applies **Standard review** and selects additional sections based on the files the PR touches:

| Section | Triggers when PR touches |
|---|---|
| Standard | Always applied |
| API contracts | Endpoints, DTOs, config keys, env vars, exit codes, output strings |
| Dependency bumps | `pom.xml`, `requirements.txt`, `pyproject.toml`, `package.json`, `*.csproj`, `go.mod`, `build.sbt` |
| CI/CD | `.github/workflows/`, `Jenkinsfile`, `Justfile`, `Makefile` (pipeline), deployment jobs |
| Infrastructure | `*.tf`, `*.tfvars`, CloudFormation, Helm, Dockerfiles, `docker-compose.yml`, `iac/`, `infra/` |
| DB migrations | `alembic/`, `flyway/`, `liquibase/`, `migrations/`, `*.sql`, `db/` |
| Skill definitions | `skills/*/SKILL.md`, any `SKILL.md` |
| Elevated risk | Overlay — applied on top when PR touches auth/security controls, secrets management, or infrastructure/external integrations |

A file may match multiple sections — all matching sections are applied.

---

## How to trigger it

Ask for a review naturally — the skill fires on intent, not exact wording:

```
review my PR
any issues with these changes?
LGTM?
does this look right?
check this diff for risks
can you review this before I merge?
```

You can also share a GitHub PR link directly:

```
https://github.com/org/repo/pull/123 — does this look safe to merge?
```

> **Does NOT trigger** for generative tasks on a diff: "generate release notes from this diff", "summarise this diff". Those are documentation tasks.

---

## Helpers

The skill ships two scripts to speed up data gathering:

| Script | Purpose |
|--------|---------|
| `scripts/fetch_pr.sh <PR_NUMBER>` | Fetches the diff and file list via `gh` |
| `scripts/classify_sections.py /tmp/pr_files.txt` | Prints which sections to apply given a file list |

These require the [GitHub CLI](https://cli.github.com/) (`gh`) to be authenticated.

---

## Overriding or scoping the review

You can narrow or redirect the review with natural language:

```
focus only on security issues
skip the nits — just blockers and importants
review only the migration files
```

---

## Installation

The skill is installed along with the rest of the toolkit:

```bash
npx skills add https://github.com/AbsaOSS/agentic-toolkit -g
```

To install only this skill:

```bash
npx skills add https://github.com/AbsaOSS/agentic-toolkit -g --skill pr-review
```

See [Getting Started](../getting-started.md) for the full install guide.
