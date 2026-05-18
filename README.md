# Agentic Toolkit

Curated, reusable AI skills — instructional context, domain conventions, and callable agent tools for any AI-assisted engineering.

---

## What Is A Skill?

**Skills** are folders of instructions, scripts, and resources that an AI agent can load on demand to improve its performance on specialised tasks.

The Agent Skills format is an open standard maintained by Anthropic, adopted by GitHub Copilot and other AI systems. See the [full specification](https://agentskills.io) and the [spec repository](https://github.com/agentskills/agentskills).

### How Skills Work

Skills manage an LLM context efficiently — the agent is not given all skill content upfront:

1. **Discovery** — At startup, the agent loads only the `name` and `description` of each available skill
2. **Activation** — When a task matches a skill's description, the agent reads the full `SKILL.md` into context
3. **Execution** — The agent follows the instructions, optionally loading referenced files or executing bundled scripts

> ⚠️ **The `description` field is your most important content.** It is the sole signal the agent uses to decide whether to activate a skill. A vague description means the skill will never fire. See [CONTRIBUTING.md](./CONTRIBUTING.md) for authoring guidance.
> 
> For detailed skill testing and evaluation methodology, see [docs/SKILL_TESTING.md](docs/SKILL_TESTING.md).

### Skill Structure

Each skill lives in its own folder, which is a top-level directory in this repository:

```
skill-name/
├── SKILL.md          # Required — metadata frontmatter + instructions
├── scripts/          # Optional — executable code the agent can run
├── references/       # Optional — supporting documentation and specs
├── assets/           # Optional — templates, examples, resources
└── evals/            # Optional — test prompts and assertions
```

The `SKILL.md` file follows a standard frontmatter schema:

```yaml
---
name: skill-name                  # kebab-case, max 64 chars
description: >                    # max 1024 chars — what it does AND when to use it
  What this skill does and the specific situations in which it should be activated.
  Be explicit. Include keywords that describe the task, domain, and trigger conditions.
license: Proprietary              # optional
compatibility: GitHub Copilot     # optional — intended tools or environment requirements
---

# Skill Title

## When To Use This Skill
...

## Instructions
...
```

Required fields: `name`, `description`. Everything else is optional.

---

## Skill Scopes

GitHub Copilot, the primary AI productivity assistant, resolves skills from two locations:

| Scope | Location | When To Use |
|---|---|---|
| **Personal Skills** | `~/.copilot/skills/` | Skills available across all your projects |
| **Project Skills** | `.github/skills/` | Skills specific to a single repository |

Other Agent Skills-compatible tools typically use:

| Scope | Location |
|---|---|
| **Personal** | `~/.agents/skills/` |
| **Project** | `.agents/skills/` |

---

## How Skills Relate To Your Own

The skills in this repo are the **base layer** — conventions and capabilities applicable across most teams and projects in the sub-department. You load them into your personal space and extend with your own layers:

```
Agentic Skills              ← shared base (this repo)
    └── Personal Skills         ← your individual skills (~/.copilot/skills/)
            └── Project Skills  ← repository-specific (.github/skills/)
```

The base layer is the **foundation every engineer might share**. Personal and project layers are **extensions** — not replacements. If something belongs in the base, propose it here rather than duplicating it downstream.

---

## Quickstart

This repo uses Copilot as the primary AI-assisted engineering tool. There are many ways how to use it, but here we leverage the [GitHub Copilot CLI](https://github.com/github/copilot-cli). Skills are managed through slash commands inside a Copilot CLI session.

### 1. Install GitHub Copilot CLI

```bash
# macOS / Linux
curl -fsSL https://gh.io/copilot-install | bash

# macOS (Homebrew)
brew install copilot-cli

# Any platform (npm)
npm install -g @github/copilot
```

Then launch a session from your project directory:

```bash
copilot
```

### 2. Add Skills To Your Personal Space

Inside a Copilot CLI session, add skills from this repo one by one:

```
/skills add ~/.copilot/skills/pr-review
/skills add ~/.copilot/skills/create-issue
/skills add ~/.copilot/skills/kudos
```

Or clone this repo and add all skills at once from your terminal before launching:

```bash
git clone https://github.com/AbsaOSS/agentic-toolkit.git
cp -r agentic-toolkit/skills/*/  ~/.copilot/skills/
```

Skills in `~/.copilot/skills/` are loaded automatically at every session start — no further action needed.

### 3. Verify Skills Are Loaded

Inside a session, inspect the full loaded environment:

```
/env
```

This shows all loaded skills, MCP servers, agents, and instructions. Confirm your skills appear in the list.

Alternatively, see all the available skills:

```
/skills list
```

### 4. Add Project-Specific Skills (Optional)

For skills that only apply to a specific repository, place them in `.github/skills/` within that repo. These are loaded automatically when Copilot CLI is launched from that directory, layered on top of your personal as well as these project-specific skills.

```
your-project-repo/
└── .github/
    └── skills/
        └── your-project-skill/
            └── SKILL.md
```

---

## Using Review Skills With the Native Copilot Reviewer

The native Copilot reviewer is the **Add Copilot as reviewer** button on a pull request on GitHub.com. It reads `.github/copilot-instructions.md` in your repository.

This repo provides a set of review-related skills. `pr-review` is the first and most broadly applicable — a single unified skill covering standard review, elevated risk, API contracts, dependency bumps, CI/CD changes, and infrastructure. Additional review skills can be added to the instructions file in the same way.

To apply review standards when Copilot is added as a reviewer on GitHub.com, add the following to your project's `.github/copilot-instructions.md`:

```markdown
## PR Review

### Core review skill — covers standard, elevated risk, API contracts, deps, CI/CD, and IaC
When reviewing a pull request, load and apply:
https://github.com/AbsaOSS/agentic-toolkit/blob/master/skills/pr-review/SKILL.md

Apply only the sections relevant to the files touched by the PR.
Output findings grouped as: Blocker / Important / Nit.
```

---

## Finding More Skills

Before building a new skill, check whether one already exists:

| Source | What's available |
|---|---|
| [github/awesome-copilot](https://github.com/github/awesome-copilot/tree/main/skills) | 200+ community skills: cloud, languages, security, DevOps, productivity |
| [skills.sh](https://skills.sh) | Open registry — install any GitHub-hosted skill with `npx skills add <owner/repo>` |
| [anthropics/skills](https://github.com/anthropics/skills) | Anthropic reference skills including `skill-creator` |
| [AbsaOSS/agentic-toolkit](https://github.com/AbsaOSS/agentic-toolkit) | Broader skill collection |

---

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md) for the full authoring guide.

To propose a new skill or a change to an existing one, open an issue using the **Skill Proposal** template.
