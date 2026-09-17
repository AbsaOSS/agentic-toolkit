# Accessibility Tests

Automated accessibility checks for this app, powered by
[Playwright](https://playwright.dev/) + [axe-core](https://github.com/dequelabs/axe-core)
(via [`@axe-core/playwright`](https://github.com/dequelabs/axe-core-npm/tree/develop/packages/playwright)).
Scans assert compliance with **WCAG 2.2 AA** (plus axe best-practice rules); manual testing is still required for full compliance.

axe-core's `violations` fail the test; `incomplete` results (checks axe couldn't confirm without
human judgement, e.g. combobox `aria-controls` patterns) are non-blocking and instead surfaced as a
`warning` annotation on the test, visible in the HTML report and the attached scan JSON. Run
`npm run test:a11y:incomplete` after a scan to print every test carrying such a warning without
opening the HTML report.

## Layout

```
playwright/
├── fixtures/
│   └── axe-helpers.ts                    # Shared axe fixture (WCAG 2.2 AA tag set) + assertion helpers
├── print-a11y-warnings.js                # Prints tests with incomplete-result warnings (reusable module + CLI)
├── run-a11y-incomplete.js                 # Runs the accessibility project, then prints incomplete-result warnings
└── a11y/
    └── example.accessibility.spec.ts     # Dummy example scan of static, known-compliant HTML
playwright.config.ts                      # `accessibility` project routes any *accessibility* spec here
```

Any spec file with `accessibility` in its name runs under the dedicated
`accessibility` Playwright project (Desktop Chrome only).

## Running

```bash
npm run test:a11y            # run all accessibility scans (auto-starts the dev server)
npm run test:a11y:headed     # same, with the browser visible
npm run test:a11y:report     # open the last HTML report
npm run test:a11y:incomplete # re-run the accessibility project and print incomplete-result warnings
```

Playwright auto-starts `npm run start` (the Angular dev server) and waits for
`http://localhost:4200`. If a dev server is already running locally, it is reused.

## Reports and artifacts

- HTML report → `playwright-report/` (open with `npm run test:a11y:report`)
- Full axe results JSON attached to each test → visible in the HTML report
- Screenshots / videos / traces on failure → `test-results/`

Both directories are git-ignored.

## Adding a scan

1. Create a spec whose filename contains `accessibility`, e.g.
   `playwright/a11y/checkout.accessibility.spec.ts`.
2. Import the shared fixture:

   ```ts
   import { test, expectNoViolations, waitForAnimationsToFinish } from '../fixtures/axe-helpers';
   ```

3. Navigate, wait for animations, scan with `makeAxeBuilder()`, call
   `annotateIncomplete(results.incomplete, testInfo)` to report (not fail on) incomplete results,
   then assert with `expectNoViolations(results.violations)`. Use the example spec as a template.

Writing real accessibility tests is intentionally out of scope of the setup —
this directory only ships the infrastructure and one dummy example.
