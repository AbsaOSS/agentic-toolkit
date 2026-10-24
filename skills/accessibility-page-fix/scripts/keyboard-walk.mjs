#!/usr/bin/env node
// Tabs through a page and prints every stop: what it is, its name, whether it is visible and whether focusing it
// changes the pixels around it (a visible focus indicator). Flags problems with "ISSUE".
//
// Usage (run from the app directory):
//   node <skill>/scripts/keyboard-walk.mjs <url> [--wait <selector>] [--max 80] [--storage <state.json>]
//        [--start <selector>] [--no-visual]
//   --start  element to click before walking (default: the first h1, else the page corner)
import { openPage, parseArgs } from './_shared.mjs';

const { positional, flags } = parseArgs(process.argv.slice(2), { max: 80 });
if (!positional[0]) {
  console.error('Usage: keyboard-walk.mjs <url> [--wait <selector>] [--max 80] [--storage <state.json>] [--start <selector>] [--no-visual]');
  process.exit(2);
}
const { browser, page } = await openPage(positional[0], flags);

const describe = () =>
  page.evaluate(() => {
    const el = document.activeElement;
    if (!el || el === document.body) return { body: true };
    const r = el.getBoundingClientRect();
    const cs = getComputedStyle(el);
    const visible = r.width > 0 && r.height > 0 && r.bottom > 0 && r.right > 0 && r.top < innerHeight && r.left < innerWidth && cs.visibility !== 'hidden';
    const name = (el.getAttribute('aria-label') || el.getAttribute('title') || el.textContent || el.getAttribute('placeholder') || '').trim().replace(/\s+/g, ' ').slice(0, 40);
    return { body: false, tag: el.tagName.toLowerCase(), role: el.getAttribute('role'), name, visible, inert: !!el.closest('[inert]'), defaultRing: cs.outlineStyle === 'auto', box: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] };
  });

/** Screenshot of the area around the focused element, as a flat pixel array. */
async function pixelsAround(box) {
  const pad = 10;
  const clip = { x: Math.max(0, box[0] - pad), y: Math.max(0, box[1] - pad), width: Math.max(1, box[2] + pad * 2), height: Math.max(1, box[3] + pad * 2) };
  const png = await page.screenshot({ clip });
  return page.evaluate(async b64 => {
    const img = new Image();
    img.src = 'data:image/png;base64,' + b64;
    await img.decode();
    const c = document.createElement('canvas');
    c.width = img.width;
    c.height = img.height;
    const x = c.getContext('2d');
    x.drawImage(img, 0, 0);
    return Array.from(x.getImageData(0, 0, c.width, c.height).data);
  }, png.toString('base64'));
}

/** Counts pixels that change around the element when it loses focus; few or none means no visible focus indicator. */
async function focusIndicatorPixels(box) {
  const focused = await page.evaluateHandle(() => document.activeElement);
  const withFocus = await pixelsAround(box);
  await focused.evaluate(el => el.blur());
  const without = await pixelsAround(box);
  await focused.evaluate(el => el.focus()); // put focus back so the next Tab continues from here
  let changed = 0;
  for (let i = 0; i < withFocus.length; i += 4) {
    if (Math.abs(withFocus[i] - without[i]) + Math.abs(withFocus[i + 1] - without[i + 1]) + Math.abs(withFocus[i + 2] - without[i + 2]) > 30) changed++;
  }
  return changed;
}

const start = flags.start ? page.locator(flags.start).first() : page.locator('h1').first();
if (await start.count()) await start.click({ force: true }).catch(() => {});
else await page.mouse.click(2, 2);

const stops = [];
let issues = 0;
for (let i = 0; i < Number(flags.max); i++) {
  await page.keyboard.press('Tab');
  const stop = await describe();
  const key = JSON.stringify([stop.tag, stop.name, stop.box]);
  if (stops.length && stops[0].key === key) {
    console.log(`-- wrapped around after ${stops.length} stops`);
    break;
  }
  let line;
  if (stop.body) {
    line = `${String(i + 1).padStart(2)}. (focus left the page / on <body>)`;
  } else {
    const problems = [];
    if (!stop.visible) problems.push('NOT VISIBLE');
    if (stop.inert) problems.push('INSIDE inert');
    // `outline-style: auto` is the browser's own ring: visible, but not the design system's (unstyled control)
    if (stop.defaultRing) problems.push("BROWSER DEFAULT FOCUS RING, not the design system's");
    if (!flags['no-visual'] && stop.visible) {
      const changed = await focusIndicatorPixels(stop.box);
      if (changed < 20) problems.push(`NO VISIBLE FOCUS INDICATOR (${changed}px changed)`);
    }
    issues += problems.length ? 1 : 0;
    line = `${String(i + 1).padStart(2)}. ${stop.tag}${stop.role ? `[role=${stop.role}]` : ''} "${stop.name}" ${stop.box.join('x')}${problems.length ? '  ISSUE: ' + problems.join(', ') : ''}`;
  }
  stops.push({ key });
  console.log(line);
}
// Heuristic: elements that look clickable (pointer cursor or an onclick attribute) but are not, and are not inside,
// something the keyboard can reach. These are the classic "div with a click handler" problem.
const unreachable = await page.evaluate(() => {
  const focusable = 'a[href],button,input,select,textarea,summary,[tabindex]:not([tabindex="-1"]),[role=button],[role=link],[role=menuitem],[role=tab],[contenteditable=true]';
  const out = [];
  for (const el of document.querySelectorAll('body *')) {
    const r = el.getBoundingClientRect();
    if (r.width === 0 || r.height === 0 || el.closest('[inert],[hidden]')) continue;
    const clickable = el.hasAttribute('onclick') || getComputedStyle(el).cursor === 'pointer';
    // Skip elements that are, are inside, or contain something focusable, and labels whose control is focusable
    // (a <label> wrapping its <input>, or pointing at it with for=)
    if (!clickable || el.closest(focusable) || el.querySelector(focusable) || el.control) continue;
    // Only report the outermost clickable element, not every child that inherits the cursor
    if (el.parentElement && (el.parentElement.hasAttribute('onclick') || getComputedStyle(el.parentElement).cursor === 'pointer')) continue;
    out.push(`${el.tagName.toLowerCase()}${el.className ? '.' + String(el.className).trim().split(/\s+/)[0] : ''} "${(el.getAttribute('aria-label') || el.textContent || '').trim().replace(/\s+/g, ' ').slice(0, 30)}"`);
  }
  return out.slice(0, 20);
});
for (const item of unreachable) console.log(`ISSUE: looks clickable but is not keyboard-reachable: ${item}`);
issues += unreachable.length;

console.log(`\n${stops.length} stops, ${issues} issue(s). The focus-indicator test only detects "nothing changes", not whether the indicator is strong enough; check the order and the look of the ring yourself.`);
await browser.close();
