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
        stillEmbedded: !!document.querySelector('web-fragment'),
        topURL: location.href,
      };
    }, { INNER, label });

  const out = { internal: [], external: null };
  out.internal.push(await probe('0:initial(a)'));

  // INTERNAL links — now UNtagged (no data-swap); opt-out filter should still intercept+swap
  const clickInternal = async (slug) => {
    await page.evaluate(({ INNER, slug }) => {
      const sr = eval(INNER);
      const link = [...sr.querySelectorAll('a')].find((a) => a.getAttribute('href') === `/astro/smooth/${slug}/`);
      if (link) link.click();
    }, { INNER, slug });
    await page.waitForFunction(
      `(${INNER}) && (${INNER}).querySelector('#content') && (${INNER}).querySelector('#content').getAttribute('data-site') === '${slug}'`,
      { timeout: 8000 },
    ).catch(() => {});
    await page.waitForTimeout(400);
    out.internal.push(await probe(`internal:${slug}`));
  };
  await clickInternal('b');
  await clickInternal('c');

  // OUT-OF-NAMESPACE link — opt-out filter should FALL THROUGH to a real top navigation
  const beforeURL = page.url();
  await page.evaluate((INNER) => {
    const sr = eval(INNER);
    const link = sr.querySelector('#ext-link');
    if (link) link.click();
  }, INNER);
  await page.waitForTimeout(1500); // allow a real navigation to occur
  out.external = {
    beforeURL,
    afterURL: page.url(),
    navigatedAway: page.url() !== beforeURL,
    webFragmentStillPresent: await page.evaluate(() => !!document.querySelector('web-fragment')),
  };

  console.log(JSON.stringify(out, null, 2));
  await browser.close();
})();
