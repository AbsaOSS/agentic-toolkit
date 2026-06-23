const { chromium } = require('@playwright/test');

const HOST = 'http://localhost:5402/';

// Traverse host light DOM -> web-fragment shadow -> web-fragment-host shadow -> fragment content
const FIND = `(() => {
  const wf = document.querySelector('web-fragment');
  const wfh = wf && wf.shadowRoot && wf.shadowRoot.querySelector('web-fragment-host');
  const sr = wfh && wfh.shadowRoot;
  return sr;
})()`;

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  const logs = [];
  page.on('console', (m) => logs.push(`[${m.type()}] ${m.text()}`.slice(0, 200)));
  page.on('pageerror', (e) => logs.push('pageerror: ' + e.message));
  const requests = [];
  page.on('request', (r) => requests.push(r.method() + ' ' + r.url()));

  await page.goto(HOST, { waitUntil: 'networkidle' });

  // wait for fragment astro content
  await page.waitForFunction(`(${FIND}) && (${FIND}).querySelector('#page-marker')`, { timeout: 15000 }).catch(() => {});

  const snap = async (label) =>
    page.evaluate(({ FIND, label }) => {
      const sr = eval(FIND);
      const marker = sr && sr.querySelector('#page-marker');
      const count = sr && sr.querySelector('#count');
      return {
        label,
        url: location.href,
        page: marker ? marker.getAttribute('data-page') : '(none)',
        markerText: marker ? marker.textContent.trim() : '(none)',
        navCount: count ? count.textContent : '(none)',
        reloadFlagPresent: !!window.__wfNoReload,
      };
    }, { FIND, label });

  const before = await snap('before-click');

  // plant a window flag that a full page reload would wipe out
  await page.evaluate(() => { window.__wfNoReload = true; });

  // click the "Page 2" link inside the fragment (Playwright pierces open shadow roots)
  let clickMethod = 'locator';
  let clicked = false;
  try {
    await page.getByRole('link', { name: 'Page 2' }).click({ timeout: 4000 });
    clicked = true;
  } catch (e) {
    clickMethod = 'evaluate-dispatch';
    clicked = await page.evaluate((FIND) => {
      const sr = eval(FIND);
      const link = [...sr.querySelectorAll('a')].find((a) => /page 2/i.test(a.textContent));
      if (!link) return false;
      link.click();
      return true;
    }, FIND);
  }

  // wait for the fragment content to become page2 (SPA) — or detect a reload
  await page.waitForFunction(`(${FIND}) && (${FIND}).querySelector('#page-marker') && (${FIND}).querySelector('#page-marker').getAttribute('data-page') === 'page2'`, { timeout: 8000 }).catch(() => {});
  await page.waitForTimeout(500);

  const after = await snap('after-click');

  const verdict =
    after.page === 'page2'
      ? after.reloadFlagPresent
        ? 'SPA navigation (client router swapped content, NO full reload)'
        : 'navigated to page2 but via FULL reload (window flag was wiped)'
      : 'navigation did NOT reach page2 inside the fragment';

  console.log(JSON.stringify({ clicked, clickMethod, before, after, verdict }, null, 2));
  console.log('--- fragment-scoped requests after click ---');
  console.log(requests.filter((r) => r.includes('/astro/')).slice(-8).join('\n'));
  console.log('--- console (last 12) ---');
  console.log(logs.slice(-12).join('\n'));
  await page.screenshot({ path: 'C:/Users/oto/AppData/Local/Temp/claude/C--Projects-agentic-toolkit/f9921fa9-5fde-47de-8514-261887da6a8d/scratchpad/astro-after.png', fullPage: true });
  await browser.close();
})();
