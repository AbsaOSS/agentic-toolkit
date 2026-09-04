# Accessibility Infra Setup Skill

The `accessibility-infra-setup` skill bootstraps automated accessibility (a11y) check infrastructure in an existing Angular application using [Playwright](https://playwright.dev/) + [axe-core](https://github.com/dequelabs/axe-core) (`@axe-core/playwright`). It scaffolds the plumbing to catch automatically detectable **WCAG 2.2 AA** violations and proves it works with one passing example scan.

It activates when you ask to set up accessibility checks, add a11y testing infrastructure, or wire axe-core into an Angular app.

---

## What it does

The skill extends your existing test setup rather than replacing it, then validates the result end to end:

| Step | Action |
|------|--------|
| Detect | Inspects `package.json`, the dev-server script, package manager, and any existing Playwright / Cypress setup |
| Install | Adds `@playwright/test` + `@axe-core/playwright` and installs the Chromium browser |
| Scaffold | Creates `playwright.config.ts`, a shared axe fixture, and one dummy example scan |
| Wire scripts | Adds `test:a11y*` npm scripts to `package.json` |
| Validate | Runs the dummy scan until it passes green — the definition of done |
| Document | Adds `docs/accessibility.md` (or `playwright/README.md`) with how to run and where reports land |

**Scope:** infrastructure plus exactly **one** dummy example scan. Authoring real accessibility tests, fixing violations, and CI wiring are all out of scope.

---

## Expected outcome

After the skill runs, the repository contains:

```
playwright/
├── fixtures/
│   └── axe-helpers.ts                  # Shared axe fixture (WCAG 2.2 AA tags) + assertion helpers
└── a11y/
    └── example.accessibility.spec.ts   # ONE dummy scan of the "/" route — passes
playwright.config.ts                    # `accessibility` project (Desktop Chrome, testMatch /accessibility/)
docs/accessibility.md                   # How to run, where reports land
```

Running `npm run test:a11y` starts the dev server, runs the dummy scan on Desktop Chrome, and passes green.

---

## How to trigger it

Ask naturally — the skill fires on intent, not exact wording:

```
set up accessibility checks
add a11y testing infrastructure
add axe-core to this Angular app
set up WCAG testing
add accessibility scans with Playwright
bootstrap a11y infra
```

---

## Requirements

- An existing Angular application with a runnable dev server (`npm run start` on port 4200)
- Node.js 22+
- Network access on first run (Playwright downloads the Chromium browser)

---

## Coexistence rules

- **Never touches Cypress.** If the repo uses Cypress, its config, specs, and dependencies are left untouched — Playwright is added alongside it.
- **Extends, doesn't recreate Playwright.** When a `playwright.config.*` already exists, the skill merges an `accessibility` project into it and reuses any existing axe fixture instead of adding a duplicate.

---

## Installation

The skill is installed along with the rest of the toolkit:

```bash
npx skills add https://github.com/AbsaOSS/agentic-toolkit -g
```

To install only this skill:

```bash
npx skills add https://github.com/AbsaOSS/agentic-toolkit -g --skill accessibility-infra-setup
```

See [Getting Started](../getting-started.md) for the full install guide.
