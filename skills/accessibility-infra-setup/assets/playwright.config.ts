import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright configuration with a dedicated `accessibility` project.
 *
 * Any spec whose filename contains `accessibility` runs axe-core scans on
 * Desktop Chrome only — axe evaluates rendered DOM/ARIA state, so cross-browser
 * variation adds no value. Functional specs (if any) run under `chromium`.
 *
 * See https://playwright.dev/docs/test-configuration
 */
export default defineConfig({
  testDir: './playwright',
  outputDir: 'test-results',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: [['html'], ['json', { outputFile: 'playwright-report/summary.json' }]],
  timeout: 30_000,
  expect: { timeout: 5_000 },
  use: {
    baseURL: 'http://localhost:4200',
    actionTimeout: 5_000,
    navigationTimeout: 5_000,
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure'
  },
  projects: [
    {
      name: 'chromium',
      testIgnore: /accessibility/,
      use: { ...devices['Desktop Chrome'] }
    },
    {
      name: 'accessibility',
      testMatch: /accessibility/,
      use: { ...devices['Desktop Chrome'] }
    }
  ],
  /* Start the Angular dev server before running tests. */
  webServer: {
    command: 'npm run start',
    url: 'http://localhost:4200',
    /* Reuse a running dev server locally; CI always starts fresh. */
    reuseExistingServer: !process.env.CI,
    /* Angular builds can be slow — allow up to 2 minutes. */
    timeout: 120_000
  }
});
