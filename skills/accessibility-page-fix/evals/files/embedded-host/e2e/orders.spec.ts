import { expect, test } from '@playwright/test';

test('standalone orders page lists the orders', async ({ page }) => {
  await page.goto('/curation/orders');
  await expect(page.locator('.order-row')).toHaveCount(4);
});

test('host page embeds the curation app', async ({ page }) => {
  await page.goto('/host/curation/orders');
  await expect(page.locator('curation-app .order-row')).toHaveCount(4);
});
