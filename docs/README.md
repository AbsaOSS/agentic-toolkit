# Documentation

Navigation hub for all guides in this repository. Browse by category below.

## Contents

- [Setup & Repository Guides](#setup--repository-guides)
- [Tools for Agentic Development](#tools-for-agentic-development)
- [Skill Guides](#skill-guides)
- [Agent Guides](#agent-guides)

## Setup & Repository Guides

| Guide                                   | Description                                                                         |
|-----------------------------------------|-------------------------------------------------------------------------------------|
| [Getting Started](./getting-started.md) | What skills are, how to install them, Copilot CLI usage                             |
| [Contributing](../CONTRIBUTING.md)  | Skill folder layout, frontmatter, description writing, body guidelines, PR process |
| [Agent Design Best Practices](./guides/agent-design.md) | Core principles, file structure, context management, tool guidance, examples, and stopping conditions for `.agent.md` files |
| [Skill Testing](./testing/skill-testing.md) | Eval creation, fixtures, regression loops, trigger and description optimization    |
| [Agent Testing](./testing/agent-testing.md) | Eval creation, trigger accuracy tuning, and body quality testing for `.agent.md` files |
| [Troubleshooting](./troubleshooting.md) | Setup fixes for install, activation, and proxy issues                               |

## Tools for Agentic Development

| Guide                       | Description                                                        |
|-----------------------------|--------------------------------------------------------------------|
| [Tools Overview](./tools/)    | Catalog of CLI-based AI coding agents and agentic development tools |
| [Pi Coding Agent](./tools/pi.md) | Minimal BYOK terminal agent -- quickstart, extensions, troubleshooting |
| [GitHub Copilot CLI](./tools/copilot-cli.md) | Multi-model agentic terminal agent with native GitHub integration |
| [CodeBurn](./tools/codeburn.md) | Token usage, cost, and performance dashboard for 25+ AI coding tools |

## Skill Guides

| Guide                               | Description                                                                        |
|-------------------------------------|------------------------------------------------------------------------------------|
| [PR Review](./guides/pr-review.md)             | How the PR review skill works, what sections it applies, and how to trigger it     |
| [Token Saving](./guides/token-saving.md)       | Keeping AI responses concise — how the token-saving skill works and when it applies |

## Agent Guides

| Guide                                         | Description                                                                              |
|-----------------------------------------------|-------------------------------------------------------------------------|
| [Living Doc BDD Copilot](./guides/living-doc-bdd-copilot.md) | The unified living documentation agent: catalog management (User Stories, Features, Functionalities, AC updates, impact analysis, gap finding) plus BDD automation (webapp exploration, PageObjects, Gherkin, step definitions, maintenance) |

> **Keep this index up to date.** When you add a new guide, add a row to the appropriate table above.

See also the [main README](../README.md) for the skill catalog, scope, and FAQ.
