#!/usr/bin/env node
// Measures the real contrast of text (or an icon) that sits on an image, gradient or pattern, which axe reports
// as "incomplete" because it cannot read the background. It hides the element's own text, screenshots the area
// behind it (inset from borders), and reports the WORST contrast between the text color and any background pixel.
//
// Usage (run from the app directory):
//   node <skill>/scripts/contrast-sample.mjs <url> <css-selector> [--wait <selector>] [--storage <state.json>]
//        [--color <css color>]   text color override, e.g. for placeholders: --color "rgb(255,255,255)"
//        [--inset 4]
import { openPage, parseArgs } from './_shared.mjs';

const { positional, flags } = parseArgs(process.argv.slice(2), { inset: 4 });
const [url, selector] = positional;
if (!url || !selector) {
  console.error('Usage: contrast-sample.mjs <url> <css-selector> [--wait <selector>] [--storage <state.json>] [--color <css color>] [--inset 4]');
  process.exit(2);
}
const { browser, page } = await openPage(url, flags);
const target = page.locator(selector).first();
if (!(await target.count())) {
  console.error('No element matches ' + selector);
  process.exit(2);
}

const info = await target.evaluate(el => {
  const cs = getComputedStyle(el);
  const ph = el.matches('input,textarea') && el.placeholder && !el.value ? getComputedStyle(el, '::placeholder') : null;
  const r = el.getBoundingClientRect();
  return { color: (ph ?? cs).color, fontSize: parseFloat(cs.fontSize), fontWeight: Number(cs.fontWeight) || 400, box: { x: r.x, y: r.y, width: r.width, height: r.height } };
});
const textColor = (flags.color ?? info.color).match(/[\d.]+/g).slice(0, 3).map(Number);

// Make the element's text invisible (also placeholder and child text) but keep its own background, then sample.
await page.addStyleTag({ content: `${selector}, ${selector} * , ${selector}::placeholder { color: transparent !important; text-shadow: none !important; -webkit-text-fill-color: transparent !important; }` });
const inset = Number(flags.inset);
const clip = { x: info.box.x + inset, y: info.box.y + inset, width: Math.max(2, info.box.width - inset * 2), height: Math.max(2, info.box.height - inset * 2) };
const png = await page.screenshot({ clip });
const pixels = await page.evaluate(async b64 => {
  const img = new Image();
  img.src = 'data:image/png;base64,' + b64;
  await img.decode();
  const c = document.createElement('canvas');
  c.width = img.width;
  c.height = img.height;
  const x = c.getContext('2d');
  x.drawImage(img, 0, 0);
  const d = x.getImageData(0, 0, c.width, c.height).data;
  const seen = new Map();
  for (let i = 0; i < d.length; i += 4) seen.set(`${d[i]},${d[i + 1]},${d[i + 2]}`, 1);
  return [...seen.keys()].map(k => k.split(',').map(Number));
}, png.toString('base64'));

const lum = c => {
  const v = c.map(x => x / 255).map(x => (x <= 0.04045 ? x / 12.92 : ((x + 0.055) / 1.055) ** 2.4));
  return 0.2126 * v[0] + 0.7152 * v[1] + 0.0722 * v[2];
};
const ratio = (a, b) => {
  const [hi, lo] = [lum(a), lum(b)].sort((p, q) => q - p);
  return (hi + 0.05) / (lo + 0.05);
};
let worst = { r: Infinity, bg: null };
for (const bg of pixels) {
  const r = ratio(textColor, bg);
  if (r < worst.r) worst = { r, bg };
}
const large = info.fontSize >= 24 || (info.fontSize >= 18.66 && info.fontWeight >= 700);
const need = large ? 3 : 4.5;
console.log(`element: ${selector}`);
console.log(`text color rgb(${textColor}), ${info.fontSize}px, weight ${info.fontWeight} -> ${large ? 'large' : 'normal'} text, needs ${need}:1`);
console.log(`${pixels.length} distinct background colors sampled; worst case rgb(${worst.bg}) -> ${worst.r.toFixed(2)}:1`);
console.log(worst.r >= need ? 'PASS' : 'FAIL: below the required ratio at its worst point');
await browser.close();
process.exit(worst.r >= need ? 0 : 1);
