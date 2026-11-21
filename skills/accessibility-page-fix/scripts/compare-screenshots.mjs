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
//   pair that differs, <out>/diff (changed pixels in red over a faded copy of the base). Each separate changed region
//   is listed with its box and pixel count, followed by the elements whose box or computed style changed at that width.
//   Also writes <out>/comparison-N.png, every changed region as base | head | diff crops (each distinct change once),
//   and <out>/comparison.md: one table row per differing pair, with empty cells for what the diff image shows, the
//   cause, and whether it is intended, a regression or noise.
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

/** Freezes animations, transitions and the caret, in the document and in every open shadow root. */
async function freeze(page) {
  await page.evaluate(css => {
    const roots = [document];
    const walk = root => {
      for (const el of root.querySelectorAll('*')) {
        if (el.shadowRoot) {
          roots.push(el.shadowRoot);
          walk(el.shadowRoot);
        }
      }
    };
    walk(document);
    for (const root of roots) {
      const style = document.createElement('style');
      style.textContent = css;
      (root instanceof Document ? root.head : root).appendChild(style);
    }
  }, FREEZE);
}

/**
 * Opens the page, freezes motion and (with --full) grows the viewport to the page's whole scrollable height.
 * Returns the screenshot's height, so the caller can show whether it is taller than the viewport.
 */
