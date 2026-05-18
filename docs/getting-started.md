# How to Start Using Skills?

This guide walks you through installing Agentic Skills and using them inside AI-assisted engineering tools.

## 1. Install the Vercel Skills CLI

Skills are distributed and installed using the [Vercel Skills CLI](https://github.com/vercel-labs/skills) — a lightweight tool available via `npx`, no separate installation required.

```bash
# Verify the CLI is accessible
npx skills --version
```

## 2. Install Skills From This Repository

### List available skills

```bash
npx skills add https://github.com/AbsaOSS/agentic-toolkit --list
```

### Install all Agentic Skills (global — available in every project)

```bash
npx skills add https://github.com/AbsaOSS/agentic-toolkit -g
```

### Install all Agentic Skills (project-scoped — installs into `.github/skills/` of the current repo)

```bash
npx skills add https://github.com/AbsaOSS/agentic-toolkit
```

> To share project-scoped skills with your team, commit the generated `.github/skills/` directory to your repository.

### Install a specific skill only

```bash
# Example: install only the pr-review skill, globally
npx skills add https://github.com/AbsaOSS/agentic-toolkit -g --skill pr-review
```

### Update installed skills

```bash
npx skills update         # interactive — prompts for scope
npx skills update -g      # update global skills only
npx skills update -y      # non-interactive, auto-detects scope
```

> **Installation method:** When running interactively, you'll be prompted to choose between **Symlink** (recommended — single source, easy updates) or **Copy** (use when symlinks aren't supported).

## 3. How Skills Work

Skills manage LLM context efficiently. The agent does **not** receive all skill content at startup — it loads content progressively:

| Phase | What Happens |
|---|---|
| **Discovery** | At startup, the agent loads only the `name` and `description` of each installed skill |
| **Activation** | When your task matches a skill's description, the agent reads the full `SKILL.md` into context |
| **Execution** | The agent follows the skill's step-by-step instructions, optionally reading reference files or running bundled scripts |

### What your prompt needs to contain

Because the `description` field is the agent's sole activation signal, your message must contain keywords or context that match it. For example:

- To trigger **pr-review**: mention "review", "pull request", or "PR".

> **Tip:** If a skill is not activating, rephrase your message to include more explicit keywords from the skill's description. You can inspect descriptions with `/skills list` inside a session.

## 4. GitHub Copilot CLI Guide

GitHub Copilot CLI is the repo-expected AI-assisted engineering tool. Skills are resolved from two locations:

| Scope | Location | When To Use |
|---|---|---|
| **Global** | `~/.copilot/skills/` | Available across all your projects, on every session start |
| **Project** | `.github/skills/` | Specific to one repository; commit the directory to share with your team |

When skills are installed with `-g`, the CLI places them in `~/.copilot/skills/`. Without `-g`, they go into `.github/skills/` of the current project.

### Inspecting loaded skills

Inside an active Copilot CLI session:

```
# See all available skills and their descriptions
/skills list

# See the full loaded environment (skills, agents, MCP servers, instructions)
/env
```

### Adding and removing skills mid-session

```
# Add a skill from a path into the current session
/skills add ~/.copilot/skills/pr-review

# Remove a skill from the current session
/skills remove pr-review
```

> **Note:** Changes made with `/skills add` or `/skills remove` inside a session are **temporary** — they only affect the running session. Use `npx skills add` from your terminal to make permanent changes.

### Stacking order

Copilot CLI resolves skills from two real locations in this order:

```
Global Skills    ← ~/.copilot/skills/   (loaded first)
    └── Project Skills  ← .github/skills/  (override global)
```

Project skills take precedence over global skills. Agentic Skills installed with `-g` are simply global skills — there is no separate "Agentic base" layer. Use project skills for repository-specific overrides that your team commits together.
