---
name: accessibility-page-fix
description: >
  Finds and fixes WCAG 2.2 AA accessibility issues on one specific page of a web app: scans with axe-core,
  walks the page by keyboard, checks text resize and screen-reader semantics, fixes the code, verifies, and
  reports. Use when asked to fix a11y/accessibility/WCAG issues, make a page keyboard- or screen-reader-friendly,
  or remediate axe violations on a given page, route, URL or component.
license: Apache-2.0
compatibility: >
  A web app with a runnable dev server and Node.js 22+. Uses Playwright + axe-core (set up by the
  accessibility-infra-setup skill if missing). Installing browsers needs network access on first run.
---

# accessibility-page-fix

Fixes accessibility issues on **one page at a time** and proves the fixes. Targets **WCAG 2.2 level AA**.
Works on any web app: nothing here depends on a particular framework, component library or backend.

Automated scanners catch only part of WCAG. A page is not done when axe is green — it is done when axe is green
**and** the manual checks in Step 4 pass. Do both.

## Input

The user names the page to fix. Accept any of these and resolve it to a URL you can open:

- a URL or route path (`/orders/123`, `https://…`)
- a component, template or file (find the route that renders it)
- a feature name ("the settings page") — find it in the router/navigation, confirm with the user if ambiguous

If no page is given, ask for one. Do not audit the whole app. If the user wants several pages, do them one by one,
each with its own Steps 1–6.

## Workflow

Copy this checklist and track progress:

```
- [ ] Step 1: Make the page reachable and list its states
- [ ] Step 2: Baseline scan (axe) and capture current behaviour
- [ ] Step 3: Triage findings
- [ ] Step 4: Manual checks (keyboard, focus, zoom/text size, semantics)
- [ ] Step 5: Fix, one cause at a time, verifying each
- [ ] Step 6: Lock in with tests, run regressions, report
```

### Step 1 · Make the page reachable and list its states

1. Check for existing accessibility test infrastructure (an axe fixture, an `accessibility` test project, a
   `test:a11y` script). If it is missing, tell the user and offer the `accessibility-infra-setup` skill; do not
   build a parallel setup. For a one-off scan without infrastructure, use `@axe-core/playwright` directly.
2. Find out which **variant** of the page you are fixing. Pages often switch implementation on runtime config or
   feature flags (a config file the app loads at start-up). Check which value local runs and CI use (CI may build
   its config from a template), test that variant, and name any variant you did not cover in the report.
3. Start the app and open the page. If it needs a login, use the test credentials the project already uses; never
   invent or hard-code real credentials. If the backend is unavailable, intercept network calls in the browser
   (Playwright `page.route`) and return small fake responses that satisfy the page — only enough to render it.
   Keep mocks inside test or local-dev code, never in production code.
4. List the page's **states**. Each one is scanned separately because hidden or conditional UI is invisible to axe:
   default, loading, empty, error, populated, dialogs and menus open, expanded/collapsed sections, tabs, form
   validation errors, hover/focus-only content, carousels or pagers moved to a later position.
5. List the **contexts** the page's components render in. The same component is often a full page in one place
   and a dialog, drawer or embedded panel in another (for example a login form shown again in a session-expired
   dialog). Each context is its own state to scan, and fixes must work in all of them.
