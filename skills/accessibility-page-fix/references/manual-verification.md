# Manual verification

axe cannot judge keyboard flow, text scaling or whether names make sense. Run these on **every state** of the page
(see Step 1 of the skill). Examples use Playwright; the same checks work in any browser.

Bundled scripts (in `../scripts/`) automate the repetitive checks. Run them from the app directory, e.g.
`node <skill>/scripts/keyboard-walk.mjs http://localhost:4200/page --wait "h1"`. For pages behind a login, save a
Playwright storage state once and pass `--storage state.json`.

## Contents

- [Reaching states](#reaching-states)
- [Keyboard walk](#keyboard-walk)
- [Accessible names and roles](#accessible-names-and-roles)
- [Text size and reflow](#text-size-and-reflow)
- [Text spacing](#text-spacing)
- [Focus not obscured](#focus-not-obscured)
- [Target size](#target-size)
- [Screen reader spot-check](#screen-reader-spot-check)
- [Contrast over images](#contrast-over-images)
- [Visual regression](#visual-regression)

## Reaching states

Hidden states are where violations hide, so produce them on purpose. With Playwright, intercept the app's own
requests inside the test (never in production code):

```ts
// Error message: make the request fail
await page.route('**/api/login*', route => route.fulfill({ status: 401, json: {} }));

// Session-expired dialog: return a token that expires within the app's warning window
await page.route('**/api/login*', route => route.fulfill({ json: { token: shortLivedToken } }));

// Empty / loading state: return an empty list, or delay the response
await page.route('**/api/items*', route => route.fulfill({ json: { items: [] } }));

// Failure states: let each test choose which requests fail (500) or are not found (404)
const fail = (paths: string[]) => (route: Route) =>
  paths.some(path => route.request().url().includes(path))
    ? route.fulfill({ status: 500, json: { message: 'Mocked server error' } })
    : route.fallback();
```

To list the failure states, find every request the page, its child components and its dialogs make, and read
each error handler: an inline message, a notification, a disabled control, a fallback text such as "N/A", or the
app's shared error page. For each one that stays on the page, check: the message is announced (alert or status
role), stays long enough to read, has enough contrast, and focus ends up somewhere sensible (for example back on
the menu button after a failed delete). Open notifications usually sit in their own container at the end of
`<body>`; scan the page while it is open.

A loading state lasts only as long as the request, so hold it open: keep the route unanswered until the scan has
finished, then release it.

```ts
let release: () => void;
const held = new Promise<void>(r => (release = r));
await page.route('**/api/items*', async route => { await held; await route.fulfill({ json: { items } }); });
// … open the page, wait for [aria-busy="true"], scan …
release!();
```

Then wait for the state to be visible (`expect(...).toBeVisible()`), not for a fixed time, and scan. For a dialog,
scan only the dialog so the page behind it adds no noise: `new AxeBuilder({ page }).include('[role="dialog"]')`.
Inspect existing notification components before adding live regions: many already announce themselves.

## Keyboard walk

`scripts/keyboard-walk.mjs <url>` does steps 1-6 below automatically and flags invisible stops, stops where focus
changes nothing visible, and clickable-looking elements the keyboard cannot reach. It does not judge whether the
order is logical or the indicator is strong enough; look at those yourself.

1. Click on the page's heading, then press Tab repeatedly. Record the order and what each stop is.
2. For each stop confirm: it is a real control, it has a visible focus indicator, and the order follows the visual
   reading order.
3. Shift+Tab backwards through the same path; the order should reverse.
4. Operate each control with the keys users expect: Enter/Space on buttons, Enter on links, arrows inside menus,
   tabs and radio groups, Esc to close menus and dialogs.
5. Open every menu/dialog, confirm focus moves in, Esc closes, and focus returns to the opener.
6. Make sure Tab never gets stuck (outside of an open modal dialog) and never lands on something invisible or
   off-screen.

Script the walk to get a repeatable record:

```ts
await page.locator('h1').click();
const stops: string[] = [];
for (let i = 0; i < 80; i++) {
  await page.keyboard.press('Tab');
  const stop = await page.evaluate(() => {
    const el = document.activeElement as HTMLElement;
    if (!el || el === document.body) return 'BODY';
    const r = el.getBoundingClientRect();
    const visible = r.width > 0 && r.height > 0 && r.bottom > 0 && r.top < innerHeight;
    return `${el.tagName.toLowerCase()} "${(el.getAttribute('aria-label') || el.textContent || '').trim().slice(0, 40)}"${visible ? '' : ' [NOT VISIBLE]'}`;
  });
  stops.push(stop);
  if (stop === stops[0] && i > 0) break; // wrapped around
}
console.log(stops.join('\n'));
```

Anything marked `[NOT VISIBLE]` or `BODY` in the middle of the page needs a fix. Save the list before and after.

## Accessible names and roles

Read the accessibility tree instead of guessing from markup:

```ts
console.log(await page.locator('main').ariaSnapshot()); // roles, names, states
```

Check that every control has a meaningful name, correct role (button vs link), and state (expanded, checked,
selected, busy, current). Repeated controls must have distinct names.

## Text size and reflow

`scripts/text-size-check.mjs <url>` runs all four checks in this section and the next (200% text, 320 px width,
text spacing) and reports horizontal scroll, clipped text, placeholders that do not fit, and controls pushed
off-screen, with a screenshot per setting. Open the screenshots: overlap and lost content are hard to detect
automatically.

Text size (1.4.4): set the root font size to 200% (for example 32 px when the default is 16 px).

```ts
await page.addStyleTag({ content: 'html { font-size: 200% !important; }' });
```

Reflow (1.4.10): set the viewport to 320 × 640 and reload.

```ts
await page.setViewportSize({ width: 320, height: 640 });
```

In both cases check: all text grows, no clipped or overlapping text, no controls pushed out of reach, no horizontal
scrolling for text content, and components that depend on width (carousels, tables, charts) still lay out correctly.
Repeat it with every dialog and menu open (`--click` opens one before the checks, `--scope '[role="dialog"]'`
limits the findings to it):

```bash
node <skill>/scripts/text-size-check.mjs http://localhost:4200/orders --click "#export-button" --scope '[role="dialog"]'
```

Text that does not grow: record each text's computed font size, double the root font size, and compare. Anything
below about 1.9× is fixed somewhere: a px font size, a browser default (an unstyled `<button>` stays 13.33 px), a
component that derives its font size from a px input such as `height`, or a library CSS variable whose fallback is
fixed. Trace it with the browser's Styles panel (the rule that wins, or the inherited one), or by matching the
element against `document.styleSheets`; inline styles set by components won't show up there.

Horizontal reflow in a dialog: first check that the dialog box fits the viewport width. A dialog wider than the
screen inside a scrollable overlay lets each control be scrolled into view sideways, so a "can every control be
reached" check passes while the dialog still fails reflow. For
components that only measure themselves on creation or on window resize, change the size **after** load too and
confirm they update.

## Text spacing

Apply this and confirm nothing is cut off or overlaps (1.4.12):

```ts
await page.addStyleTag({ content: `
  * { line-height: 1.5 !important; letter-spacing: 0.12em !important; word-spacing: 0.16em !important; }
  p { margin-bottom: 2em !important; }` });
```

## Focus not obscured

With sticky headers, footers or banners present, Tab through the page and verify the focused element is not fully
covered (2.4.11). Make the window short enough for content to scroll under the sticky bar, or this never shows.
In the keyboard walk it appears as "no visible focus" on stops near the top or bottom edge. Fix with
`scroll-padding` on the scroll container, `scroll-margin` on the focusable elements, or by changing the sticky
layer.

## Target size

Find small targets quickly:

```ts
const small = await page.evaluate(() =>
  [...document.querySelectorAll('a[href], button, input, select, textarea, [role=button], [tabindex]')]
    .map(el => ({ el, r: el.getBoundingClientRect() }))
    .filter(({ r }) => r.width > 0 && (r.width < 24 || r.height < 24))
    .map(({ el, r }) => `${el.tagName} ${Math.round(r.width)}×${Math.round(r.height)} "${(el.getAttribute('aria-label') || el.textContent || '').trim().slice(0, 30)}"`));
```

Each hit must have 24 px of clear space around it, or be enlarged (inline text links are exempt).

## Screen reader spot-check

When feasible, try the page with a real screen reader (VoiceOver on macOS, NVDA on Windows). At minimum:

- Landmarks and headings list gives a sensible outline of the page.
- Tabbing announces each control's name, role and state.
- Opening a menu/dialog announces it and moves focus; closing returns focus.
- Status and error messages are announced.

If you cannot run one, say so in the report. The accessibility-tree snapshot above is a partial substitute, not a
replacement.

## Contrast over images

axe reports `incomplete` for text on an image, gradient or pattern because it cannot read the background.
`scripts/contrast-sample.mjs <url> <selector>` hides the element's own text, samples the real pixels behind it,
and reports the **worst-case** ratio against the required one. Notes:

- Sample **inside** the element, away from its border: a white border once produced a false 1.6:1 reading.
- Hide the text, not the element: hiding the whole element also hides its own background.
- For placeholders the script reads the `::placeholder` color automatically; use `--color` to override.
- Check each state that changes the background (hover, focus, error).

## Visual regression

Take a screenshot of each state before and after the fixes. List every intended visual change (new focus ring, darker
color, larger target) in the report. Unintended differences (shifted layout, changed spacing, lost icons) are bugs.

The visual design must stay exactly as it was, except for the changes you list. Prove it with a pixel comparison
of the base branch against yours:

1. Start the base branch next to yours: `git worktree add ../base <base-branch>`, link `node_modules` into it, and
   run its dev server on another port against the **same** mocked backend. Remove the worktree afterwards.
2. Build the matrix of pages and states:
   - the page you fixed in every state (default, each view, expanded sections, open menus, each dialog, empty,
     error notification open);
   - every other page and dialog that uses a shared component, style sheet or layout you changed, and the app
     shell's own menus;
   - at least three desktop widths (for example 1440, 1280, 1024) and one just below each breakpoint you added.
3. Compare in one run (each path may end in `@@selector;;selector` to click through to a state):

```bash
node <skill>/scripts/compare-screenshots.mjs compare shots /orders "/orders@@#export-button" /home \
  --base http://localhost:4201 --head http://localhost:4200 \
  --viewports 1440x900,1280x720,1024x768 --full --storage state.json
```

4. Investigate **every** pair that differs. Open `shots/diff/<name>.png` (changed pixels in red) and the two
   originals; measure the element boxes and computed styles in both builds; find the rule in your diff that causes
   it. Classify each difference:
   - **intended** (new focus ring, darker color, larger target): list it in the report;
   - **regression** (shifted layout, changed spacing, lost icon): fix it and compare again;
   - **noise** (animation frame, loading state, time-dependent text): stabilise the capture and compare again.
5. A size mismatch (`different size`) always means a layout change: the page got taller or wider.
6. Measuring beats looking. When a pair differs, run `compare-screenshots.mjs boxes <path> --base … --head …`: it
   compares the position and size of every element in both builds, matched by position in the DOM tree (not by
   class name). The first element whose box differs is the cause; everything after it only moved. If no box
   differs, the change is colour or anti-aliasing.
7. Run the **base against itself** twice. Differences that appear there (animated artwork, logos, canvases) are
   noise: list them once and ignore them.

Typical causes of differences found this way:
- a `gap` added to a flex row that already had a margin between its children (spacing doubled);
- `flex-wrap`, `flex-basis` or `min-width` added for narrow screens that also changes the wide layout (the first
  line break moves earlier, or items stop being squeezed). Put such rules in a narrow-screen media query;
- a larger click target (24 px) that moves its icon by a pixel: grow the box towards the free side and pad the
  inside so the icon stays where it was;
- a fix that changes the layout only where the base was already broken (a button clipped at the screen edge). It
  can't be identical; list it as an intended difference.

Media queries in `rem` follow browser zoom and the browser's text size setting, but **not** a `font-size` set on
`html` by a script. Test the layout of such rules at the viewport width that zoom produces (200% zoom = half the
width), and use the `html` override only to find text that does not grow.

Desktop widths must come out identical. Narrow widths and large text are expected to differ where you made them
responsive; list those differences as intended. Before trusting the result, compare the base with itself (all
identical) and check the screenshots are taller than the viewport (`--full`).
