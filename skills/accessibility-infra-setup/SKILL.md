---
name: accessibility-infra-setup
description: >
  Sets up automated accessibility (a11y) check infrastructure in an existing Angular application
  using Playwright + axe-core (@axe-core/playwright) to catch automatically detectable WCAG 2.2 AA violations.
  Detects the existing test setup, installs and wires Playwright with a dedicated `accessibility` project,
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
│   └── axe-helpers.ts                  # Shared axe fixture (WCAG 2.2 AA tags) + assertion + incomplete-warning helpers
├── print-a11y-warnings.js              # Prints tests carrying incomplete-result warnings (reusable module + CLI)
├── run-a11y-incomplete.js              # Runs the accessibility project, then prints incomplete-result warnings
└── a11y/
    └── example.accessibility.spec.ts   # ONE dummy scan of static, known-compliant HTML — passes
playwright.config.ts                    # `accessibility` project (Desktop Chrome, testMatch /\.accessibility\.spec\.ts$/)
docs/accessibility.md                   # How to run, where reports land (or playwright/README.md)
```

- `package.json` gains `@playwright/test` + `@axe-core/playwright` (devDependencies) and
  `test:a11y*` scripts, including `test:a11y:incomplete`.
- `npm run test:a11y` starts the dev server and runs the dummy scan on Desktop Chrome against static,
  known-compliant HTML (via `page.setContent`, not a real app route) — it **passes green**
  regardless of whether the app itself is WCAG-compliant yet. That green run is the definition of
  done; fixing app violations is a separate, out-of-scope concern.
- axe `violations` fail the test; axe `incomplete` results (checks axe couldn't confirm without
  human judgement) are non-blocking — reported as a warning annotation instead, never as a failure.

## Workflow

Copy this checklist and track progress:

```
- [ ] Step 1: Detect existing test infrastructure
- [ ] Step 2: Install dependencies
- [ ] Step 3: Scaffold config + fixture + example spec
- [ ] Step 4: Wire npm scripts
- [ ] Step 5: Validate (run the dummy scan, confirm the pipeline itself works)
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
  `{ name: 'accessibility', testMatch: /\.accessibility\.spec\.ts$/, use: { ...devices['Desktop Chrome'] } }`,
  add `testIgnore: /\.accessibility\.spec\.ts$/` to existing functional projects, and ensure `webServer`
  starts the Angular dev server. The pattern is anchored to the filename suffix, not a bare
  `/accessibility/` substring match, so a directory segment (e.g. a checkout under
  `accessibility-app/`) can't cause unrelated specs to be picked up or excluded. Keep the user's
  existing `testDir` and place a11y specs (and the axe fixture, if new) underneath it, with import
  paths adjusted to resolve from that location — do not introduce a separate top-level `playwright/`
  directory alongside it. Reuse any existing axe fixture instead of adding a second one. Merge the
  `reporter` array so the existing reporter(s) (e.g. `'html'` or `['html']`) are kept as-is and a
  `['json', { outputFile: 'playwright-report/summary.json' }]` entry is added alongside — never
  replace an existing reporter outright.
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

 `npx playwright install chromium` downloads the browser and needs network access. If Playwright is
 already installed, install `@axe-core/playwright` when it is missing, skip reinstalling
 `@playwright/test`, and still ensure the Chromium browser is present.

### Step 3 · Scaffold config, fixture, and example spec

