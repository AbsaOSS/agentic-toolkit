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
| [Responsible Agent Use](./responsible-agent-use.md) | Not burning your Copilot token budget — context, models, agent mode, MCP, plugins, skills, and a must-do checklist |
| [Agent Testing](./testing/agent-testing.md) | Eval creation and body quality testing for `.agent.md` files — agents are invoked by @-mention, not auto-triggered |
| [Skill Testing](./skill-testing.md) | Eval creation, fixtures, regression loops, trigger and description optimization |
| [Troubleshooting](./troubleshooting.md) | Setup fixes for install, activation, and proxy issues |

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
| [PR Review](./pr-review.md)             | How the PR review skill works, what sections it applies, and how to trigger it     |
| [TDD Workflow](./tdd-workflow.md)       | Test-driven development with: specification, confirmation gates, and vertical-sliced implementation |
| [Test Data Management](./test-data-management.md)   | How the test-data-management skill works, what it covers, and when it fires |
| [Test Mocking Patterns](./test-mocking-patterns.md) | Double selection, patching strategies, cleanup, and language-specific guidance |
| [Unit Test Standards](./test-unit-standards.md)  | Reference for unit test standards across isolation, scope, naming, assertions, coverage, fixtures |
| [Unit Test Writer](./test-unit-write.md)         | Generate complete unit tests from scratch following language-specific standards |
| [Unit Test Reviewer](./test-unit-review.md)      | Systematically audit unit tests and report findings by severity |
| [Token Saving](./token-saving.md)       | Keeping AI responses concise — how the token-saving skill works and when it applies |

## Agent Guides

| Guide                                         | Description                                                                              |
|-----------------------------------------------|-------------------------------------------------------------------------|
| [Living Doc BDD Copilot](./guides/living-doc-bdd-copilot.md) | Living documentation and BDD automation — catalog management (User Stories, Features, Functionalities, AC updates, impact analysis, gap finding) and automation (webapp exploration, PageObjects, Gherkin, step definitions, maintenance) |

> **Keep this index up to date.** When you add a new guide, add a row to the appropriate table above.

See also the [main README](../README.md) for the skill catalog, scope, and FAQ.
