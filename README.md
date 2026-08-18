# Agentic Toolkit

Curated, reusable AI skills — instructional context, domain conventions, and callable agent tools for AI-assisted
engineering.

Every AI assistant starts from zero — no accumulated engineering experience, no reusable workflows. This repo fixes
that. It's a curated library of **skills**: bundles of domain knowledge, engineering patterns, and proven practices
packaged for any [Agent Skills](https://agentskills.io)-compatible client (Copilot, Claude, Cursor, and others). The
knowledge here is not internal or proprietary — it reflects universal software engineering practices used at ABSA.
Tomorrow the scope may expand to agents, MCP servers, and plugins as agentic tooling matures (see [Scope](#scope)).

**Who is this for?** Anyone who uses AI for AI-assisted engineering. The primary audience is technical: engineers, tech
leads, architects, or anyone on a technical team.

## Table of Contents

- [Scope](#scope)
- [How Skills Relate To Your Own](#how-skills-relate-to-your-own)
- [Quickstart](#quickstart)
- [Skill Catalog](#skill-catalog)
- [Finding More Skills](#finding-more-skills)
- [Contributing](#contributing)
- [FAQ](#faq)
- [Troubleshooting](#troubleshooting)

## Scope

This repo currently focuses on **Skills** — basically just folders of instructions, scripts, and resources that an AI
agent can load on demand to improve its performance on specialised tasks.

As our use of agentic tooling matures, the scope may expand to include:

- **Agents** — custom agent definitions for recurring engineering tasks (code review, architecture, research)
- **MCP Servers** — callable tool servers giving agents access to internal systems and data
- **Plugins** — bundled distributions packaging skills, agents, and MCP servers into a single install

If and when that happens, the repo structure, name, and install instructions will be updated accordingly. For now,
skills are the right place to start — they are the lowest friction, highest value layer, and the foundation everything
else builds on.

## How Skills Relate To Your Own

The skills in this repo are the **base layer** — shared conventions and capabilities applicable across teams and
projects. You load them into your personal or project space and extend with your own layers, so every session inherits
the team's collective knowledge or workflows.

If something might help the wider team, it belongs here.

```
Agentic Skills                    ← shared base (this repo)
    └── Personal Skills           ← your individual skills (~/.copilot/skills/ or ~/.agents/skills/)
            └── Project Skills    ← repository-specific (most commonly in .github/skills/)
```

Each layer extends the one above — personal and project layers are **extensions**, not replacements.

## Quickstart

Skills are managed through the [Vercel Skills CLI](https://github.com/vercel-labs/skills) or via
[GitHub Copilot CLI](https://github.com/github/copilot-cli) slash commands.

```bash
# Install all skills globally
npx skills add https://github.com/AbsaOSS/agentic-toolkit -g

# Or install a single skill
npx skills add https://github.com/AbsaOSS/agentic-toolkit -g --skill pr-review
```

For the full guide — what skills are, how they activate, project-scoped installs, updates, Copilot CLI commands — see
**[docs/getting-started.md](./docs/getting-started.md)**.

## Skill Catalog

Browse all available skills in the **[skills/](./skills/)** directory — each skill folder contains a `SKILL.md` with
its purpose, trigger phrases, and full instructions.

| Skill                                                | Description                                                                                                                         |
|------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------|
| **[pr-review](./skills/pr-review/)**                 | Pull request code review — reviews diffs for risk, security issues, API contract changes, dependency bumps, CI/CD and infrastructure changes. Produces concise Blocker / Important / Nit comments. |
| **[tdd-workflow](./skills/tdd-workflow/)**           | Test-driven development: upfront SPEC.md planning + confirmation gate (avoids batch design), then vertical-sliced implementation (one test → one code cycle at a time, not all tests then all code). |
| **[test-data-management](./skills/test-data-management/)** | Test data setup and management — factory functions, parametrised tests, deterministic seeds, fixture reuse, and production-data rules for unit and integration tests. |
| **[test-mocking-patterns](./skills/test-mocking-patterns/)** | Test double selection and implementation — classifies mock, stub, spy, fake, and dummy; guides patching strategy and cleanup for Python (pytest-mock), JavaScript/TypeScript (Jest), and Scala (mockito-scala). |
| **[test-unit-standards](./skills/test-unit-standards/)** | Reference for unit test standards across isolation, scope, naming, assertions, coverage, and fixtures. Language-specific guidance (pytest, Jest, MUnit) with principles and conventions. |
| **[test-unit-write](./skills/test-unit-write/)**     | Generate unit tests from scratch following language-specific standards. Analyzes source, selects mock strategies, and produces tests covering happy paths, failure conditions, and edge cases. |
| **[test-unit-review](./skills/test-unit-review/)**   | Systematically audit unit test suites. Runs test runner, checks isolation/scope/naming/assertions/coverage standards, and reports findings by severity (Blocker / Important / Nit). |
| **[token-saving](./skills/token-saving/)**           | Always-active response discipline — enforces brevity, no filler openers or closers, structured output, and a What/Why/How footer on code responses. Suspends on explicit "full detail" requests. |

## Finding More Skills

Before building a new skill, check whether one already exists:

| Source                                                                               | What's Available                                                        |
|--------------------------------------------------------------------------------------|-------------------------------------------------------------------------|
| [github/awesome-copilot](https://github.com/github/awesome-copilot/tree/main/skills) | 200+ community skills: cloud, languages, security, DevOps, productivity |
| [skills.sh](https://skills.sh)                                                       | Open registry — install with `npx skills add <owner/repo>`              |
| [anthropics/skills](https://github.com/anthropics/skills)                            | Anthropic reference skills including `skill-creator`                    |

## Contributing

See **[CONTRIBUTING.md](./CONTRIBUTING.md)** for the skill authoring guide — folder layout, frontmatter schema, writing
effective descriptions and bodies, [testing](./docs/skill-testing.md), and the PR checklist.

To propose a new skill — or to propose expanding the repo into agents, MCP servers, or
plugins — [open an issue](https://github.com/AbsaOSS/agentic-toolkit/issues/new).

Contributions are welcome from anyone.

## FAQ

### What's the difference between a skill, an agent, and an MCP server?

A **skill** gives the agent instructions — prose it reads into context when a task matches.
An **agent** is a full persona: a system prompt, tools, and behavioural constraints bundled together — it may *use*
multiple skills. An **MCP server** gives the agent callable tools for live integrations and API calls.
Think of skills as books, agents as the people who read them, and MCP servers as the phone lines they dial.

### Can I use these skills outside of GitHub Copilot?

Yes. Skills follow the open [Agent Skills](https://agentskills.io) standard and work with any compatible tool —
Claude, Cursor, Windsurf, and custom pipelines.

## Troubleshooting

Setup issues and common fixes are covered in **[docs/troubleshooting.md](./docs/troubleshooting.md)**.
All documentation guides are indexed at **[docs/](./docs/)**.