6. Reach hard-to-reach states on purpose instead of skipping them: mock a failing request to get an error message,
   mock a short token lifetime to get a session-expired dialog, mock an empty response for the empty state
   ([references/manual-verification.md](references/manual-verification.md#reaching-states)).
   For **failure states**, go through every request the page and its dialogs make, and read what its error handler
   shows. Check app-wide error handling (HTTP interceptors, global error handlers) first: some failures replace
   the page with a shared error page, which is out of the page's scope.
7. Wait for animations and async content to settle before every scan (scanning mid-transition gives false
   contrast failures).

### Step 2 · Baseline

1. Run axe on every state with the tags `wcag2a`, `wcag2aa`, `wcag21a`, `wcag21aa`, `wcag22a`, `wcag22aa`,
   `best-practice`. Save the full results (violations **and** incomplete).
2. Plan the visual comparison now: the base branch will be run next to yours and every page and state you touch,
   and every page that uses a shared component or layout you may touch, will be compared pixel by pixel
   ([references/manual-verification.md](references/manual-verification.md#visual-regression)).
3. Record the page's current keyboard behaviour in Step 4 *before* changing code — it is the reference for
   regressions.

### Step 3 · Triage

Group findings by **root cause**, not by rule count — one wrong shared component can produce dozens of violations.
For each group, note the WCAG criterion, the affected elements, and where the fix belongs:

| Where the cause lives | What to do |
|---|---|
| This page's own code | Fix it. |
| A shared component or global style used by other pages | Fix at the root, but first find every consumer and decide whether the change is safe for all of them (see Gotchas). |
| A third-party library you cannot edit | Fix through its supported options, wrap it, or adjust the DOM it renders; never patch `node_modules`. |
| A design decision (colors, sizes) | Prefer existing design tokens. If none fits, propose the smallest change and flag it for the design owner. |
| Shared code another open, unmerged change already fixes | Reuse that change **byte for byte** (copy the files from its branch) instead of fixing it again differently: identical changes merge without conflicts. Put anything extra in separate blocks. |

Each **incomplete** result is a question for a human: check it by hand (Step 4) and decide — never ignore it,
never silence the rule. Details in [references/fix-patterns.md](references/fix-patterns.md#incomplete-results).

### Step 4 · Manual checks

Do these on every state; the full procedure is in
[references/manual-verification.md](references/manual-verification.md). Three bundled scripts do the repetitive
parts. Run them from the app directory (they load the app's own Playwright), and read their output as leads, not
verdicts:

| Script | What it does |
|---|---|
| `scripts/keyboard-walk.mjs <url>` | Tabs through the page; lists each stop, flags invisible stops, stops with no visible focus change, and clickable-looking elements the keyboard cannot reach |
| `scripts/text-size-check.mjs <url>` | Loads the page at 200% text, 320 px wide and with text-spacing overrides; reports text that does not grow, horizontal scroll, clipped text, placeholders that do not fit, dialogs wider than the screen, controls pushed off-screen or covering each other; saves screenshots |
| `scripts/contrast-sample.mjs <url> <selector>` | Measures real contrast for text over an image, gradient or pattern (axe `incomplete`), using the worst background pixel |
| `scripts/compare-screenshots.mjs compare` | Pixel-compares full-page screenshots of the base branch and your branch (several pages, states and widths in one run) and writes a diff image for every change; `boxes` lists the elements whose position or size differs, which finds the cause; `diff` compares two folders of screenshots |

All take `--wait <selector>` (an element that must exist; it may be hidden at some sizes, which is what the checks
look for), `--storage <state.json>` (a saved Playwright login state for pages behind authentication) and
`--click "<selector>;;<selector>"` (clicks to open a menu or dialog before checking). `text-size-check` also takes
`--scope <selector>` to report only one part of the page, such as `[role="dialog"]`.

- **Keyboard:** Tab and Shift+Tab through everything. Every interactive element is reachable, in a logical order,
  with a visible focus indicator that is not hidden behind sticky UI. No keyboard traps. Enter/Space/Esc/arrow
  keys work as users expect for buttons, menus, dialogs and widgets. Open **every** menu, dropdown and dialog with
  the keyboard and check where focus lands (inside it, not on `<body>`) and where it returns on Esc (the opener).
- **Names, roles, values:** each control has an accessible name (check the accessibility tree, not just the
  markup), the right role, and its state exposed (expanded, selected, checked, busy, current).
- **Text size and reflow:** set the browser/root font size to 200% and the viewport to 320 CSS px wide. All text
  grows, and nothing is cut off, overlaps, or needs two-dimensional scrolling (except truly 2D content like maps or
  tables). Check **every dialog and menu** this way too, not only the page: they are sized separately and often in
  px.
- **Structure:** one `h1`, headings in order, landmarks present (`header`, `nav`, `main`), lists and tables use
  real elements, reading order matches visual order.
- **Dynamic content:** status and error messages reach screen readers without stealing focus; focus moves
  sensibly when content opens, closes or is replaced.
- **Pointer:** targets are at least 24×24 CSS px (or have enough spacing); nothing needs a drag as the only way.
- **Contrast and color:** text 4.5:1 (3:1 for large text), UI components and meaningful graphics 3:1; color is
  never the only signal.

### Step 5 · Fix

Work through the triage groups one at a time, highest impact first (blockers for keyboard/screen-reader users, then
perceivability, then polish). For each group:

1. Make the smallest change that fixes the cause, using native HTML elements before ARIA
   ([references/fix-patterns.md](references/fix-patterns.md)). **Search the project and its design system first**
   for something that already does the job — a screen-reader-only class, a focus-ring mixin, color tokens, a
   component option for accessible names — and reuse it instead of adding a new one. This matters most for
   behaviour: if the design system ships accessibility services (focus management, a live announcer, focus
   trapping, root-font-size tracking), use them, through their injection tokens or public API, instead of local
   code. List its exports once at the start (search for `focus`, `announc`, `live`, `trap`, `font`, `sr-only`).
2. Re-run only the affected scans and the keyboard check for that area.
3. Re-run the comparison (`compare-screenshots.mjs compare`). Unintended visual changes are bugs; intended ones
   (a darker color, a larger target) are listed in the report. Changes for narrow screens or large text must leave
   the desktop layout pixel-identical.
4. Move on only when the group is green.

Rules while fixing:

- **Do not** suppress or disable axe rules, add `aria-hidden` to hide a problem, or `display:none` things to make a
  scan pass.
- **Do not** change business logic, data flow or API contracts. If a fix seems to need it, stop and ask.
- Do not add ARIA that repeats what the native element already says (`role="button"` on a `<button>`).
- Prefer changing the element (div → button, span → link) over bolting on `role`, `tabindex` and key handlers.
- Keep the diff reviewable: avoid reformatting unrelated code. Re-indentation from new wrappers is fine; mixed
  refactors are not.

### Step 6 · Lock in, regress, report

1. **Add a scan per state** for this page in the project's accessibility test project, following the existing
   fixture and conventions. Mock only what the page needs. Add a focused test for behaviour axe cannot check
   (keyboard path, focus return, text-size layout) when you changed it.
2. **Prove the new tests catch the problems:** temporarily revert only the fix, run the new tests and confirm they
   fail; restore the fix and confirm they pass. A test that passes either way protects nothing: if it passes on
   the old code, the scenario misses the bug (the last page of a list, where the widget re-focuses and scrolls,
   instead of a middle page), so change the scenario, not the assertion. Check a suspected issue on every page you
   plan to fix it on: a detail such as a sticky footer can make it a non-issue there. If the new tests fail early
   for an unrelated reason (for example waiting for a heading the fix adds), run a temporary copy that waits for
   something else, so the scans themselves run against the old code and report the real problems.
3. Run: the new scans, the existing accessibility tests, the unit tests for everything you touched, lint, the type
   check, and the project's functional tests for pages that use any shared component you changed. Run the new tests
   several times (`--repeat-each`) before calling them stable, and report any failure you could not explain.
   When you later simplify the tests, keep every assertion: merge tests that share a setup, put repeated states
   in a table, and share helpers, but re-run the revert proof for any check you rewrote.
4. If the project documents accessibility conventions, add the new ones (for example "icon buttons use X").
5. Report using [references/report-template.md](references/report-template.md): what was found, what was fixed,
   what remains and why, observations that are not failures, shared code touched, and visual changes.

Done means: all scans for the page's states pass with no violations, every incomplete is resolved or explained,
Step 4 passes, and no regressions in tests or screenshots.

## Gotchas

- **Library popups sit outside every landmark.** Many UI kits attach open menus and dropdown lists to the end of
  `<body>`, so axe's `region` best practice flags them. When the library offers no inline option, scan the page
  with the popup excluded, then the popup on its own with every rule except `region`, and document it. Don't
  disable `region` for the whole page.
- **Sticky footers and headers hide focus.** A sticky paginator or toolbar covers the controls that scroll under it
  (WCAG 2.4.11). The keyboard walk shows it as stops with no visible focus near the screen edge. Give focusable
  elements a `scroll-margin` at least as tall as the sticky bar.
- **Async refreshes drop focus.** A menu that reloads its items after opening re-renders them and loses the focused
  element. Restore focus into the menu after the refresh if it was there before.
- **Global CSS can remove focus outlines.** A rule such as `button:focus { outline: none }` beats a component's own
  `:focus` outline. Check the computed style, and draw the design system's focus ring on `:focus-visible`.
- **Brand colors often fail contrast.** Test a replacement token against every background it appears on, including
  hover, selected and highlighted states, not just white. One token may not fit all of them.
- **The app shell must reflow too.** At 320 px a fixed-position header and sidebar push every page off-screen.
  Below a breakpoint, switch the shell to normal flow (header wraps, page scrolls, sidebar collapses), leaving the
  desktop layout untouched.
- **Branch from the right base, without tracking main.** A branch created from `origin/main` tracks it, so a plain
  push sends commits to `main`. Create fix branches with `--no-track` and push with `-u origin <branch>`.
- **One component, several contexts.** Landmarks and headings that are right for a page are wrong inside a dialog
  (a second `main`, a second `h1`). Make them depend on the context, and scan the dialog on its own with
  axe's `include` so the page behind it does not add noise.
- **Axe cannot see fixed sizes.** Widths and heights in px clip text when users enlarge it (a placeholder or
  label cut off at 200%). The text-size script and screenshots find these; axe does not.
- **Text in px doesn't grow, and not all px is in your CSS.** Look for: browser defaults (a `<button>` without a
  font size is a fixed 13.33 px), component inputs that turn a px size into a px font size (a button `height` in
  px), and library CSS variables nobody sets, whose fallback is fixed. Compare each text's font size before and
  after doubling the root font size; `text-size-check` does this.
- **Breakpoints don't help when only the root font size grows.** Media queries in `rem`/`em` follow the browser's
  default font size, not the page's root font size. With 200% text set on `html`, a layout that only stacks below
  a breakpoint stays side by side and controls start covering each other. Grid and flex rows should hold on their
  own: `minmax(min-content, 1fr)` instead of `minmax(0, 1fr)` for columns holding controls, and `flex-wrap` on
  rows. Check at more than one viewport width, and look for overlapping controls, not just off-screen ones.
- **Scrolling can hide a reflow failure.** A dialog wider than a 320 px screen can still let every control be
  scrolled into view, sideways. That's two-dimensional scrolling, which fails reflow. Check that the dialog itself
  fits the screen width before checking its controls, and look at the screenshot when a new check passes on the
  first try.
- **Notifications that close on their own.** A toast that disappears after a few seconds fails WCAG 2.2.1 for
  errors people need time to read, even if it pauses on hover or focus: keyboard users rarely reach it in time.
  Keep errors and warnings open until closed (usually one setting in the app's notification wrapper; it is shared,
  so list it). Scan the page with the notification open. A notification that stays open can then cover the focused
  element (WCAG 2.4.11), typically a sticky footer under a bottom toast: Tab through the page with one open, and
  let Esc close notifications without moving focus.
- **Live regions need real spaces.** Frameworks that strip whitespace between elements can turn "1 source,
  0 replacements" into "1source0replacements" in the announced text. Check the region's `textContent`.
- **Playwright's `fullPage` is not the full page.** Apps that scroll an inner container (a shell with a fixed
  header and sidebar) show only the first screen. Use `compare-screenshots.mjs --full`, which grows the viewport to
  the tallest scrolling element, and check that the PNG is taller than the viewport.
- **Layout fixes for small screens belong in a media query.** Wrapping, new flex bases and relaxed minimum
  widths added without one change the wide layout too: the page looks the same at first glance and differs by a
  few pixels. The pixel comparison with the base branch finds this; measure element boxes to find the cause.
- **Compare like with like.** Run the base branch from a separate worktree (`git worktree add ../base <base>`,
  with `node_modules` linked from the main checkout), against the same mocked backend and the same login, so a
  difference can only come from code. A saved login is per origin: put both origins in the state file.
- **Shared global styles.** Converting a shared stylesheet from px to rem renders the same pixels at the default
  size and fixes every page that uses it. Prove it with screenshots of those pages, and list them as shared code.
- **Placeholder is not a label.** Inputs labelled only by a placeholder need an accessible name (visible label,
  or the component's accessible-name option with the placeholder text contained in it) and an `autocomplete`
  token where the field is personal data or a credential.
- **Check existing announcements before adding live regions.** Toasts and notification components often announce
  themselves already; inspect their DOM before adding another.
- **Don't write environment claims into tests.** Comments such as "no credentials needed" are true only for one
  setup; tests move between repos. Describe what the test does, not where it runs.
- **Shared code has a blast radius.** Before editing a shared component, directive, mixin or global style, search for
  every use, run the tests for those places, and look at one or two of them in the browser. A fix that is right for
  this page can break another.
- **Scan whole states, not just the happy path.** Open menus, dialogs and error states are where most violations
  hide.
- **`incomplete` is not "pass".** Typical causes: text over images or gradients, content partly clipped by a
  scroll container, elements axe could not measure. Resolve by hand, and where it is a test artifact (scroll
  position, animation) fix the test setup rather than excluding the rule.
- **Visible focus is not enough.** The indicator must not be clipped by `overflow: hidden` or covered by sticky
  headers/footers (WCAG 2.4.11), and mouse clicks should not leave sticky highlight states meant for keyboard users
  — use `:focus-visible` for those.
- **Hover-only is not enough.** Anything revealed on hover must also appear on keyboard focus and be dismissible
  without moving the pointer (1.4.13).
- **Sizes in px break text scaling.** Libraries and canvases that only accept px need values derived from the
  current root font size and updated when it changes.
- **Off-screen is still focusable.** Slides, collapsed panels and hidden drawers that stay in the DOM need
  `inert` (or `hidden`) so Tab and screen readers skip them.
- **Live regions are tricky.** `role="alert"` interrupts; several at once talk over each other. Use `role="status"`
  (polite) for routine updates and reserve `alert` for urgent, single messages. A live region reads most reliably
  when it exists before its text changes.
- **Third-party widgets re-render.** A widget can recreate its own DOM (resize, data change) and drop attributes you
  added once. Apply fixes in a way that survives re-rendering (supported options, or an observer that re-applies).
- **Do not rely on one tool.** axe finds roughly a third to half of issues. Keyboard, zoom and accessibility-tree
  checks find the rest.
- **Not every oddity is a failure.** A submit button that stays disabled until the form is valid, a missing skip
  link on a one-form page, or a design choice you would change are observations. Report them in their own list;
  do not change behaviour to "fix" them without asking.
- **Don't lose the accessible name when restyling.** An icon-only control needs a name from text, `aria-label` or
  `aria-labelledby`; a tooltip alone is not a name.

## Out of scope

- Setting up the accessibility test infrastructure → use `accessibility-infra-setup`.
- Auditing or fixing the whole app in one pass.
- WCAG AAA criteria, or standards other than WCAG 2.2 AA.
- Native mobile apps and PDFs.
- Legal conformance statements (VPAT/ACR). Say what was tested and what was not; do not claim "fully compliant".
