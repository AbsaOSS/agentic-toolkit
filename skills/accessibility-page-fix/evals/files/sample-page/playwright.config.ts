import { defineConfig, devices } from '@playwright/test';

const port = Number(process.env.PORT ?? 5173);

/**
 * Playwright configuration with a dedicated `accessibility` project: every spec whose filename ends in
 * `.accessibility.spec.ts` runs axe-core scans on Desktop Chrome.
 */
export default defineConfig({
  testDir: './playwright',
  outputDir: 'test-results',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: [['list'], ['json', { outputFile: 'playwright-report/summary.json' }]],
  timeout: 30_000,
  expect: { timeout: 5_000 },
  use: {
    baseURL: `http://localhost:${port}`,
    actionTimeout: 5_000,
    navigationTimeout: 5_000,
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },
  projects: [
    { name: 'chromium', testIgnore: /\.accessibility\.spec\.ts$/, use: { ...devices['Desktop Chrome'] } },
    { name: 'accessibility', testMatch: /\.accessibility\.spec\.ts$/, use: { ...devices['Desktop Chrome'] } },
  ],
  webServer: {
    command: 'npm run dev',
    url: `http://localhost:${port}`,
    reuseExistingServer: !process.env.CI,
    timeout: 60_000,
  },
});