async function capture(url, file, viewport, options, clicks = '') {
  const [width, height] = viewport;
  const { browser, page } = await openPage(url, { ...options, click: clicks || undefined }, { width, height });
  await freeze(page);
  if (options.full) {
    // The tallest scrolling element decides the height: the document, or an inner container of the app shell.
    // Scrollers with no visible height (collapsed panels) hide their content and don't count.
    const extra = await page.evaluate(() => {
      const elements = [];
      const walk = root => {
        for (const el of root.querySelectorAll('*')) {
          elements.push(el);
          if (el.shadowRoot) walk(el.shadowRoot);
        }
      };
      walk(document);
      const scrollers = [document.scrollingElement, ...elements].filter(
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
  const shotHeight = page.viewportSize().height;
  await browser.close();
  return shotHeight;
}

// The computed styles that change pixels without moving a box
const STYLES = ['color', 'background-color', 'border-color', 'outline', 'font-size', 'font-weight', 'opacity', 'fill'];

/**
 * Every element's box (left, top, width, height) and STYLES, keyed by its place in the DOM tree, open shadow roots
 * included.
 */
async function elementBoxes(url, viewport, options, clicks = '') {
  const [width, height] = viewport;
  const { browser, page } = await openPage(url, { ...options, click: clicks || undefined }, { width, height });
  await freeze(page);
  const boxes = await page.evaluate(styles => {
    const out = {};
    const walk = (el, at) => {
      const r = el.getBoundingClientRect();
      // getAttribute, not className: an SVG element's className is an object, not a string
      const cls = (el.getAttribute('class') || '').split(/\s+/).filter(Boolean).slice(0, 2).join('.');
      const computed = getComputedStyle(el);
      out[at] = {
        label: el.tagName.toLowerCase() + (cls ? '.' + cls : ''),
        box: [r.left, r.top, r.width, r.height].map(n => Math.round(n * 10) / 10),
        style: Object.fromEntries(styles.map(name => [name, computed.getPropertyValue(name)])),
      };
      [...el.children].forEach((child, i) => walk(child, `${at}/${i}`));
      [...(el.shadowRoot?.children ?? [])].forEach((child, i) => walk(child, `${at}/shadow/${i}`));
    };
    walk(document.body, 'body');
    return out;
  }, STYLES);
  await browser.close();
  return boxes;
}

/**
 * Elements whose computed styles differ, matched like boxes. An inherited change (a parent's color) shows up on every
 * child, so a change is listed only on the first element that has it, not on children that have the same change.
 */
function styleChanges(base, head) {
  const changed = [];
  const keys = {};
  for (const [at, h] of Object.entries(head)) {
    const b = base[at];
    if (!b || b.label !== h.label) continue;
    keys[at] = new Set();
    const parent = keys[at.replace(/\/(shadow\/)?\d+$/, '')];
    const own = [];
    for (const name of STYLES) {
      if (b.style[name] === h.style[name]) continue;
      // Borders, outlines and SVG fills default to the text color: a change there that only follows it adds nothing
      if (['border-color', 'outline', 'fill'].includes(name) && b.style[name].includes(b.style.color) && h.style[name].includes(h.style.color)) continue;
      const key = `${name} ${b.style[name]} -> ${h.style[name]}`;
      keys[at].add(key);
      if (!parent?.has(key)) own.push(key);
    }
    if (own.length) changed.push({ at, label: h.label, change: own.join('; ') });
  }
  return changed;
}

/** Elements whose box differs, matched by their place in the tree; the first one is the cause, the rest only moved. */
function boxChanges(base, head) {
  const changed = [];
  let compared = 0;
  for (const [at, h] of Object.entries(head)) {
    const b = base[at];
    if (!b || b.label !== h.label) continue; // the trees diverge here: an element was added or removed
    compared++;
    if (b.box.join() !== h.box.join()) changed.push({ at, label: h.label, base: b.box, head: h.box });
  }
  return { changed, compared, baseCount: Object.keys(base).length, headCount: Object.keys(head).length };
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
      // Changed pixels are grouped in 16 px cells; touching cells form one region. Separate regions are reported
      // separately, so a few anti-aliased pixels don't hide inside one box with a real change
      const CELL = 16;
      const columns = Math.ceil(x.width / CELL);
      const cells = new Map();
      for (let i = 0; i < x.pixels.length; i += 4) {
        const delta = Math.abs(x.pixels[i] - y.pixels[i]) + Math.abs(x.pixels[i + 1] - y.pixels[i + 1]) + Math.abs(x.pixels[i + 2] - y.pixels[i + 2]);
        if (delta > 0) {
          changed++;
          const [px, py] = [(i / 4) % x.width, Math.floor(i / 4 / x.width)];
          const key = Math.floor(py / CELL) * columns + Math.floor(px / CELL);
          const cell = cells.get(key) ?? { left: px, top: py, right: px, bottom: py, pixels: 0 };
          cell.left = Math.min(cell.left, px);
          cell.right = Math.max(cell.right, px);
          cell.top = Math.min(cell.top, py);
          cell.bottom = Math.max(cell.bottom, py);
          cell.pixels++;
          cells.set(key, cell);
          out.set([255, 0, 0, 255], i);
        } else out.set([x.pixels[i] / 4 + 191, x.pixels[i + 1] / 4 + 191, x.pixels[i + 2] / 4 + 191, 255], i);
      }
      if (!changed) return { changed: 0 };
      const regions = [];
      const seen = new Set();
      for (const start of cells.keys()) {
        if (seen.has(start)) continue;
        seen.add(start);
        const region = { left: Infinity, top: Infinity, right: -1, bottom: -1, pixels: 0 };
        for (const queue = [start]; queue.length; ) {
          const key = queue.pop();
          const cell = cells.get(key);
          region.left = Math.min(region.left, cell.left);
          region.right = Math.max(region.right, cell.right);
          region.top = Math.min(region.top, cell.top);
          region.bottom = Math.max(region.bottom, cell.bottom);
          region.pixels += cell.pixels;
          const [cx, cy] = [key % columns, Math.floor(key / columns)];
          for (const [dx, dy] of [[-1, -1], [0, -1], [1, -1], [-1, 0], [1, 0], [-1, 1], [0, 1], [1, 1]]) {
            const next = (cy + dy) * columns + cx + dx;
            if (cx + dx >= 0 && cx + dx < columns && cells.has(next) && !seen.has(next)) {
              seen.add(next);
              queue.push(next);
            }
          }
        }
        regions.push(region);
      }
      regions.sort((p, q) => p.top - q.top || p.left - q.left);
      const canvas = document.createElement('canvas');
      canvas.width = x.width;
      canvas.height = x.height;
      canvas.getContext('2d').putImageData(new ImageData(out, x.width, x.height), 0, 0);
      return { changed, regions, image: canvas.toDataURL('image/png').split(',')[1] };
    }, images);
    if (result.size) results.push({ name, status: `different size ${result.size}` });
    else if (!result.changed) results.push({ name, status: 'identical' });
    else {
      if (outDir) fs.writeFileSync(path.join(outDir, name), Buffer.from(result.image, 'base64'));
      const shown = result.regions.slice(0, 8).map(r => `\n    x ${r.left}-${r.right}, y ${r.top}-${r.bottom}: ${r.pixels} px`);
      const more = result.regions.length > 8 ? `\n    … ${result.regions.length - 8} more` : '';
      results.push({ name, status: `${result.changed} pixels differ in ${result.regions.length} region(s)${shown.join('')}${more}`, regions: result.regions });
    }
  }
  // A screenshot taken only on the "after" side was never compared
  for (const name of fs.readdirSync(afterDir).filter(f => f.endsWith('.png') && !fs.existsSync(path.join(beforeDir, f)))) {
    results.push({ name, status: `missing in ${beforeDir}` });
  }
  await browser.close();
  return results;
}

/**
 * Writes comparison-1.png, comparison-2.png…: every changed region of every differing pair as base | head | diff
 * crops. A crop that looks exactly the same in several places (one change repeated on many pages and widths) is shown
 * once, so a few images cover every pair. Returns the images and, per pair, the rows that show its regions.
 */
async function overview(outDir, results) {
  const files = [];
  const where = new Map();
  const pairs = results.filter(r => r.regions);
  if (!pairs.length) return { files, where };
  const { chromium } = loadPlaywright();
  const browser = await chromium.launch();
  const page = await browser.newPage();
  const found = new Map(); // crop image -> the pair of each region that looks like it
  for (const r of pairs) {
    const images = ['base', 'head', 'diff'].map(dir => fs.readFileSync(path.join(outDir, dir, r.name)).toString('base64'));
    const crops = await page.evaluate(async ([images, regions]) => {
      const loaded = await Promise.all(images.map(async data => {
        const img = new Image();
        img.src = 'data:image/png;base64,' + data;
        await img.decode();
        return img;
      }));
      return regions.map(r => {
        const [left, top] = [Math.max(0, r.left - 12), Math.max(0, r.top - 12)];
        const width = Math.min(loaded[0].width, r.right + 13) - left;
        const height = Math.min(loaded[0].height, r.bottom + 13) - top;
        // Small changes are enlarged (up to 4x) so a 1 px shift shows; large ones shrink to fit the sheet
        const scale = Math.min(4, 392 / width, 240 / height);
        const [w, h] = [Math.max(1, Math.round(width * scale)), Math.max(1, Math.round(height * scale))];
        const canvas = document.createElement('canvas');
        canvas.width = w * 3 + 16;
        canvas.height = h;
        const context = canvas.getContext('2d');
        context.imageSmoothingEnabled = false;
        context.fillStyle = '#fff';
        context.fillRect(0, 0, canvas.width, canvas.height);
        loaded.forEach((img, i) => context.drawImage(img, left, top, width, height, i * (w + 8), 0, w, h));
        return canvas.toDataURL('image/png');
      });
    }, [images, r.regions]);
    for (const crop of crops) found.set(crop, [...(found.get(crop) ?? []), r.name]);
  }
  const groups = [...found];
  const ROWS = 6;
  for (let start = 0; start < groups.length; start += ROWS) {
    const file = `comparison-${files.length + 1}.png`;
    const items = groups.slice(start, start + ROWS).map(([crop, names], i) => {
      const counts = new Map();
      for (const name of names) counts.set(name, (counts.get(name) ?? 0) + 1);
      for (const name of counts.keys()) where.set(name, [...(where.get(name) ?? []), `${file} row ${i + 1}`]);
      const listed = [...counts].map(([name, n]) => (n > 1 ? `${name} (${n} regions)` : name));
      const label = listed.length > 3 ? `${listed.slice(0, 3).join(', ')} and ${listed.length - 3} more pair${listed.length > 4 ? 's' : ''}` : listed.join(', ');
      return [crop, `${i + 1}. ${label}`];
    });
    const sheet = await page.evaluate(async items => {
      const loaded = await Promise.all(items.map(async ([crop]) => {
        const img = new Image();
        img.src = crop;
        await img.decode();
        return img;
      }));
      const LINE = 18;
      const canvas = document.createElement('canvas');
      canvas.width = 1200;
      canvas.height = LINE + loaded.reduce((sum, img) => sum + LINE + img.height + 14, 0);
      const context = canvas.getContext('2d');
      context.fillStyle = '#fff';
      context.fillRect(0, 0, canvas.width, canvas.height);
      context.fillStyle = '#000';
      context.font = '13px sans-serif';
      context.fillText('Each row: base | head | diff (changed pixels in red), below the pairs where it occurs', 4, 13);
      let y = LINE;
      items.forEach(([, label], i) => {
        context.fillText(label, 4, y + 13);
        context.drawImage(loaded[i], 0, y + LINE);
        y += LINE + loaded[i].height + 14;
      });
      return canvas.toDataURL('image/png').split(',')[1];
    }, items);
    fs.writeFileSync(path.join(outDir, file), Buffer.from(sheet, 'base64'));
    files.push(file);
  }
  await browser.close();
  return { files, where };
}

if (mode === 'compare' && rest.length >= 2 && flags.base && flags.head) {
  const [outDir, ...entries] = rest;
  const viewports = String(flags.viewports || flags.viewport).split(',').map(parseViewport);
  for (const side of ['base', 'head']) fs.mkdirSync(path.join(outDir, side), { recursive: true });
  const shots = {};
  for (const entry of entries) {
    const [route, clicks] = entry.split('@@');
    for (const viewport of viewports) {
      const name = `${slug(entry)}-${viewport[0]}.png`;
      const heights = [];
      for (const side of ['base', 'head']) {
        heights.push(await capture(String(flags[side]).replace(/\/$/, '') + route, path.join(outDir, side, name), viewport, flags, clicks));
      }
      shots[name] = { entry, route, clicks, viewport };
      // With --full, a screenshot no taller than the viewport means the page fits it (or the inner scroller was missed)
      const fits = heights.map(h => (h > viewport[1] ? `${h} px` : `${h} px, fits the viewport`));
      console.log(`shot ${name}: base ${fits[0]}, head ${fits[1]} (viewport ${viewport[1]} px)`);
    }
  }
  const results = await diffFolders(path.join(outDir, 'base'), path.join(outDir, 'head'), path.join(outDir, 'diff'));
  console.log();
  const rows = [];
  for (const r of results) {
    console.log(`${r.name}: ${r.status}`);
    const shot = shots[r.name];
    if (!shot || r.status === 'identical' || r.status.startsWith('missing')) continue;
    // Measure why this pair differs, at its own width: the first element whose box changed is the cause
    const [base, head] = await Promise.all(['base', 'head'].map(side => elementBoxes(String(flags[side]).replace(/\/$/, '') + shot.route, shot.viewport, flags, shot.clicks)));
    const { changed } = boxChanges(base, head);
    const styled = styleChanges(base, head);
    const measured = [
      ...(changed.length ? [] : ['boxes: no element moved or changed size']),
      ...changed.slice(0, 3).map(c => `boxes: ${c.label} at ${c.at}: base ${c.base.join(', ')} -> head ${c.head.join(', ')}`),
      ...(changed.length > 3 ? [`boxes: … ${changed.length - 3} more elements moved`] : []),
      ...(styled.length ? [] : ['styles: no computed style changed (look for an image, a pseudo-element or anti-aliasing)']),
      ...styled.slice(0, 3).map(c => `styles: ${c.label} at ${c.at}: ${c.change}`),
      ...(styled.length > 3 ? [`styles: … ${styled.length - 3} more elements changed style`] : []),
    ];
    for (const line of measured) console.log(`    ${line}`);
    // Screenshots of different sizes get no diff image
    const image = r.status.startsWith('different size') ? '' : path.join('diff', r.name);
    if (image) console.log(`    diff image: ${path.join(outDir, image)}`);
    rows.push({ name: r.name, cells: [shot.entry, shot.viewport[0], r.status.split('\n')[0], measured.join('<br>'), image || 'none (sizes differ)', '', '', ''] });
  }
  const different = results.filter(r => r.status !== 'identical');
  console.log(`\n${results.length - different.length} identical, ${different.length} different. Diff images: ${path.join(outDir, 'diff')}`);
  const { files, where } = await overview(outDir, results);
  for (const row of rows) if (where.has(row.name)) row.cells[4] += `<br>${where.get(row.name).join(', ')}`;
  // A table with one row per differing pair; the last three cells are for the person who checks the pair
  const table = [
    `# Screenshot comparison: base ${flags.base}, head ${flags.head}`,
    '',
    `${results.length - different.length} of ${results.length} pairs identical. Open the overview images (${files.join(', ') || 'none'}): they show every changed region of every pair, base | head | diff, each distinct change once. Then fill the last three cells of every row, and put the table in the report.`,
    '',
    '| Page and state | Width | Pixels differ | Measured (boxes, computed style) | Diff image | What the diff image shows | Cause (rule in the diff) | Intended / regression / noise |',
    '|---|---|---|---|---|---|---|---|',
    ...rows.map(row => `| ${row.cells.map(cell => String(cell).replace(/\|/g, '\\|')).join(' | ')} |`),
  ];
  fs.writeFileSync(path.join(outDir, 'comparison.md'), table.join('\n') + '\n');
  if (files.length) console.log(`Overview of every change: ${files.map(file => path.join(outDir, file)).join(', ')}`);
  console.log(`Table to fill in: ${path.join(outDir, 'comparison.md')}`);
  process.exitCode = different.length ? 1 : 0;
} else if (mode === 'boxes' && rest.length === 1 && flags.base && flags.head) {
  const [route, clicks] = rest[0].split('@@');
  const viewport = parseViewport(flags.viewport);
  const sides = {};
  for (const side of ['base', 'head']) sides[side] = await elementBoxes(String(flags[side]).replace(/\/$/, '') + route, viewport, flags, clicks);
  const { changed, compared, baseCount, headCount } = boxChanges(sides.base, sides.head);
  for (const c of changed.slice(0, Number(flags.max ?? 30))) {
    console.log(`${c.at.split('/').length}  ${c.label}\n      base ${c.base.join(', ')}\n      head ${c.head.join(', ')}`);
  }
  console.log(`\n${changed.length} of ${compared} elements differ (base ${baseCount}, head ${headCount}). Boxes are left, top, width, height.`);
} else if (mode === 'diff' && rest.length === 2) {
  for (const r of await diffFolders(rest[0], rest[1], flags.out)) console.log(`${r.name}: ${r.status}`);
} else {
  console.error('Usage: compare-screenshots.mjs compare <out-dir> <path[@@click]> ... --base <url> --head <url> [--viewports 1440x900,1024x768] [--full]');
  console.error('       compare-screenshots.mjs diff <before-dir> <after-dir> [--out <dir>]');
  console.error('       compare-screenshots.mjs boxes <path[@@click]> --base <url> --head <url> [--viewport 1440x900]');
  process.exit(2);
}
