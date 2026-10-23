#!/usr/bin/env node
// Pixel-compares pages between a BASE build (the main branch) and a HEAD build (your branch), to prove a fix did not
// change the layout where it should not (other pages that share a component, the app shell, desktop sizes).
//
// Usage (run from the app directory):
//   node <skill>/scripts/compare-screenshots.mjs compare <out-dir> <path[@@click;;click]> [...]
//        --base http://localhost:4201 --head http://localhost:4200
//        [--viewports 1440x900,1280x720,1024x768] [--full] [--wait <selector>] [--storage <state.json>]
//   node <skill>/scripts/compare-screenshots.mjs diff <before-dir> <after-dir> [--out <dir>]
//   node <skill>/scripts/compare-screenshots.mjs boxes <path[@@click]> --base <url> --head <url> [--viewport 1440x900]
//        [--max 30]
//
// compare: shoots every path on both servers at every viewport and diffs them. Each path may end in
//   `@@selector;;selector` to click through to a menu or dialog first. Writes <out>/base, <out>/head and, for every
//   pair that differs, <out>/diff (changed pixels in red over a faded copy of the base).
// boxes: finds WHY two screenshots differ. Lists the elements whose position or size differs between the builds,
//   matched by their place in the DOM tree. The first one in the list is the cause; the rest only moved.
// --full: the page is captured at its whole height, including content that scrolls INSIDE the page (app shells
//   often scroll an inner container, so Playwright's own fullPage only captures the first screen).
// Animations, transitions and the text caret are frozen so that only real differences show up.
// A saved login (--storage) is per origin: the state file must hold an entry for both the base and the head URL.
import { createHash } from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';
import { loadPlaywright, openPage, parseArgs } from './_shared.mjs';

const { positional, flags } = parseArgs(process.argv.slice(2), { viewport: '1440x900', viewports: '' });
const [mode, ...rest] = positional;
const MAX_HEIGHT = 12000;
// File names stay short and unique even when the clicks are long: a readable prefix plus a hash of the whole entry
const slug = text => {
  const readable = text.replace(/^https?:\/\/[^/]+/, '').replace(/\W+/g, '-').replace(/^-|-$/g, '') || 'root';
  return readable.length <= 60 ? readable : `${readable.slice(0, 50)}-${createHash('sha1').update(text).digest('hex').slice(0, 8)}`;
};
const parseViewport = text => String(text).split('x').map(Number);

const FREEZE = '*,*::before,*::after{animation:none!important;transition:none!important;caret-color:transparent!important;scroll-behavior:auto!important}';

/** Opens the page, freezes motion and (with --full) grows the viewport to the page's whole scrollable height. */
async function capture(url, file, viewport, options, clicks = '') {
  const [width, height] = viewport;
  const { browser, page } = await openPage(url, { ...options, click: clicks || undefined }, { width, height });
  await page.addStyleTag({ content: FREEZE });
  if (options.full) {
    // The tallest scrolling element decides the height: the document, or an inner container of the app shell.
    // Scrollers with no visible height (collapsed panels) hide their content and don't count.
    const extra = await page.evaluate(() => {
      const scrollers = [document.scrollingElement, ...document.querySelectorAll('*')].filter(
        el =>
          el &&
          (el === document.scrollingElement || (el.clientHeight > 0 && ['auto', 'scroll'].includes(getComputedStyle(el).overflowY)))
      );
      return Math.max(0, ...scrollers.map(el => el.scrollHeight - el.clientHeight));
    });
    if (extra > 1) await page.setViewportSize({ width, height: Math.min(height + extra, MAX_HEIGHT) });
    await page.waitForTimeout(500);
  }
  await page.screenshot({ path: file });
  await browser.close();
}