Create these files (templates live in this skill's `assets/`):

1. `playwright.config.ts` (root) — from `assets/playwright.config.ts` (fresh setup only; otherwise
   merge as in Step 1). Adjust `baseURL`, `webServer.command`, and port if the app differs.
2. `playwright/fixtures/axe-helpers.ts` — copy verbatim from `assets/axe-helpers.ts`. This is the
   single source of the WCAG 2.2 AA tag set; every scan must build from `makeAxeBuilder`. It also
   exports `annotateIncomplete`, which every scan must call on `results.incomplete` so those
   findings are reported as a warning annotation instead of silently dropped or failing the build.
3. `playwright/a11y/example.accessibility.spec.ts` — from `assets/example.accessibility.spec.ts`.
   It scans static, known-compliant HTML via `page.setContent(...)` rather than a real app route, so
   the dummy proof stays green independent of whether the app itself is WCAG-compliant yet. Do not
   point it at a real route (e.g. `page.goto('/')`) — that reintroduces exactly the failure mode this
   avoids. Copy the template's HTML as-is; it only needs a landmark, a heading, and text.
4. `playwright/print-a11y-warnings.js` — copy verbatim from `assets/print-a11y-warnings.js`. Exports a
   `printWarnings(report)` helper (plus a `<report.json>` CLI mode) that prints every test carrying an
   incomplete-result warning, so they can be reviewed without opening the HTML report.
5. `playwright/run-a11y-incomplete.js` — copy verbatim from `assets/run-a11y-incomplete.js`. The
   cross-platform entry point behind `test:a11y:incomplete`: it spawns the accessibility project
   itself with `--reporter=json` piped to a temp file (never a fixed path, and never stdout — test
   attachments like screenshots/videos are base64-inlined and can blow past `spawnSync`'s stdout
   buffer), calls `printWarnings` on it, then exits with the underlying test run's own exit code.

The `accessibility` substring in the spec filename is what routes it to the accessibility project —
keep it.

### Step 4 · Wire npm scripts

Add to `package.json` `scripts` (do not clobber existing entries):

```jsonc
"test:a11y": "playwright test --project=accessibility",
"test:a11y:headed": "playwright test --project=accessibility --headed",
"test:a11y:report": "playwright show-report",
"test:a11y:incomplete": "node playwright/run-a11y-incomplete.js"
```

`test:a11y:incomplete` is self-contained — it runs its own accessibility-project pass (JSON reporter
only, written to a temp file) and prints any incomplete-result warnings, then exits with that run's
status. Run it standalone; it does not depend on `test:a11y` having run first.

### Step 5 · Validate — run the dummy scan

Run the feedback loop until green:

```bash
npm run test:a11y
```

1. If it **passes**, the infrastructure is proven. Done.
2. If it fails, it is a **setup** problem (missing browser, wrong port, dev server timeout, import
   error) — the dummy HTML is fixed and known-compliant, so a real WCAG violation should never be
   the cause. Fix the config/paths and re-run. Common causes: dev server not on 4200,
   `webServer.command` wrong, Chromium not installed, fixture import path incorrect.

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
- **Filename routing.** A spec only lands in the accessibility project if its filename ends in
  `.accessibility.spec.ts`. This is `testMatch: /\.accessibility\.spec\.ts$/`, anchored to the
  filename suffix rather than a bare `/accessibility/` substring — a directory named e.g.
  `accessibility-app/` must never cause unrelated specs to match.
- **git-ignore artifacts.** Ensure `test-results/` and `playwright-report/` are git-ignored.
- **WCAG tag set lives in one place.** Never inline `withTags(...)` in a spec — always go through
  `makeAxeBuilder`, so the standard stays consistent as scans are added later.
- **Incomplete ≠ violation.** Never assert `expectNoViolations(results.incomplete)` in a fresh setup
  — `incomplete` results need human judgement and must only be surfaced via `annotateIncomplete`
  (a non-blocking warning annotation), never used to fail the build.
- **Dummy scan uses static HTML, not a real route.** The example spec calls `page.setContent(...)`
  with known-compliant markup instead of `page.goto('/')`, so it proves the plumbing without
  depending on whether the app itself is WCAG-compliant. Do not repoint it at a real route — real
  per-page coverage belongs in dedicated specs added later, once the app's actual violations (if any)
  are a separate, tracked concern.

## Out of scope

- Writing real accessibility tests / per-page coverage (separate skill/task).
- Fixing accessibility violations found in the app.
- pa11y-ci, Lighthouse, or CI-pipeline wiring — Playwright + axe-core only, run locally.
