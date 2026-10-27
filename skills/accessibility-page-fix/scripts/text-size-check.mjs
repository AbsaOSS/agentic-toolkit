#!/usr/bin/env node
// Checks a page at 200% text size, at 320 CSS px wide (reflow), and with WCAG text-spacing overrides.
// Reports horizontal scrolling (of the page or of a scroll container inside it), clipped text, placeholders that
// don't fit, controls pushed off-screen or covering each other, and text that does not grow when the root font size doubles. Saves a screenshot of each setting so you can look at them.
//
// Usage (run from the app directory):
//   node <skill>/scripts/text-size-check.mjs <url> [--wait <selector>] [--storage <state.json>] [--out <dir>]
//        [--click "<selector>;;<selector>"] [--scope <selector>]
// --click opens a menu or dialog first (one click per selector); --scope limits the findings to one part of the
// page, e.g. --scope '[role="dialog"]'.
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { openPage, parseArgs } from './_shared.mjs';

// Screenshots go to the temp folder by default, not into the app's repository
const { positional, flags } = parseArgs(process.argv.slice(2), { out: path.join(os.tmpdir(), 'a11y-text-size') });
if (!positional[0]) {
  console.error('Usage: text-size-check.mjs <url> [--wait <selector>] [--storage <state.json>] [--out <dir>] [--click <selectors>] [--scope <selector>]');
  process.exit(2);
}
fs.mkdirSync(flags.out, { recursive: true });

const SETTINGS = [
  { name: 'baseline (100%)', viewport: { width: 1440, height: 900 }, css: '' },
  { name: '200% text', viewport: { width: 1440, height: 900 }, css: 'html { font-size: 200% !important; }' },
  { name: '320px wide', viewport: { width: 320, height: 640 }, css: '' },
  {
    name: 'text spacing',
    viewport: { width: 1440, height: 900 },
    css: '* { line-height: 1.5 !important; letter-spacing: 0.12em !important; word-spacing: 0.16em !important; } p { margin-bottom: 2em !important; }',
  },
];

const measure = scope =>
  document.fonts.ready.then(() => {
    const issues = [];
    const doc = document.documentElement;
    if (doc.scrollWidth > doc.clientWidth + 1) issues.push(`horizontal scroll: page is ${doc.scrollWidth}px wide in a ${doc.clientWidth}px viewport`);
    for (const root of document.querySelectorAll(scope)) {
      const box = root.getBoundingClientRect();
      if (root !== document.body && (box.left < -1 || box.right > innerWidth + 1)) issues.push(`wider than the screen: ${scope} is ${Math.round(box.width)}px wide (x ${Math.round(box.left)}..${Math.round(box.right)})`);
    }
    const label = el => `${el.tagName.toLowerCase()}${el.className ? '.' + String(el.className).trim().split(/\s+/)[0] : ''} "${(el.getAttribute('aria-label') || el.textContent || el.getAttribute('placeholder') || '').trim().replace(/\s+/g, ' ').slice(0, 28)}"`;
    const canvas = document.createElement('canvas').getContext('2d');
    for (const el of document.querySelectorAll(`${scope} *`)) {
      const cs = getComputedStyle(el);
      const r = el.getBoundingClientRect();
      // Boxes of 2px or less are the intentional "screen-reader only" pattern, not clipped content
      if (r.width <= 2 || r.height <= 2 || cs.visibility === 'hidden' || el.closest('[hidden],[inert]')) continue;
      const hasText = [...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim());
      const clips = ['hidden', 'clip'].includes(cs.overflowX) || ['hidden', 'clip'].includes(cs.overflowY);
      if (hasText && clips && cs.textOverflow !== 'ellipsis' && (el.scrollWidth > el.clientWidth + 1 || el.scrollHeight > el.clientHeight + 1)) issues.push(`clipped text: ${label(el)} (content ${el.scrollWidth}x${el.scrollHeight}, box ${el.clientWidth}x${el.clientHeight})`);
      if (hasText && cs.textOverflow === 'ellipsis' && el.scrollWidth > el.clientWidth + 1) issues.push(`truncated with "…": ${label(el)} (check the full text is still available)`);
      if (el.matches('input,textarea') && el.placeholder && !el.value) {
        canvas.font = `${cs.fontStyle} ${cs.fontWeight} ${cs.fontSize} ${cs.fontFamily}`;
        const room = el.clientWidth - parseFloat(cs.paddingLeft) - parseFloat(cs.paddingRight);
        const need = canvas.measureText(el.placeholder).width;
        if (need > room + 1) issues.push(`placeholder does not fit: "${el.placeholder}" needs ${Math.round(need)}px, input has ${Math.round(room)}px`);
      }
      if (el.matches('a[href],button,input,select,textarea,[role=button]') && (r.right > innerWidth + 1 || r.left < -1)) issues.push(`control pushed off-screen: ${label(el)} (x ${Math.round(r.left)}..${Math.round(r.right)} in ${innerWidth}px viewport)`);
      // A scroll container inside the page (a tab panel, a card body) that scrolls sideways hides a reflow failure from
      // the page-level check. A data table's own frame may scroll sideways.
      const isTable = n => n?.matches?.('table,[role=table],[role=grid],[role=treegrid]');
      if (['auto', 'scroll'].includes(cs.overflowX) && el.scrollWidth > el.clientWidth + 1 && !isTable(el) && !isTable(el.firstElementChild)) issues.push(`scrolls sideways inside the page: ${label(el)} (content ${el.scrollWidth}px in a ${el.clientWidth}px box)`);
    }
    // Controls covering each other. Only the part left after clipping by overflow ancestors counts (collapsed
    // panels), controls in a sticky or fixed layer are only compared with each other (content scrolls under them), and a
    // control lying wholly inside another (a clear button inside an input) is a deliberate overlay.
    const visibleBox = el => {
      let { left, top, right, bottom } = el.getBoundingClientRect();
      for (let p = el.parentElement; p; p = p.parentElement) {
        if (getComputedStyle(p).overflow === 'visible') continue;
        const c = p.getBoundingClientRect();
        [left, top, right, bottom] = [Math.max(left, c.left), Math.max(top, c.top), Math.min(right, c.right), Math.min(bottom, c.bottom)];
      }
      return right - left > 1 && bottom - top > 1 ? { left, top, right, bottom } : null;
    };
    const layer = el => { for (let n = el; n; n = n.parentElement) if (['sticky', 'fixed'].includes(getComputedStyle(n).position)) return n; return null; };
    const controls = [...document.querySelectorAll(`${scope} :is(a[href],button,input,select,textarea,[role=button],[role=combobox])`)]
      .filter(el => el.checkVisibility())
      .map(el => ({ el, layer: layer(el), box: visibleBox(el) }))
      .filter(c => c.box);
    const inside = (x, y) => x.left >= y.left - 1 && x.right <= y.right + 1 && x.top >= y.top - 1 && x.bottom <= y.bottom + 1;
    controls.forEach((a, i) => controls.slice(i + 1).forEach(b => {
      if (a.el.contains(b.el) || b.el.contains(a.el) || a.layer !== b.layer || inside(a.box, b.box) || inside(b.box, a.box)) return;
      if (a.box.left < b.box.right - 1 && b.box.left < a.box.right - 1 && a.box.top < b.box.bottom - 1 && b.box.top < a.box.bottom - 1) issues.push(`controls overlap: ${label(a.el)} / ${label(b.el)}`);
    }));
    return issues;
  });

