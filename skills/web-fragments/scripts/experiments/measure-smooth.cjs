const { chromium } = require('@playwright/test');
const HOST = 'http://localhost:5402/';
const INNER = `(() => {
  const wf = document.querySelector('web-fragment');
  const wfh = wf && wf.shadowRoot && wf.shadowRoot.querySelector('web-fragment-host');
  return wfh && wfh.shadowRoot;
})()`;

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  const logs = [];
  page.on('console', (m) => logs.push(`[${m.type()}] ${m.text()}`.slice(0, 160)));
  page.on('pageerror', (e) => logs.push('pageerror: ' + e.message));
  await page.goto(HOST, { waitUntil: 'networkidle' });
  await page.waitForFunction(`(${INNER}) && (${INNER}).querySelector('#content')`, { timeout: 15000 }).catch(() => {});

  const probe = (label) =>
    page.evaluate(({ INNER, label }) => {
      const sr = eval(INNER);
      const content = sr && sr.querySelector('#content');
      const siteName = sr && sr.querySelector('#site-name');
      return {
        label,
        contentSite: content ? content.getAttribute('data-site') : '(none)',
        siteNameColor: siteName ? getComputedStyle(siteName).color : '(none)',
        stylesInShadow: sr ? sr.querySelectorAll('style').length : -1,
        linksInShadow: sr ? sr.querySelectorAll('link').length : -1,
        stillEmbedded: !!document.querySelector('web-fragment'),
        topURL: location.href,
      };
    }, { INNER, label });

  const steps = [await probe('0:initial(a)')];

  const visit = async (slug) => {
    await page.evaluate(({ INNER, slug }) => {
      const sr = eval(INNER);
      const link = [...sr.querySelectorAll('a[data-swap]')].find((a) => a.getAttribute('href') === `/astro/smooth/${slug}/`);
      if (link) link.click();
    }, { INNER, slug });
    await page.waitForFunction(
      `(${INNER}) && (${INNER}).querySelector('#content') && (${INNER}).querySelector('#content').getAttribute('data-site') === '${slug}'`,
      { timeout: 8000 },
    ).catch(() => {});
    await page.waitForTimeout(500);
    steps.push(await probe(`visit:${slug}`));
  };
  for (const n of ['b', 'c', 'a', 'b']) await visit(n);

  console.log(JSON.stringify(steps, null, 2));
  console.log('--- console (last 6) ---\n' + logs.slice(-6).join('\n'));
  await browser.close();
})();
