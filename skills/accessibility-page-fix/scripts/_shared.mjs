// Shared helpers for the accessibility-page-fix scripts. Not meant to be run directly.
import { createRequire } from 'node:module';
import path from 'node:path';

/** Loads Playwright from the app being tested (the current directory), not from the skill folder. */
export function loadPlaywright() {
  const require = createRequire(path.join(process.cwd(), 'noop.js'));
  for (const name of ['@playwright/test', 'playwright']) {
    try {
      return require(name);
    } catch {
      /* try the next one */
    }
  }
  console.error('Playwright not found. Run this from the app directory after installing @playwright/test.');
  process.exit(2);
}

/** Minimal `--flag value` parser: positional args first, then flags. */
export function parseArgs(argv, defaults = {}) {
  const positional = [];
  const flags = { ...defaults };
  for (let i = 0; i < argv.length; i++) {
    if (argv[i].startsWith('--')) {
      const key = argv[i].slice(2);
      const next = argv[i + 1];
      if (next === undefined || next.startsWith('--')) flags[key] = true;
      else {
        flags[key] = next;
        i++;
      }
    } else positional.push(argv[i]);
  }
  return { positional, flags };
}

/** Opens `url` in a fresh browser context; `--storage` loads a saved Playwright storageState (for logged-in pages). */
export async function openPage(url, flags, viewport = { width: 1440, height: 900 }) {
  const { chromium } = loadPlaywright();
  const browser = await chromium.launch();
  const context = await browser.newContext({ viewport, ...(flags.storage ? { storageState: flags.storage } : {}) });
  const page = await context.newPage();
  await page.goto(url);
  if (flags.wait) {
    // Wait until the element exists, not until it is visible: at some sizes (320 px, 200% text) the page may hide
    // or push it off-screen, which is exactly what the checks are looking for.
    await page
      .locator(flags.wait)
      .first()
      .waitFor({ state: 'attached', timeout: Number(flags['wait-timeout'] ?? 20000) })
      .catch(() => console.warn(`warning: "${flags.wait}" did not appear; checking the page as it is`));
  }
  await page.waitForLoadState('networkidle').catch(() => {});
  await page.waitForTimeout(Number(flags.settle ?? 800));
  // `--click "a;;b"` clicks each selector in turn, to open a menu or dialog before the checks run
  for (const selector of flags.click ? String(flags.click).split(';;') : []) {
    await page
      .locator(selector.trim())
      .first()
      .click({ timeout: 10000 })
      .catch(() => console.warn(`warning: could not click "${selector.trim()}"; checking the page as it is`));
    await page.waitForTimeout(Number(flags.settle ?? 800));
  }
  return { browser, context, page };
}