// Text whose font size stays the same when the root font size doubles: px sizes, browser defaults (buttons use a
// fixed 13.33px unless styled), or library inputs that turn a px size into a px font size.
const fixedSizeText = scope => {
  const texts = [...document.querySelectorAll(`${scope} *`)].filter(
    el => el.checkVisibility() && [...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim())
  );
  const before = texts.map(el => parseFloat(getComputedStyle(el).fontSize));
  const style = document.head.appendChild(document.createElement('style'));
  // Transitions are off, or a size that animates (a floating placeholder) would still read its old value
  style.textContent = 'html { font-size: 200% !important; } *, *::before, *::after { transition: none !important; }';
  const fixed = texts.filter((el, i) => parseFloat(getComputedStyle(el).fontSize) < before[i] * 1.9);
  style.remove();
  return fixed.map(el => `text does not grow: "${el.textContent.trim().replace(/\s+/g, ' ').slice(0, 28)}" stays ${getComputedStyle(el).fontSize}`);
};

const scope = flags.scope || 'body';
let total = 0;
for (const setting of SETTINGS) {
  const { browser, page } = await openPage(positional[0], flags, setting.viewport);
  const fixed = setting.name === '200% text' ? await page.evaluate(fixedSizeText, scope) : [];
  if (setting.css) await page.addStyleTag({ content: setting.css });
  await page.waitForTimeout(500); // let width-dependent components re-measure
  const issues = [...fixed, ...(await page.evaluate(measure, scope))];
  const shot = path.join(flags.out, setting.name.replace(/\W+/g, '-').toLowerCase() + '.png');
  await page.screenshot({ path: shot, fullPage: true });
  console.log(`\n== ${setting.name}  (${shot})`);
  if (issues.length === 0) console.log('   no automatic findings');
  for (const issue of issues.slice(0, 25)) console.log('   ISSUE: ' + issue);
  if (setting.name !== 'baseline (100%)') total += issues.length;
  await browser.close();
}
console.log(`\n${total} finding(s) outside the baseline. Open the screenshots too: overlaps and lost content are hard to detect automatically.`);
console.log('Also change the size AFTER load for components that measure themselves (carousels, charts, virtual lists).');
