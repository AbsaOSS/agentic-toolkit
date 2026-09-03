# Accessibility Tests

Automated accessibility checks for this app, powered by
[Playwright](https://playwright.dev/) + [axe-core](https://github.com/dequelabs/axe-core)
(via [`@axe-core/playwright`](https://github.com/dequelabs/axe-core-npm/tree/develop/packages/playwright)).
Scans assert compliance with **WCAG 2.2 AA** (plus axe best-practice rules).

## Layout

```
playwright/
├── fixtures/
│   └── axe-helpers.ts                    # Shared axe fixture (WCAG 2.2 AA tag set) + assertion helpers
└── a11y/
    └── example.accessibility.spec.ts     # Dummy example scan of the home route
playwright.config.ts                      # `accessibility` project routes any *accessibility* spec here
```

Any spec file with `accessibility` in its name runs under the dedicated
`accessibility` Playwright project (Desktop Chrome only).

## Running

```bash
npm run test:a11y            # run all accessibility scans (auto-starts the dev server)
npm run test:a11y:headed     # same, with the browser visible
npm run test:a11y:report     # open the last HTML report
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

3. Navigate, wait for animations, scan with `makeAxeBuilder()`, assert with
   `expectNoViolations`. Use the example spec as a template.

Writing real accessibility tests is intentionally out of scope of the setup —
this directory only ships the infrastructure and one dummy example.
