---
name: accessibility-infra-setup
description: >
  Sets up automated accessibility (a11y) check infrastructure in an existing Angular application
  using Playwright + axe-core (@axe-core/playwright) to catch automatically detectable WCAG 2.2 AA violations.
  Detects the existing test setup (including package manager), installs and wires Playwright with a
  dedicated `accessibility` project, scaffolds a shared axe fixture, adds one dummy example scan,
  wires package.json scripts, documents how to run the checks, and validates that the sample passes.
  Activates on requests like: "set up
  accessibility checks", "add a11y testing infrastructure", "add axe-core to this Angular app",
  "set up WCAG testing", "add accessibility scans with Playwright", "bootstrap a11y infra".
  Scope is infrastructure only plus ONE dummy example test — authoring real accessibility tests is
  a separate concern and out of scope.
license: Apache-2.0
compatibility: >
  Requires an existing Angular application with a runnable dev server (`start` script on port 4200,
  run via npm, Yarn, or pnpm) and Node.js 22+. Installs Playwright browsers, which needs network
  access on first run.
---

# accessibility-infra-setup

Bootstraps Playwright + axe-core accessibility infrastructure in an existing Angular app. Follows the
[AbsaOSS/cps-shared-ui](https://github.com/AbsaOSS/cps-shared-ui) pattern, generalized for a plain
application (not a component library).

**Scope:** infrastructure + exactly one dummy example scan. Do **not** author real accessibility
tests here — that is a separate follow-up task.

## Expected outcome

After this skill runs, the repository contains (fresh setup; see Step 3 for where these land instead
when merging into an existing `testDir`):

```
playwright/
├── fixtures/
│   └── axe-helpers.ts                  # Shared axe fixture (WCAG 2.2 AA tags) + assertion + incomplete-warning helpers
├── print-a11y-warnings.cjs             # Prints tests carrying incomplete-result warnings (reusable module + CLI)
├── run-a11y-incomplete.cjs              # Runs the accessibility project, then prints incomplete-result warnings
└── a11y/
    └── example.accessibility.spec.ts   # ONE dummy scan of static, known-compliant HTML — passes
playwright.config.ts                    # `accessibility` project (Desktop Chrome, testMatch /\.accessibility\.spec\.ts$/)
docs/accessibility.md                   # How to run, where reports land (or playwright/README.md)
```

- `package.json` gains `@playwright/test` + `@axe-core/playwright` (devDependencies) and
  `test:a11y*` scripts, including `test:a11y:incomplete`.
- Running `test:a11y` through the repo's detected package manager (see Step 1) starts the dev server
  and runs the dummy scan on Desktop Chrome against static, known-compliant HTML (via
  `page.setContent`, not a real app route) — it **passes green** regardless of whether the app
  itself is WCAG-compliant yet. That green run is the definition of done; fixing app violations is a
  separate, out-of-scope concern.
- axe `violations` fail the test; axe `incomplete` results (checks axe couldn't confirm without
  human judgement) are non-blocking — reported as a warning annotation instead, never as a failure.

## Workflow

Copy this checklist and track progress:

```
- [ ] Step 1: Detect existing test infrastructure (incl. package manager)
- [ ] Step 2: Install dependencies
- [ ] Step 3: Scaffold config + fixture + example spec
- [ ] Step 4: Wire package.json scripts
- [ ] Step 5: Validate (run the dummy scan, confirm the pipeline itself works)
- [ ] Step 6: Document
```

### Step 1 · Detect existing test infrastructure

Inspect the repo before writing anything — the goal is to **extend, not clobber**.

1. Read `package.json`: note the dev-server script (usually `start` → `ng serve`, port 4200), the
   package manager (from `package-lock.json` / `yarn.lock` / `pnpm-lock.yaml`, or a `packageManager`
   field — distinguish Yarn Classic from Yarn Berry/PnP via `.yarnrc.yml`'s `nodeLinker`), and any
   existing `@playwright/test`, `@axe-core/playwright`, Cypress, or Karma entries.
2. Check for an existing `playwright.config.*` and for Cypress (`cypress.config.*`, a `cypress/`
   folder, or a `cypress` devDependency).

**Carry the detected package manager through every later step.** All install and run commands below
are shown for npm, Yarn (Classic and Berry/PnP), and pnpm — use the one matching this repo, not npm
by default. This matters most under Yarn PnP: it doesn't hoist packages into `node_modules/.bin`, so
a plain `npm run ...` or bare `npx playwright ...` there fails to resolve the Playwright binary even
though setup is otherwise correct.

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

Confirm the dev-server command and port with the user only if they differ from `start` / `4200`;
otherwise proceed.

### Step 2 · Install dependencies

Use the package manager detected in Step 1 — not npm by default:

```bash
# npm
npm install -D @playwright/test @axe-core/playwright
npx playwright install chromium

# Yarn (Classic or Berry/PnP)
yarn add -D @playwright/test @axe-core/playwright
yarn playwright install chromium

# pnpm
pnpm add -D @playwright/test @axe-core/playwright
pnpm exec playwright install chromium
```

Under Yarn PnP there is no `node_modules/.bin`, so a bare `npx playwright ...` cannot resolve the
binary — always go through `yarn playwright ...` (or `yarn dlx playwright ...`) instead. The browser
download step needs network access regardless of package manager. If Playwright is already
installed, install `@axe-core/playwright` when it is missing, skip reinstalling `@playwright/test`,
and still ensure the Chromium browser is present.

### Step 3 · Scaffold config, fixture, and example spec

Create these files (templates live in this skill's `assets/`). The root is `playwright/` on a fresh
setup; when merging into an existing config, use the existing `testDir` as the root instead and keep
the same relative layout below it — otherwise Playwright's `testDir` never discovers the new files.

1. `playwright.config.ts` (root) — from `assets/playwright.config.ts` (fresh setup only; otherwise
   merge as in Step 1). Adjust `baseURL`, `webServer.command`, and port if the app differs, and set
   `webServer.command` to launch the dev server through the package manager detected in Step 1
   (`npm run start`, `yarn start`, or `pnpm start`) rather than defaulting to npm.
2. `<root>/fixtures/axe-helpers.ts` — copy verbatim from `assets/axe-helpers.ts`. This is the
   single source of the WCAG 2.2 AA tag set; every scan must build from `makeAxeBuilder`. It also
   exports `annotateIncomplete`, which every scan must call on `results.incomplete` so those
   findings are reported as a warning annotation instead of silently dropped or failing the build.
3. `<root>/a11y/example.accessibility.spec.ts` — from `assets/example.accessibility.spec.ts`.
   It scans static, known-compliant HTML via `page.setContent(...)` rather than a real app route, so
   the dummy proof stays green independent of whether the app itself is WCAG-compliant yet. Do not
   point it at a real route (e.g. `page.goto('/')`) — that reintroduces exactly the failure mode this
   avoids. Copy the template's HTML as-is; it only needs a landmark, a heading, and text.
4. `<root>/print-a11y-warnings.cjs` — copy verbatim from `assets/print-a11y-warnings.cjs`. Exports a
   `printWarnings(report)` helper (plus a `<report.json>` CLI mode) that prints every test carrying an
   incomplete-result warning, so they can be reviewed without opening the HTML report.
5. `<root>/run-a11y-incomplete.cjs` — copy verbatim from `assets/run-a11y-incomplete.cjs`. The
   cross-platform entry point behind `test:a11y:incomplete`: it spawns the accessibility project
   itself with `--reporter=json` piped to a temp file (never a fixed path, and never stdout — test
   attachments like screenshots/videos are base64-inlined and can blow past `spawnSync`'s stdout
   buffer), calls `printWarnings` on it, then exits with the underlying test run's own exit code.

   Both scripts use the `.cjs` extension (not `.js`) so they load as CommonJS even in an Angular app
   with `"type": "module"` in `package.json` — plain `.js` there is parsed as ESM and `require` throws
   `ReferenceError: require is not defined`. Keep the `.cjs` extension regardless of the host
   package's `type` field.

`<root>` is `playwright/` on a fresh setup, or the existing `testDir` when merging — e.g. with
`testDir: './e2e'` the fixture lands at `e2e/fixtures/axe-helpers.ts` and the dummy spec at
`e2e/a11y/example.accessibility.spec.ts`. Adjust import paths (e.g. `../fixtures/axe-helpers`) to
match wherever `<root>` ends up; the relative layout between the files stays the same either way.

The `.accessibility.spec.ts` filename suffix is what routes a spec to the accessibility project —
keep it.

### Step 4 · Wire package.json scripts

Add to `package.json` `scripts` (do not clobber existing entries). These entries are invoked via
whichever package manager Step 1 detected (`npm run test:a11y`, `yarn test:a11y`, or
`pnpm test:a11y`), so the script bodies themselves don't need to vary:

```jsonc
"test:a11y": "playwright test --project=accessibility",
"test:a11y:headed": "playwright test --project=accessibility --headed",
"test:a11y:report": "playwright show-report",
"test:a11y:incomplete": "node playwright/run-a11y-incomplete.cjs"
```

Substitute `playwright/` in `test:a11y:incomplete` with the actual `<root>` from Step 3 — e.g. for an
existing `testDir: './e2e'` the script must read `"node e2e/run-a11y-incomplete.cjs"`. The hardcoded
`playwright/` only applies on a fresh setup; using it verbatim when merging into an existing `testDir`
points at a path that was never created, and the script fails with `MODULE_NOT_FOUND`.

`test:a11y:incomplete` is self-contained — it runs its own accessibility-project pass (JSON reporter
only, written to a temp file) and prints any incomplete-result warnings, then exits with that run's
status. Run it standalone; it does not depend on `test:a11y` having run first.

### Step 5 · Validate — run the dummy scan

Run the feedback loop until green, invoking the script through the package manager detected in
Step 1 (never assume npm):

```bash
npm run test:a11y    # npm
yarn test:a11y        # Yarn (Classic or Berry/PnP)
pnpm test:a11y        # pnpm
```

1. If it **passes**, the infrastructure is proven. Done.
2. If it fails, it is a **setup** problem (missing browser, wrong port, dev server timeout, import
   error, or — under Yarn PnP — a package-manager mismatch where the wrong command was used to
   invoke the script) — the dummy HTML is fixed and known-compliant, so a real WCAG violation should
   never be the cause. Fix the config/paths and re-run. Common causes: dev server not on 4200,
   `webServer.command` wrong, Chromium not installed, fixture import path incorrect, script run via
   the wrong package manager.

Do not finish until `test:a11y` exits green through the detected package manager.

### Step 6 · Document

Add `assets/accessibility-README.md` to the repo as `docs/accessibility.md` (or
`playwright/README.md`). Adjust file paths/scripts to match what you created, and rewrite the
`npm run ...` commands in it to match the package manager detected in Step 1 (`yarn ...` / `pnpm ...`)
so the docs don't point users at a command that can't resolve the binary. Add a short
"Accessibility" note with the run command to the main `README.md` if one exists.

## Gotchas

- **Separate project, Chrome only.** axe evaluates rendered DOM/ARIA, not browser rendering quirks —
  scan once on Desktop Chrome. Do not fan a11y scans across webkit/firefox.
- **Wait for animations.** Scanning mid-transition produces false-positive color-contrast
  violations. `waitForAnimationsToFinish` (in the fixture) prevents this — call it before every scan.
- **Never touch Cypress.** If the repo uses Cypress, leave its config, specs, and dependencies
  untouched — add Playwright alongside it rather than migrating or editing anything Cypress owns.
- **Never default to npm.** Step 1 detects the repo's package manager (npm, Yarn Classic, Yarn
  Berry/PnP, or pnpm) — use it consistently for installs, `webServer.command`, the validation run,
  and the docs. Yarn PnP in particular has no `node_modules/.bin`, so a bare `npm run ...` or
  `npx playwright ...` there fails to resolve the binary even when the rest of the setup is correct.
- **Extend, don't recreate Playwright.** When a `playwright.config.*` already exists, merge the
  `accessibility` project into it and reuse any existing axe fixture — do not generate a second
  config or a duplicate fixture. Scaffold the fixture and dummy spec under the existing `testDir`,
  not a hardcoded `playwright/` — otherwise Playwright's own `testDir` setting never discovers them
  and validation fails with "no tests found".
- **Filename routing.** A spec only lands in the accessibility project if its filename ends in
  `.accessibility.spec.ts`. This is `testMatch: /\.accessibility\.spec\.ts$/`, anchored to the
  filename suffix rather than a bare `/accessibility/` substring — a directory named e.g.
  `accessibility-app/` must never cause unrelated specs to match.
- **git-ignore artifacts.** Ensure `test-results/` and `playwright-report/` are git-ignored.
- **Helper scripts must stay `.cjs`.** `print-a11y-warnings.cjs` and `run-a11y-incomplete.cjs` use
  CommonJS `require`/`module.exports`. If the host `package.json` has `"type": "module"`, a plain
  `.js` copy is loaded as ESM and fails immediately with `ReferenceError: require is not defined`.
  Copy them with the `.cjs` extension regardless of the app's `type` field, and keep the `require`
  between them pointed at `./print-a11y-warnings.cjs`.
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
