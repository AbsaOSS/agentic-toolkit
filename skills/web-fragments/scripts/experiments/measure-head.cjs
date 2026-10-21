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
  await page.waitForFunction(`(${INNER}) && (${INNER}).querySelector('#page-marker')`, { timeout: 15000 }).catch(() => {});

  const probe = (label) =>
    page.evaluate(({ INNER, label }) => {
      const sr = eval(INNER);
      const all = (root, sel) => [...root.querySelectorAll(sel)];
      // probe styles/links ANYWHERE in the inner shadow tree
      const inAnywhere = all(sr, 'style.wf-probe-inline').map((s) => s.getAttribute('data-site'));
      const linkAnywhere = all(sr, 'link.wf-probe-link').map((l) => l.getAttribute('data-site'));
      // adopted stylesheets on the inner shadow root (constructable)
      const adopted = (sr.adoptedStyleSheets || []).map((ss) => {
        try { return [...ss.cssRules].map((r) => r.cssText).join(' ').slice(0, 80); } catch { return '(opaque)'; }
      });
      // also check the outer light-DOM document head (in case styles hoist to the top doc)
      const outerProbe = all(document.head, 'style.wf-probe-inline, link.wf-probe-link').map(
        (e) => e.getAttribute('data-site'),
      );
      const cur = sr.querySelector('#inline-mark') || sr.querySelector('#page-marker');
      const col = (id) => {
        const el = sr.querySelector('#' + id);
        return el ? getComputedStyle(el).color : '(no el)';
      };
      return {
        label,
        site: cur ? cur.getAttribute('data-site') || cur.getAttribute('data-page') : '(none)',
        inlineProbeSites_inShadow: inAnywhere,
        linkProbeSites_inShadow: linkAnywhere,
        totalStyleEls_inShadow: all(sr, 'style').length,
        totalLinkEls_inShadow: all(sr, 'link').length,
        adoptedSheetsCount: (sr.adoptedStyleSheets || []).length,
        adoptedProbeRules: adopted.filter((t) => /inline-mark|link-mark/.test(t)),
        outerHeadProbeSites: outerProbe,
        inlineMarkColor: col('inline-mark'),
        linkMarkColor: col('link-mark'),
        // pollution check on shared #site-name: only the CURRENT site's distinct rule should apply
        siteName: (() => {
          const el = sr.querySelector('#site-name');
          if (!el) return '(no el)';
          const c = getComputedStyle(el);
          return { bg: c.backgroundColor, borderBottom: c.borderBottomWidth, fontStyle: c.fontStyle };
        })(),
      };
    }, { INNER, label });

  const steps = [await probe('0:home')];
  const visit = async (slug) => {
    await page.evaluate(({ INNER, slug }) => {
      const sr = eval(INNER);
      const link = [...sr.querySelectorAll('a')].find((a) => a.getAttribute('href') === `/astro/${slug}/`);
      if (link) link.click();
    }, { INNER, slug });
    await page.waitForFunction(
      `(${INNER}) && (${INNER}).querySelector('#inline-mark') && (${INNER}).querySelector('#inline-mark').getAttribute('data-site') === '${slug}'`,
      { timeout: 8000 },
    ).catch(() => {});
    await page.waitForTimeout(500);
    steps.push(await probe(`visit:${slug}`));
  };
  for (const n of ['a', 'b', 'c', 'a', 'b']) await visit(n);

  console.log(JSON.stringify(steps, null, 2));
  await browser.close();
})();
