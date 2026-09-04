# Documentation

Navigation hub for all guides in this repository. Browse by category below.

## Contents

- [Repository Guides](#repository-guides)
- [Agent Development Guides](#agent-development-guides)
- [Tools for Agentic Development](#tools-for-agentic-development)
- [Agent Guides](#agent-guides)
- [Skill Guides](#skill-guides)
  - [Solo Skills (Standalone, No Dependencies)](#solo-skills-standalone-no-dependencies)
  - [QA And Testing Skills](#qa-and-testing-skills)
  - [Living Documentation & BDD Skills](#living-documentation--bdd-skills)
    - [Catalog & Entity Creation](#catalog--entity-creation)
    - [BDD Workflow & Automation](#bdd-workflow--automation)
    - [Analysis & Maintenance](#analysis--maintenance)

## Repository Guides

Fundamental setup, conventions, and troubleshooting for working with skills in this repository.

| Guide                                   | Description                                                                         |
|-----------------------------------------|-------------------------------------------------------------------------------------|
| [Getting Started](./getting-started.md) | What skills are, how to install them, Copilot CLI usage                             |
| [Contributing](../CONTRIBUTING.md)  | Skill folder layout, frontmatter, description writing, body guidelines, PR process |
| [Skill Testing](./testing/skill-testing.md) | Eval creation, fixtures, regression loops, trigger and description optimization |
| [Troubleshooting](./troubleshooting.md) | Setup fixes for install, activation, and proxy issues |

## Agent Development Guides

Core practices for designing, testing, and deploying agent workflows with Copilot.

| Guide                                   | Description                                                                         |
|-----------------------------------------|-------------------------------------------------------------------------------------|
| [Agent Design Best Practices](./guides/agent-design.md) | Core principles, file structure, context management, tool guidance, examples, and stopping conditions for `.agent.md` files |
| [Responsible Agent Use](./responsible-agent-use.md) | Not burning your Copilot token budget — context, models, agent mode, MCP, plugins, skills, and a must-do checklist |
| [Agent Testing](./testing/agent-testing.md) | Eval creation and body quality testing for `.agent.md` files — agents are invoked by @-mention, not auto-triggered |

## Tools for Agentic Development

CLI-based agents and dashboards for terminal-driven coding and cost tracking.

| Guide                       | Description                                                        |
|-----------------------------|--------------------------------------------------------------------|
| [Tools Overview](./tools/)    | Catalog of CLI-based AI coding agents and agentic development tools |
| [Pi Coding Agent](./tools/pi.md) | Minimal BYOK terminal agent -- quickstart, extensions, troubleshooting |
| [GitHub Copilot CLI](./tools/copilot-cli.md) | Multi-model agentic terminal agent with native GitHub integration |
| [CodeBurn](./tools/codeburn.md) | Token usage, cost, and performance dashboard for 25+ AI coding tools |

## Agent Guides

Orchestrated agent workflows that coordinate multiple skills for complex tasks.

| Guide                                         | Description                                                                              |
|-----------------------------------------------|-------------------------------------------------------------------------|
| [Living Doc BDD Copilot](./guides/living-doc-bdd-copilot.md) | Living documentation and BDD automation — catalog management (User Stories, Features, Functionalities, AC updates, impact analysis, gap finding) and automation (webapp exploration, PageObjects, Gherkin, step definitions, maintenance) |

## Skill Guides

Task-specific guidance for using individual skills. Start by picking your use case below.

### Solo Skills (Standalone, No Dependencies)

| Guide | Description |
|---|---|
| [Token Saving](./guides/token-saving.md) | Keeping AI responses concise — how the token-saving skill works and when it applies |
| [PR Review](./guides/pr-review.md) | How the PR review skill works, what sections it applies, and how to trigger it |
| [Create Repository](./create-repository.md) | Creating a new AbsaOSS/absa-group repo from the template with standard guardrails |

### QA And Testing Skills

| Guide | Description |
|---|---|
| [Accessibility Infra Setup](./guides/accessibility-infra-setup.md) | Bootstrap Playwright + axe-core a11y infrastructure in an Angular app (WCAG 2.2 AA) — config, shared fixture, one example scan, npm scripts, docs |
| [TDD Workflow](./guides/tdd-workflow.md) | Test-driven development with: specification, confirmation gates, and vertical-sliced implementation |
| [Unit Test Standards](./guides/test-unit-standards.md) | Reference for unit test standards across isolation, scope, naming, assertions, coverage, fixtures |
| [Unit Test Writer](./guides/test-unit-write.md) | Generate complete unit tests from scratch following language-specific standards |
| [Unit Test Reviewer](./guides/test-unit-review.md) | Systematically audit unit tests and report findings by severity |
| [Test Data Management](./guides/test-data-management.md) | How the test-data-management skill works, what it covers, and when it fires |
| [Test Mocking Patterns](./guides/test-mocking-patterns.md) | Double selection, patching strategies, cleanup, and language-specific guidance |

### Living Documentation & BDD Skills

**Start here:** [`@living-doc-bdd-copilot`](./guides/living-doc-bdd-copilot.md) — orchestrates the full workflow.

#### Catalog & Entity Creation

| Guide | Description |
|---|---|
| [Create User Story](./guides/living-doc-create-user-story.md) | Author well-formed User Stories with business-level ACs ready for E2E scenarios |
| [Create Feature](./guides/living-doc-create-feature.md) | Document system surfaces (UI screens, APIs, services) as Feature entities |
| [Create Functionality](./guides/living-doc-create-functionality.md) | Define atomic, testable behaviors with Acceptance Criteria for unit/integration tests |
| [Update Living Doc](./guides/living-doc-update.md) | Amend entities: add ACs, change status, deprecate, update ownership and links |

#### BDD Workflow & Automation

| Guide | Description |
|---|---|
| [Gherkin Step Definitions](./guides/gherkin-step.md) | Multi-language step definition patterns: Python behave, TypeScript/Java Cucumber, Scala; state sharing, hooks, parameter types |
| [Scenario Creator](./guides/living-doc-scenario-creator.md) | Convert User Story and Functionality ACs to Gherkin scenarios with full traceability tagging |
| [Gherkin ↔ Living Doc Sync](./guides/gherkin-living-doc-sync.md) | Keep scenarios and ACs in sync: audit AC links, fix drift, propagate changes |
| [PageObject Scan](./guides/living-doc-pageobject-scan.md) | Discover, create, and maintain Playwright PageObjects: bootstrap, re-scan after UI changes, heal selector drift |
| [Data-Cy Instrument](./guides/data-cy-instrument.md) | Add missing test-id attributes to templates; sync PageObjects to use `getByTestId()` |

#### Analysis & Maintenance

| Guide | Description |
|----|----|
| [BDD Maintenance](./guides/bdd-maintain.md) | Clean up BDD artifacts: remove deprecated feature files, find dead code, audit unused steps and PageObject methods |
| [Gap Finder](./guides/living-doc-gap-finder.md) | Audit living doc completeness: find undocumented features, orphan tests, untested ACs; produce gap reports |
| [Impact Analysis](./guides/living-doc-impact-analysis.md) | Trace PR impact on living doc: identify affected Features, Functionalities, User Stories; determine what to review/re-test |

> **Keep this index up to date.** When you add a new guide, add a row to the appropriate table above.

See also the [main README](../README.md) for the skill catalog, scope, and FAQ.
