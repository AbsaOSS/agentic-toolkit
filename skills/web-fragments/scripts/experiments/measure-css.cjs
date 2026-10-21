const { chromium } = require('@playwright/test');

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  const errors = [];
  page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()); });
  page.on('pageerror', (e) => errors.push('pageerror: ' + e.message));

  await page.goto('http://localhost:5300/css-vars-isolation/', { waitUntil: 'networkidle' });

  // Wait for the nested fragment shadow content to mount
  await page.waitForFunction(() => {
    const wf = document.querySelector('web-fragment');
    const wfh = wf && wf.shadowRoot && wf.shadowRoot.querySelector('web-fragment-host');
    const sr = wfh && wfh.shadowRoot;
    return sr && sr.querySelector('#frag-brand');
  }, { timeout: 15000 }).catch(() => {});

  const result = await page.evaluate(() => {
    const color = (el) => (el ? getComputedStyle(el).color : '(no element)');
    const font = (el) => (el ? getComputedStyle(el).fontFamily : '(no element)');
    const varOf = (el, name) => (el ? getComputedStyle(el).getPropertyValue(name).trim() : '(no element)');
    const get = (id) => document.getElementById(id);
    const wf = document.querySelector('web-fragment');
    const wfh = wf && wf.shadowRoot && wf.shadowRoot.querySelector('web-fragment-host');
    const sr = wfh && wfh.shadowRoot;
    const fget = (id) => (sr ? sr.querySelector('#' + id) : null);

    let shadowDump = null;
    if (sr && !fget('frag-brand')) {
      shadowDump = sr.innerHTML.slice(0, 600);
    }

    return {
      shadowRootPresent: !!sr,
      shadowDump,
      host: {
        brand_expectRed: color(get('host-brand')),
        layered_expectGreen: color(get('host-layered')),
        accentProbe_expectBlack: color(get('host-accent-probe')),
        font: font(get('host-brand')),
      },
      fragment: sr
        ? {
            brand_red_or_purple: color(fget('frag-brand')),
            brandVarValue: varOf(fget('frag-brand'), '--brand'),
            accent_expectOrange: color(fget('frag-accent')),
            hostAccentVarValue: varOf(fget('frag-accent'), '--host-accent'),
            layered_expectGreen: color(fget('frag-layered')),
            font_Georgia_means_leak: font(fget('frag-font')),
            leak_expectBlack_notMagenta: color(fget('frag-leak')),
          }
        : null,
    };
  });

  console.log(JSON.stringify({ result, consoleErrors: errors }, null, 2));
  await page.screenshot({ path: 'C:/Users/oto/AppData/Local/Temp/claude/C--Projects-agentic-toolkit/f9921fa9-5fde-47de-8514-261887da6a8d/scratchpad/css-shot.png', fullPage: true });
  await browser.close();
})();
