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
| **[living-doc-create-user-story](./skills/living-doc-create-user-story/)** | Create a well-formed User Story with business-level Acceptance Criteria that are traceable, testable, and E2E-ready. |
| **[living-doc-create-feature](./skills/living-doc-create-feature/)** | Document a system surface (UI screen, API endpoint, service) as a Feature entity with ownership and traceability links. |
| **[living-doc-create-functionality](./skills/living-doc-create-functionality/)** | Define an atomic, testable behaviour (Functionality) with AC designed for fast unit or integration tests. |
| **[living-doc-update](./skills/living-doc-update/)** | Amend or deprecate existing User Story, Feature, or Functionality entities — add ACs, change status, update ownership. |
| **[living-doc-impact-analysis](./skills/living-doc-impact-analysis/)** | Trace which Features, Functionalities, User Stories, and Gherkin scenarios are affected by a code change or PR. |
| **[living-doc-gap-finder](./skills/living-doc-gap-finder/)** | Identify undocumented behaviours, orphan tests, and untested ACs. Shared by `@living-doc-copilot` and `@living-doc-bdd-copilot`. |
| **[living-doc-pageobject-scan](./skills/living-doc-pageobject-scan/)** | Discover, create, and maintain PageObject classes from a live web application — bootstrapping from scratch and detecting selector drift after UI changes. |
| **[living-doc-scenario-creator](./skills/living-doc-scenario-creator/)** | Generate Gherkin scenario skeletons from User Story ACs — one scenario per AC, coverage report, and missing step identification. |
| **[gherkin-scenario](./skills/gherkin-scenario/)** | Write BDD Gherkin scenarios in plain business language — Given/When/Then rules, anti-patterns, Scenario Outlines, and Background. |
| **[gherkin-step](./skills/gherkin-step/)** | Implement clean, reusable step definitions — behave (Python), Cucumber (Java, TypeScript, Scala), parameter types, DataTable, DocString, and hooks. |
| **[gherkin-living-doc-sync](./skills/gherkin-living-doc-sync/)** | Synchronise Gherkin feature files with the living documentation catalog — fix missing AC traceability headers, step text drift, and stale scenario links. |
| **[token-saving](./skills/token-saving/)**           | Always-active response discipline — enforces brevity, no filler openers or closers, structured output, and a What/Why/How footer on code responses. Suspends on explicit "full detail" requests. |

## Agent Roster

Agents are pre-configured AI personas that orchestrate multiple skills for a specific engineering phase. Agent files live in **[.github/agents/](./.github/agents/)**.

| Agent | Description |
|---|---|
| **[@living-doc-copilot](./.github/agents/living-doc-copilot.agent.md)** | Creates and maintains the living documentation catalog: User Stories, Features, Functionalities, AC updates, impact analysis, gap finding. |
| **[@living-doc-bdd-copilot](./.github/agents/living-doc-bdd-copilot.agent.md)** | Automation layer: explores web apps via MCP Playwright, generates PageObjects and Gherkin scenarios, writes step definitions, and maintains the BDD suite across RE-SCAN, HEALING, and REMOVE phases. |

## Finding More Skills

Before building a new skill, check whether one already exists:

| Source                                                                               | What's Available                                                        |
|--------------------------------------------------------------------------------------|-------------------------------------------------------------------------|
| [github/awesome-copilot](https://github.com/github/awesome-copilot/tree/main/skills) | 200+ community skills: cloud, languages, security, DevOps, productivity |
| [skills.sh](https://skills.sh)                                                       | Open registry — install with `npx skills add <owner/repo>`              |
| [anthropics/skills](https://github.com/anthropics/skills)                            | Anthropic reference skills including `skill-creator`                    |
| [absa-group/agent-skills](https://github.com/absa-group/agent-skills)                | Broader ABSA-owned skill collection                                     |
| [absa-group/cps-agentic-toolkit](https://github.com/absa-group/cps-agentic-toolkit)  | CPS team's extended skill set (ABSA-internal)                           |

## Contributing

See **[CONTRIBUTING.md](./CONTRIBUTING.md)** for the skill authoring guide — folder layout, frontmatter schema, writing
effective descriptions and bodies, [testing](./docs/testing/skill-testing.md), and the PR checklist.

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
