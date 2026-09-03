---
name: accessibility-infra-setup
description: >
  Sets up automated accessibility (a11y) check infrastructure in an existing Angular application
  using Playwright + axe-core (@axe-core/playwright), asserting WCAG 2.2 AA compliance. Detects the
  existing test setup, installs and wires Playwright with a dedicated `accessibility` project,
  scaffolds a shared axe fixture, adds one dummy example scan, wires npm scripts, documents how to
  run the checks, and validates that the sample passes. Activates on requests like: "set up
  accessibility checks", "add a11y testing infrastructure", "add axe-core to this Angular app",
  "set up WCAG testing", "add accessibility scans with Playwright", "bootstrap a11y infra".
  Scope is infrastructure only plus ONE dummy example test — authoring real accessibility tests is
  a separate concern and out of scope.
license: Apache-2.0
compatibility: >
  Requires an existing Angular application with a runnable dev server (`npm run start` on port 4200)
  and Node.js 22+. Installs Playwright browsers, which needs network access on first run.
---

# accessibility-infra-setup

Bootstraps Playwright + axe-core accessibility infrastructure in an existing Angular app. Follows the
[AbsaOSS/cps-shared-ui](https://github.com/AbsaOSS/cps-shared-ui) pattern, generalized for a plain
application (not a component library).

**Scope:** infrastructure + exactly one dummy example scan. Do **not** author real accessibility
tests here — that is a separate follow-up task.

## Expected outcome

After this skill runs, the repository contains:

```
playwright/
├── fixtures/
│   └── axe-helpers.ts                  # Shared axe fixture (WCAG 2.2 AA tags) + assertion helpers
└── a11y/
    └── example.accessibility.spec.ts   # ONE dummy scan of the "/" route — passes
playwright.config.ts                    # `accessibility` project (Desktop Chrome, testMatch /accessibility/)
docs/accessibility.md                   # How to run, where reports land (or playwright/README.md)
```

- `package.json` gains `@playwright/test` + `@axe-core/playwright` (devDependencies) and
  `test:a11y*` scripts.
- `npm run test:a11y` starts the dev server, runs the dummy scan on Desktop Chrome, and **passes
  green**. That green run is the definition of done.

## Workflow

Copy this checklist and track progress:

```
- [ ] Step 1: Detect existing test infrastructure
- [ ] Step 2: Install dependencies
- [ ] Step 3: Scaffold config + fixture + example spec
- [ ] Step 4: Wire npm scripts
- [ ] Step 5: Validate (run the dummy scan → green)
- [ ] Step 6: Document
```

### Step 1 · Detect existing test infrastructure

Inspect the repo before writing anything — the goal is to **extend, not clobber**.

1. Read `package.json`: note the dev-server script (usually `start` → `ng serve`, port 4200), the
   package manager (from `package-lock.json` / `yarn.lock` / `pnpm-lock.yaml`), and any existing
   `@playwright/test`, `@axe-core/playwright`, Cypress, or Karma entries.
2. Check for an existing `playwright.config.*` and for Cypress (`cypress.config.*`, a `cypress/`
   folder, or a `cypress` devDependency).

Pick exactly one path based on what Playwright infra exists — Cypress never changes the decision:

- **Playwright already configured** (a `playwright.config.*` exists) → **adjust it in place, do not
  recreate it.** Merge in an `accessibility` project
  `{ name: 'accessibility', testMatch: /accessibility/, use: { ...devices['Desktop Chrome'] } }`,
  add `testIgnore: /accessibility/` to existing functional projects, and ensure `webServer` starts
  the Angular dev server. Keep the user's existing `testDir` and place a11y specs accordingly. Reuse
  any existing axe fixture instead of adding a second one.
- **No Playwright yet** → fresh setup. Copy `assets/playwright.config.ts` to the repo root and
  scaffold the full structure in Step 3.

**Cypress is off-limits either way.** If Cypress is present, treat it as read-only: never edit,
migrate, or delete Cypress config, specs, or dependencies, and never fold a11y scans into Cypress.
The two runners coexist — Playwright owns accessibility, Cypress keeps whatever it already covers.
Cypress existing does **not** make this a "fresh" or "adjust" decision; only the presence/absence of
a `playwright.config.*` does.

Confirm the dev-server command and port with the user only if they differ from `npm run start` /
`4200`; otherwise proceed.

### Step 2 · Install dependencies

Use the repo's package manager. For npm:

```bash
npm install -D @playwright/test @axe-core/playwright
npx playwright install chromium
```

`npx playwright install chromium` downloads the browser and needs network access. If Playwright was
already installed, skip the packages but still ensure the Chromium browser is present.

### Step 3 · Scaffold config, fixture, and example spec

Create these files (templates live in this skill's `assets/`):

1. `playwright.config.ts` (root) — from `assets/playwright.config.ts` (fresh setup only; otherwise
   merge as in Step 1). Adjust `baseURL`, `webServer.command`, and port if the app differs.
2. `playwright/fixtures/axe-helpers.ts` — copy verbatim from `assets/axe-helpers.ts`. This is the
   single source of the WCAG 2.2 AA tag set; every scan must build from `makeAxeBuilder`.
3. `playwright/a11y/example.accessibility.spec.ts` — from `assets/example.accessibility.spec.ts`.
   Verify the import path resolves to the fixture (`../fixtures/axe-helpers`) given where you place
   the spec, and point `page.goto('/')` at a route that renders without auth. If the app's landing
   route requires login, use a known public route instead and note it.

The `accessibility` substring in the spec filename is what routes it to the accessibility project —
keep it.

### Step 4 · Wire npm scripts

Add to `package.json` `scripts` (do not clobber existing entries):

```jsonc
"test:a11y": "playwright test --project=accessibility",
"test:a11y:headed": "playwright test --project=accessibility --headed",
"test:a11y:report": "playwright show-report"
```

### Step 5 · Validate — run the dummy scan

Run the feedback loop until green:

```bash
npm run test:a11y
```

1. If it **passes**, the infrastructure is proven. Done.
2. If it **fails on a real WCAG violation** on the chosen route, switch the example to a simpler
   public route (the dummy test must pass to prove the plumbing — fixing app violations is out of
   scope). Note the finding for the user.
3. If it fails on **setup** (missing browser, wrong port, dev server timeout, import error), fix the
   config/paths and re-run. Common causes: dev server not on 4200, `webServer.command` wrong,
   Chromium not installed, fixture import path incorrect.

Do not finish until `npm run test:a11y` exits green.

### Step 6 · Document

Add `assets/accessibility-README.md` to the repo as `docs/accessibility.md` (or
`playwright/README.md`). Adjust file paths/scripts to match what you created. Add a short
"Accessibility" note with the run command to the main `README.md` if one exists.

## Gotchas

- **Separate project, Chrome only.** axe evaluates rendered DOM/ARIA, not browser rendering quirks —
  scan once on Desktop Chrome. Do not fan a11y scans across webkit/firefox.
- **Wait for animations.** Scanning mid-transition produces false-positive color-contrast
  violations. `waitForAnimationsToFinish` (in the fixture) prevents this — call it before every scan.
- **Never touch Cypress.** If the repo uses Cypress, leave its config, specs, and dependencies
  untouched — add Playwright alongside it rather than migrating or editing anything Cypress owns.
- **Extend, don't recreate Playwright.** When a `playwright.config.*` already exists, merge the
  `accessibility` project into it and reuse any existing axe fixture — do not generate a second
  config or a duplicate fixture.
- **Filename routing.** A spec only lands in the accessibility project if `accessibility` is in its
  filename. This is `testMatch: /accessibility/`, not a folder.
- **git-ignore artifacts.** Ensure `test-results/` and `playwright-report/` are git-ignored.
- **WCAG tag set lives in one place.** Never inline `withTags(...)` in a spec — always go through
  `makeAxeBuilder`, so the standard stays consistent as scans are added later.

## Out of scope

- Writing real accessibility tests / per-page coverage (separate skill/task).
- Fixing accessibility violations found in the app.
- pa11y-ci, Lighthouse, or CI-pipeline wiring — Playwright + axe-core only, run locally.
