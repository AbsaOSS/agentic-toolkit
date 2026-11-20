import { defineConfig, devices } from '@playwright/test';

const port = Number(process.env.PORT ?? 5173);

export default defineConfig({
  testDir: './e2e',
  outputDir: 'test-results',
  reporter: [['list']],
  timeout: 30_000,
  use: { baseURL: `http://localhost:${port}`, trace: 'on-first-retry' },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
  webServer: { command: 'npm run dev', url: `http://localhost:${port}/curation/orders`, reuseExistingServer: !process.env.CI, timeout: 60_000 },
});