/** Compares two folders of PNGs by name; returns one result per file and writes diff images when `outDir` is set. */
async function diffFolders(beforeDir, afterDir, outDir) {
  const { chromium } = loadPlaywright();
  const browser = await chromium.launch();
  const page = await browser.newPage();
  const results = [];
  if (outDir) fs.mkdirSync(outDir, { recursive: true });
  for (const name of fs.readdirSync(beforeDir).filter(f => f.endsWith('.png'))) {
    const after = path.join(afterDir, name);
    if (!fs.existsSync(after)) {
      results.push({ name, status: `missing in ${afterDir}` });
      continue;
    }
    const images = [path.join(beforeDir, name), after].map(f => fs.readFileSync(f).toString('base64'));
    const result = await page.evaluate(async ([a, b]) => {
      const load = async data => {
        const img = new Image();
        img.src = 'data:image/png;base64,' + data;
        await img.decode();
        const canvas = document.createElement('canvas');
        canvas.width = img.width;
        canvas.height = img.height;
        const context = canvas.getContext('2d');
        context.drawImage(img, 0, 0);
        return { pixels: context.getImageData(0, 0, img.width, img.height).data, width: img.width, height: img.height };
      };
      const [x, y] = [await load(a), await load(b)];
      if (x.width !== y.width || x.height !== y.height) return { size: `${x.width}x${x.height} vs ${y.width}x${y.height}` };
      const out = new Uint8ClampedArray(x.pixels.length);
      let changed = 0;
      const box = { left: Infinity, top: Infinity, right: -1, bottom: -1 };
      for (let i = 0; i < x.pixels.length; i += 4) {
        const delta = Math.abs(x.pixels[i] - y.pixels[i]) + Math.abs(x.pixels[i + 1] - y.pixels[i + 1]) + Math.abs(x.pixels[i + 2] - y.pixels[i + 2]);
        if (delta > 0) {
          changed++;
          const [px, py] = [(i / 4) % x.width, Math.floor(i / 4 / x.width)];
          box.left = Math.min(box.left, px);
          box.right = Math.max(box.right, px);
          box.top = Math.min(box.top, py);
          box.bottom = Math.max(box.bottom, py);
          out.set([255, 0, 0, 255], i);
        } else out.set([x.pixels[i] / 4 + 191, x.pixels[i + 1] / 4 + 191, x.pixels[i + 2] / 4 + 191, 255], i);
      }
      if (!changed) return { changed: 0 };
      const canvas = document.createElement('canvas');
      canvas.width = x.width;
      canvas.height = x.height;
      canvas.getContext('2d').putImageData(new ImageData(out, x.width, x.height), 0, 0);
      return { changed, box, image: canvas.toDataURL('image/png').split(',')[1] };
    }, images);
    if (result.size) results.push({ name, status: `different size ${result.size}` });
    else if (!result.changed) results.push({ name, status: 'identical' });
    else {
      if (outDir) fs.writeFileSync(path.join(outDir, name), Buffer.from(result.image, 'base64'));
      const { left, top, right, bottom } = result.box;
      results.push({ name, status: `${result.changed} pixels differ (x ${left}-${right}, y ${top}-${bottom})` });
    }
  }
  await browser.close();
  return results;
}

if (mode === 'compare' && rest.length >= 2 && flags.base && flags.head) {
  const [outDir, ...entries] = rest;
  const viewports = String(flags.viewports || flags.viewport).split(',').map(parseViewport);
  for (const side of ['base', 'head']) fs.mkdirSync(path.join(outDir, side), { recursive: true });
  for (const entry of entries) {
    const [route, clicks] = entry.split('@@');
    for (const viewport of viewports) {
      const name = `${slug(entry)}-${viewport[0]}.png`;
      for (const side of ['base', 'head']) {
        await capture(String(flags[side]).replace(/\/$/, '') + route, path.join(outDir, side, name), viewport, flags, clicks);
      }
      console.log(`shot ${name}`);
    }
  }
  const results = await diffFolders(path.join(outDir, 'base'), path.join(outDir, 'head'), path.join(outDir, 'diff'));
  console.log();
  for (const r of results) console.log(`${r.name}: ${r.status}`);
  const different = results.filter(r => r.status !== 'identical');
  console.log(`\n${results.length - different.length} identical, ${different.length} different. Diff images: ${path.join(outDir, 'diff')}`);
  process.exitCode = different.length ? 1 : 0;
} else if (mode === 'boxes' && rest.length === 1 && flags.base && flags.head) {
  const [route, clicks] = rest[0].split('@@');
  const [width, height] = parseViewport(flags.viewport);
  const boxes = {};
  for (const side of ['base', 'head']) {
    const { browser, page } = await openPage(String(flags[side]).replace(/\/$/, '') + route, { ...flags, click: clicks || undefined }, { width, height });
    await page.addStyleTag({ content: FREEZE });
    boxes[side] = await page.evaluate(() => {
      const out = {};
      const walk = (el, at) => {
        const r = el.getBoundingClientRect();
        const cls = (el.className?.toString() || '').split(/\s+/).filter(Boolean).slice(0, 2).join('.');
        out[at] = { label: el.tagName.toLowerCase() + (cls ? '.' + cls : ''), box: [r.left, r.top, r.width, r.height].map(n => Math.round(n * 10) / 10) };
        [...el.children].forEach((child, i) => walk(child, `${at}/${i}`));
      };
      walk(document.body, 'body');
      return out;
    });
    await browser.close();
  }
  let shown = 0;
  let compared = 0;
  for (const [at, head] of Object.entries(boxes.head)) {
    const base = boxes.base[at];
    if (!base || base.label !== head.label) continue; // the trees diverge here: an element was added or removed
    compared++;
    if (base.box.join() !== head.box.join() && shown++ < Number(flags.max ?? 30)) {
      console.log(`${at.split('/').length}  ${head.label}\n      base ${base.box.join(', ')}\n      head ${head.box.join(', ')}`);
    }
  }
  console.log(`\n${shown} of ${compared} elements differ (base ${Object.keys(boxes.base).length}, head ${Object.keys(boxes.head).length}). Boxes are left, top, width, height.`);
} else if (mode === 'diff' && rest.length === 2) {
  for (const r of await diffFolders(rest[0], rest[1], flags.out)) console.log(`${r.name}: ${r.status}`);
} else {
  console.error('Usage: compare-screenshots.mjs compare <out-dir> <path[@@click]> ... --base <url> --head <url> [--viewports 1440x900,1024x768] [--full]');
  console.error('       compare-screenshots.mjs diff <before-dir> <after-dir> [--out <dir>]');
  console.error('       compare-screenshots.mjs boxes <path[@@click]> --base <url> --head <url> [--viewport 1440x900]');
  process.exit(2);
}
