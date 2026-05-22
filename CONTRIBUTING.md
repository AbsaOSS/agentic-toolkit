# Contributing to Agentic Toolkit

This guide covers everything you need to author a high-quality skill for this repository — from file layout and
frontmatter rules through description writing, body guidelines, and testing.

> New here? Read **[docs/getting-started.md](./docs/getting-started.md)** first to understand what skills are and how
> to install them before authoring your own.

## Table of Contents

1. [Skill structure](#1-skill-structure)
2. [Frontmatter schema](#2-frontmatter-schema)
3. [Writing the description](#3-writing-the-description)
4. [Writing the skill body](#4-writing-the-skill-body)
5. [Testing your skill](#5-testing-your-skill)
6. [Proposing a skill via a pull request](#6-proposing-a-skill-via-a-pull-request)

## 1. Skill structure

Each skill lives in its own folder under `skills/`:

```
skills/
└── skill-name/
    ├── SKILL.md          # Required — frontmatter + instructions
    ├── scripts/          # Optional — executable scripts the agent can run
    ├── references/       # Optional — supporting docs loaded on demand
    ├── assets/           # Optional — templates, icons, example files
    └── evals/            # Optional — test prompts and assertions
```

> **Rule:** the folder name must exactly match the `name` field in the `SKILL.md` frontmatter.

### When to add each optional directory

| Directory     | Use for                                                                                                                                  |
|---------------|------------------------------------------------------------------------------------------------------------------------------------------|
| `scripts/`    | Deterministic or repetitive logic better run as code than described in prose (e.g. a validation script, a formatter, a data transformer) |
| `references/` | Domain docs, API specs, decision tables, or anything too large to keep in `SKILL.md` without exceeding 500 lines                         |
| `assets/`     | Template files, example inputs/outputs, icons — anything the skill produces or consumes                                                  |
| `evals/`      | Test prompts and assertions to verify skill behavior and trigger accuracy. See [skill-testing.md](./docs/testing/skill-testing.md)               |

---

## 2. Frontmatter schema

Every `SKILL.md` must open with a YAML frontmatter block:

```yaml
---
name: skill-name
description: >
  What this skill does and the specific situations in which it should be
  activated. Include trigger phrases, domains, and keywords.
license: Proprietary             # optional
compatibility: GitHub Copilot    # optional — only when env requirements exist
---
```

### Field reference

| Field | Required | Constraints |
|---|---|---|
| `name` | ✅ | Lowercase letters, numbers, and hyphens only. Max 64 chars. Must not start or end with a hyphen. No consecutive hyphens (`--`). Must match the parent directory name. |
| `description`   | ✅        | Max 1024 chars. Non-empty. Must describe both **what** the skill does and **when** to activate it. See [Writing the description](#3-writing-the-description).         |
| `license` | ➖ | Short SPDX name or reference to a bundled `LICENSE.txt`. |
| `compatibility` | ➖ | Max 500 chars. Only include if the skill has specific environment requirements (tools, Python version, network access, etc.). Most skills do not need this field. |

#### Valid `name` examples

```yaml
name: pr-review          # ✅
name: create-issue       # ✅
name: data-pipeline      # ✅
```

#### Invalid `name` examples

```yaml
name: PR-Review          # ❌ uppercase
name: -pr-review         # ❌ starts with hyphen
name: pr--review         # ❌ consecutive hyphens
name: pr_review          # ❌ underscores not allowed
```

---

## 3. Writing the description

The `description` field is the **primary triggering mechanism**. The agent never reads your skill body until it decides the description matches the current task. A weak description means the skill never fires, no matter how good the body is.

### What to include

1. **What it does** — a concise statement of the skill's output or capability
2. **When to use it** — explicit trigger phrases, domains, user intents
3. **Keywords** — include both formal terms and casual phrasings a real user might type

### Be slightly "pushy"

Claude tends to under-trigger skills. Lean toward explicit activation language:

```yaml
# Too vague — will often not trigger
description: Helps with pull request reviews.

# Better — explicit about when to activate
description: >
  Pull request code review. Activate when asked to review a PR, check a diff,
  or give feedback on code changes. Covers standard risk, elevated risk, API
  contracts, dependency bumps, CI/CD changes, and infrastructure changes.
  Applies the relevant sections based on what files the PR touches.
  Produces concise comments grouped by severity: Blocker / Important / Nit.
```

### Length guidelines

- **Aim for 150–400 characters** for most skills
- Do not pad to the 1024-char limit — filler dilutes signal
- Do not put "when to use" information only in the body; it belongs in `description`

### Good vs. poor examples

| | Example |
|---|---|
| ✅ Good | `"Extracts text and tables from PDF files, fills PDF forms, and merges multiple PDFs. Use when working with PDF documents or when the user mentions PDFs, forms, or document extraction."` |
| ❌ Poor | `"Helps with PDFs."` |
| ✅ Good | `"Creates a GitHub issue from a natural language prompt. Triggers on requests like 'create an issue for X', 'open a bug report about Y', 'file a feature request for Z', 'add a ticket for W'."` |
| ❌ Poor | `"Opens GitHub issues."` |

---

## 4. Writing the skill body

### Size and progressive disclosure

- **Target under 500 lines** for `SKILL.md`. If you are approaching this limit, move supporting detail into `references/` files and add clear pointers in `SKILL.md` telling the agent when and how to load them.
- For large reference files (> 300 lines), include a table of contents at the top.
- When a skill supports multiple distinct domains or frameworks, create a `references/` file per domain and let the skill body select which one to load based on context.

```
cloud-deploy/
├── SKILL.md            # workflow + selection logic
└── references/
    ├── aws.md
    ├── gcp.md
    └── azure.md
```

### Add only what the agent lacks

Focus on what the agent *would not* know without the skill: project-specific conventions, non-obvious edge cases, the particular APIs or tools to use, and team standards. Do not explain what a PDF is, how HTTP works, or what a migration does — the agent already knows.

```markdown
<!-- ❌ Too verbose — the agent already knows what PDFs are -->
PDF (Portable Document Format) files are common documents that contain text
and images. To extract text you need a library. pdfplumber is recommended.

<!-- ✅ Better — jumps to what the agent wouldn't know -->
Use pdfplumber for text extraction. For scanned documents, fall back to
pdf2image + pytesseract.
```

### Explain the why, not just the what

Prefer explaining *why* over issuing directives. Today's models respond better to reasoning than to rigid commands.

```markdown
<!-- ❌ Rigid — brittle and hard to reason about -->
ALWAYS use the imperative form. NEVER use passive voice.

<!-- ✅ Better — gives the model room to apply good judgment -->
Use imperative form in instructions (e.g. "Run the linter" not "The linter
should be run") — it is clearer and easier for the agent to follow.
```

### Bundle reusable scripts

If every test run of your skill independently writes the same helper script (a formatter, a validator, a transformer), bundle it in `scripts/` and reference it from `SKILL.md`. This saves every future invocation from reinventing the wheel.

### Format conventions

- Use `##` and `###` headings to structure the body
- Use numbered lists for sequential steps, bullet lists for non-ordered items
- Include short worked examples where they add clarity
- Keep code blocks minimal — a representative snippet beats an exhaustive reference

### Effective body patterns

| Pattern | When to use |
|---|---|
| **Gotchas** | Environment-specific facts the agent will get wrong without being told. Keep in `SKILL.md` itself — the agent reads it before encountering the situation. |
| **Output template** | When you need a specific output format. A concrete template is more reliable than describing the format in prose. |
| **Checklist** | Multi-step workflows where skipping a step causes downstream failures: `- [ ] Step 1: Run scripts/validate.py`. |
| **Validation loop** | Any task where the agent should self-check before finishing: do → run validator → fix errors → repeat until clean. |
| **Plan-validate-execute** | Batch or destructive operations: generate a plan file → validate it against a source of truth → execute. |

---

## 5. Testing your skill

Before proposing a PR, verify that your skill activates correctly and produces good output. The full testing
methodology — eval creation, fixture management, with/without comparisons, trigger testing, and description
optimization using the Anthropic [`skill-creator`](https://github.com/anthropics/skills/tree/main/skills/skill-creator)
skill — is covered in **[docs/testing/skill-testing.md](./docs/testing/skill-testing.md)**.

---

## 6. Proposing a skill via a pull request

1. **Open an issue first** using
   the [Skill Proposal template](https://github.com/AbsaOSS/agentic-toolkit/issues/new/choose) to discuss scope
   before writing code
2. Create your skill folder under `skills/` following the structure in [Skill structure](#1-skill-structure)
3. Run the tests described in [Testing your skill](#5-testing-your-skill) and include benchmark results in the PR description
4. Open a pull request; CODEOWNERS will be automatically requested for review
5. Optionally, add `Copilot` as a reviewer to get automated skill quality feedback

### PR checklist

Before opening a pull request, verify:

- [ ] Folder name matches the `name` frontmatter field exactly
- [ ] `name` is kebab-case, ≤ 64 chars, no consecutive hyphens
- [ ] `description` covers both *what it does* and *when to trigger*, with explicit keywords
- [ ] `description` is ≤ 1024 chars and not padded with filler
- [ ] `SKILL.md` body is < 500 lines, or uses progressive disclosure via `references/`
- [ ] No hardcoded credentials, secrets, or internal paths in skill body or scripts
- [ ] Any script in `scripts/` is referenced from `SKILL.md` with usage guidance
- [ ] New skill's description does not conflict with or shadow existing skills
- [ ] Skill added to the catalog table in `README.md`
- [ ] Evals exist (or a note explains why they are not applicable)
- [ ] `skills-ref validate ./skills/my-skill` passes (install: `pip install skills-ref`)
