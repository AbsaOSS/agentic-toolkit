# Fix patterns

Framework-neutral patterns, shown in plain HTML. Apply them with your framework's syntax. First rule: **use the
native element; reach for ARIA only when no native element does the job.**

## Contents

- [Clickable things](#clickable-things)
- [Names for controls and images](#names-for-controls-and-images)
- [Form fields](#form-fields)
- [Menus, dialogs and disclosure widgets](#menus-dialogs-and-disclosure-widgets)
- [Focus](#focus)
- [Structure](#structure)
- [Status and error messages](#status-and-error-messages)
- [Sizing and text scaling](#sizing-and-text-scaling)
- [Off-screen and hidden content](#off-screen-and-hidden-content)
- [Third-party widgets](#third-party-widgets)
- [Contrast](#contrast)
- [Incomplete results](#incomplete-results)

## Clickable things

Wrong: a generic element with a click handler. It has no role, is not focusable and ignores Enter/Space.

```html
<div class="icon" onclick="open()"></div>
```

Right: a real button, reset so it looks the same.

```html
<button type="button" class="btn-reset" aria-label="Open settings">
  <svg aria-hidden="true">…</svg>
</button>
```

```css
/* Removes the browser's default button look; keeps it a real button */
.btn-reset { appearance: none; background: none; border: 0; padding: 0; margin: 0;
             font: inherit; color: inherit; text-align: inherit; cursor: pointer; }
```

- Navigation → `<a href>`. Action → `<button>`. Never a link without `href` or a button that only navigates.
- A whole clickable card/row: make one real control inside (usually the title) the keyboard target; let clicks
  bubble to the container for mouse users. Don't nest interactive elements.
- Remove inline `cursor: pointer` hacks once the element is a real control.

## Names for controls and images

Accessible name priority: visible text content → `aria-labelledby` → `aria-label` → `title` (last resort).

- Icon-only buttons: `aria-label` describing the action ("Search", "Actions for Invoice 12").
- When the same control repeats in a list, include the row's subject in the name so each one is distinct.
- The name must contain the visible label text (2.5.3). Don't label a "Search" button "Find".
- Decorative images/icons: `alt=""` or `aria-hidden="true"`. Informative ones: short `alt`. Logos next to the
  site name are usually decorative.
- A tooltip is not a name. It also must not be the only place information appears.

## Form fields

- **A placeholder is not a label.** It disappears while typing and is often low-contrast. Prefer a visible label.
  If the design keeps placeholder-only fields, give each input an accessible name through the component's
  accessible-name option (`aria-label`), and make the name contain the placeholder text (2.5.3).
- Set `autocomplete` tokens on fields about the user (`username`, `current-password`, `new-password`, `email`,
  `given-name`, …). This supports 1.3.5 and, for logins, 3.3.8: never block paste or password managers, and
  don't leave `autocomplete="off"` on credentials.
- Errors: text next to the field linked with `aria-describedby`, plus `aria-invalid="true"`.
- A value the user can't change (the only option there is) is text with a visible label, not a read-only input: a
  read-only input is still a Tab stop with nothing to do. Match the input's box size so the layout doesn't move.
- A submit button that is disabled until the form is valid is not a WCAG failure, but it hides the reason from
  users; report it as an observation and don't change behaviour without asking.

## Menus, dialogs and disclosure widgets

- A button that opens a menu or popup: `aria-haspopup="menu"` (or `dialog`) and `aria-expanded="true|false"`,
  updated from the widget's open/close events.
- A show/hide section: button with `aria-expanded` and `aria-controls`.
- Dialogs: label them (`aria-labelledby`), move focus in on open, trap Tab inside, close on Esc, and **return
  focus to the element that opened it**.
- A menu whose items change while it is open (loaded or re-checked after opening) re-renders them and drops focus
  to `<body>`. Remember whether focus was inside before the update, render the new items at once, and move focus
  back in the same task. A delayed refocus (a timer, or a library `focus()` that waits a few milliseconds) leaves a
  window where Esc lands on `<body>`: the menu closes, then the late refocus pulls focus into the closed menu and it
  is lost. Repeat such tests many times in parallel (`--repeat-each 30 --workers 6`) to expose the race.
- Custom widgets (tabs, listbox, combobox) must follow the WAI-ARIA Authoring Practices keyboard model. If a native
  element does it (`<select>`, `<details>`), prefer that.

## Focus

- Never remove the outline without a replacement that has ≥ 3:1 contrast and is clearly visible.
- If a component's own focus style doesn't show, look for a global rule that removes outlines (`button:focus
  { outline: none }`) and wins on specificity. Draw the design system's focus ring on `:focus-visible` instead of
  fighting the rule with `!important`.
- Use `:focus-visible` for keyboard-only styles so mouse clicks don't leave highlights behind. If a script tracks
  focus, check `element.matches(':focus-visible')`.
- Keep hover and focus state separate in code: ending hover must not clear a highlight that focus still needs, and
  vice versa.
- Rings drawn with `outline-offset`/pseudo-elements can be clipped by `overflow: hidden` ancestors; add padding or
  adjust the container.
- Sticky headers/footers: use `scroll-padding-top/bottom` on the scroll container so focused items aren't hidden
  (2.4.11). When the scroll container is hard to reach (the page scrolls inside a shared shell), put
  `scroll-margin-bottom` (at least the sticky bar's height) on the page's focusable elements instead.
- Be careful with helpers that set `position: relative` on focus: they break absolutely-positioned controls.
- After content is removed or replaced, send focus somewhere sensible (the next item, the container, a heading) —
  not to `<body>`. A heading used as a focus target gets `tabindex="-1"` and no ring: it is a starting point, not a
  control.
- The same goes for an action that removes or disables the focused control: a Publish button whose editor closes, an
  "Add" button that is disabled once its field is empty, a "Close" button that disappears. Move focus to where the
  user goes on (the control that opened the editor, the content's heading, the field). Check first that focus really
  drops: a button in a loading state often stays enabled and keeps it.
- A button that only disables itself while its own action runs (Reload, Refresh) should stay enabled instead:
  disabling it drops focus and the ring for the whole loading time, and moving focus back afterwards leaves that gap.
  The disabled state was also what stopped a second request, so keep that: ignore a press while loading. Otherwise
  two requests race and the older reply can arrive last; after a delete, the deleted row comes back. Test it with a
  slow response: a fast mock never shows either problem.
- A list keyed by object identity rebuilds an item when an update returns a new object for it (toggling a vote), and
  the item's focused button goes with it. Key list items by a stable id.
- A focus ring in the design system's brand color disappears on a bar of the same color (a branded page header).
  Give the ring a contrasting color there.
- A ring drawn with `::before`/`::after` replaces content that some widgets put in those pseudo-elements (a
  dropdown that shows its current value with `::before`). Draw the ring on the widget's container instead, for
  example `.dropdown:has(> .label:focus-visible)`.
- Don't pull focus away from a widget that manages its own focus (a paginator whose page buttons move with the
  arrow keys, a tab list). Fix what the page does around it instead: for example, don't scroll the page away from
  a paginator that keeps focus when it is used from the keyboard (the focus service's input modality tells you).

## Structure

- Landmarks: `<header>`, `<nav>`, `<main>` (one), `<footer>`, and `<section>`/`<aside>` with an accessible name when
  there are several. A component that renders both as a page and inside a dialog should add `main` and `h1` only
  in the page context (a dialog gets its name from its own title); a second `main` or `h1` is a violation. Dialogs
  attached to `<body>` never contain `main`: next to the page's own it is a second one. An app that can also run
  embedded in a host page (a micro-frontend) leaves `main` to the host there and uses a `div` for its content area.
- Where the heading would not fit the design, a screen-reader-only heading is fine. Reuse the project's existing
  "screen-reader only" class instead of writing a new one.
- Exactly one `h1` that names the page; headings descend without skipping levels. Pick the level by structure, then
  style with CSS — never choose a tag for its size.
- A section that loads data: `aria-busy="true"` while loading, and name it with `aria-labelledby` pointing to its
  heading.
- Lists → `ul/ol/li`; data tables → `table` with `th scope`; form groups → `fieldset/legend`.
- Update `document.title` when the route changes.
- Repeated items (cards, rows) with the same controls: give each control a name that contains its visible text plus
  the item, e.g. "More actions for Orders 2024". A shared component that is repeated should take the name as an
  input, with a sensible default for its other uses.
- Two widgets of the same kind on one page (two tables with the same toolbar buttons): when the library offers no
  name for its built-in controls, wrap each widget in a `<section>` named after its visible title. The buttons are
  then told apart by the region they are in. Only the widget goes in its section: a nearby link or button about
  something else stays outside, or screen readers announce it as part of the widget.

## Status and error messages

- Routine updates (saved, 3 results, loading finished): `role="status"` (polite).
- Urgent, rare errors: `role="alert"` (assertive, interrupts).
- Several sections failing together → don't give each an `alert`; use `status` or one shared live region.
- Live regions are most reliable when the container already exists in the DOM and only its text changes. A
  design-system live announcer service already does this; use it before adding a region of your own.
- A live region's text is what gets announced: make sure numbers and labels in it are separated by real spaces
  (templating engines that strip whitespace between elements glue them together).
- Notifications: errors and warnings stay until the user closes them (WCAG 2.2.1); routine success messages can
  close on their own. The close button needs a name and a 24×24 px target. Because they stay, they can cover the
  focused element (WCAG 2.4.11): make Esc close them without moving focus (a document `keydown` listener in the
  notification wrapper), or place them where they cover nothing interactive. Take Esc only when it is needed: a
  notification's box overlaps the focused element, focus is in a notification, or nothing has focus. Otherwise
  leave the key to the page, or it never reaches a tooltip, a drag in progress or a dialog. When Esc is taken, close
  one layer at a time, top first: an open menu or list, then the notifications, then a dialog or side panel. In the
  capture phase, before anything else handles the key, skip the notifications when focus is inside a popup or on a
  control whose popup is open (`aria-expanded="true"` together with `role="combobox"` or `aria-haspopup`; a section
  that expands in place is not a popup). Otherwise close them and stop the event, so the dialog under them stays
  open with its form intact. When focus was on a notification's own button, send it back to where it was before; if
  that element is gone (its panel closed, or it was drawn again), to the open dialog or the main landmark, with a
  `tabindex="-1"` that is removed again on blur. Focus must never fall to the top of the document. Checking whether
  a popup is visible fails while it animates closed. Remove the listeners when the app is destroyed.
- Notification libraries often drop a message identical to one that is still open. That was harmless while messages
  closed after a few seconds. Once errors stay open, the same failure a second time shows nothing and is not read
  out. Don't allow duplicates instead: identical errors stack up and cover half the screen. Keep one copy on screen
  and read the message out again through a live announcer, and cap how many notifications stay open (the oldest
  closes).
- Results that arrive later in a dialog (checks finishing, validation results) belong in a `role="status"` summary
  so they are announced without moving focus.
- Form errors: put text next to the field, link it with `aria-describedby`, set `aria-invalid="true"`, and move
  focus to the first error or an error summary on submit.

## Sizing and text scaling

- Use `rem`/`em`/`%` for font sizes, spacing, widths and line-heights that carry content. Avoid fixed `height` on
  text containers (use `min-height`). Fixed px widths on panels and inputs are a common cause of text cut off at
  200% (axe cannot see this; the text-size script can).
- Sizes that something else owns stay in px: a host page's panel, a third-party bar measured in px. Converted to
  rem, a calculation that subtracts them breaks as soon as the text size changes.
- Images such as logos: either scale them with the text (rem) or keep them at px and say so in the report. Pick
  one deliberately; a fixed logo is fine, a fixed text container is not.
- Libraries and canvases that accept only px (charts, carousels, virtual lists): compute px from the **current**
  root font size and recompute when it changes. Re-initialise them in a way that keeps their position (selected
  slide, scroll offset) and re-measures their container.
- Some libraries measure their container only at creation or on window `resize`. A layout change without a window
  resize (font size, collapsing a sidebar) leaves them stale; trigger their refresh API, or re-create them.
- Check 200% text, 400% zoom (320 px wide) and text-spacing overrides.
- Unstyled buttons use the browser's fixed default size (13.33 px). Give them a rem font size (`0.8333rem` keeps
  the same pixels) or `font: inherit`.
- Component inputs that take a size (`height="38px"`, `width="760px"` for a dialog) often accept rem too; pass rem.
  Some derive the font size from the height, so a px height means px text.
- Library CSS variables with fixed fallbacks (for example a stepper's label size): set the variables to rem values in
  the app's styles instead of overriding the library's selectors.
- Dialogs: give width and height in rem, and let the dialog shrink to the screen. A fixed height clips content once
  text grows; prefer a min-height or a height in rem. Rows of steps, tabs or chips that can't fit 320 px wrap onto
  more rows below a breakpoint.
- App shell at 320 px: a fixed-position header and a sidebar that fill the screen leave no room for the page. Below
  a breakpoint, switch the shell to normal flow (header becomes static and wraps, the page scrolls with the
  document) and collapse the sidebar by default. Follow the breakpoint with the framework's breakpoint service if it
  has one (it cleans up and is easy to replace in tests), otherwise with `matchMedia` and its `change` event.
  When the screen is wide again, restore the sidebar the user had there instead of forcing the default. Prove the
  desktop layout is pixel-identical.
- Toolbars and headers built as one flex row: let them wrap (`flex-wrap: wrap`, `min-width: 0` on children) instead
  of overflowing.
- Grid columns that hold controls: `minmax(min-content, 1fr)` rather than `minmax(0, 1fr)`, so the column can't
  shrink below its buttons and let them spill over the next column. At normal text size the column is wider than
  its content anyway, so the layout doesn't change.
- Pointer targets: at least 24×24 CSS px (`min-width`/`min-height`, or padding). A larger invisible hit area via
  pseudo-element keeps the design.

## Off-screen and hidden content

Content that is out of view but still in the DOM is reachable by Tab and screen readers unless you hide it:

- `inert` attribute: not focusable, not clickable, not exposed — right for off-screen slides, collapsed drawers,
  background behind a modal.
- `hidden` / `display: none`: removes it entirely (also from the accessibility tree).
- `aria-hidden="true"` alone does **not** remove focusability — never use it on something focusable.
- If the focused element becomes inert, move focus to a sensible nearby control first.

## Third-party widgets

- Prefer the library's accessibility options; read its docs for labels, keyboard support and ARIA.
- If it renders its own controls (previous/next buttons, close buttons) without names, add them through supported
  inputs or by decorating the rendered DOM.
- Widgets may re-render and drop what you added. Decorate in an idempotent function and re-run it when the widget
  changes its DOM (a `MutationObserver` scoped to the widget, run outside change-detection loops, ignoring changes
  inside the widget's content).
- Don't fork or patch vendored code, unless the vendored copy belongs to your own library and the user agrees.
- Popups that the library attaches to the end of `<body>` sit outside every landmark, so axe's `region` best
  practice flags them. If the library can't render them inline, scan the page with the popup excluded and then the
  popup alone with `region` disabled for that scan only, and note it in the test.
- Rich text editors: Tab often types a tab character, and in lists, quotes and code blocks Tab and Shift+Tab indent
  and outdent instead. In an empty list item that leaves no way out (WCAG 2.1.2). Turn off every key binding that
  takes Tab through the editor's options, and test Tab from plain text and from an empty list item. The editable
  area is usually a plain `contenteditable` element: give it `role="textbox"`, `aria-multiline="true"` and a name
  that matches its visible label. Every place that uses the editor must pass that name: a textbox without one is a
  new axe failure. Toolbar dropdowns and their options often have no names, and color swatches are smaller than
  24 px. Add the names once the editor has been created (its "created" callback) and enlarge the swatches with CSS.
- Date pickers grey out the days you can't pick. Disabled controls are exempt from contrast (WCAG 1.4.3), but if
  the library doesn't mark them `aria-disabled`, axe can't tell and reports them. Exclude exactly those day cells
  from that one scan, say why in the test, and report the missing `aria-disabled` as a library issue.
- If the library is your own design system, the root cause can be fixed there instead of worked around in every
  app. That is a separate change in a separate repo, so propose it to the user and let them choose where it goes
  (for example a vendored copy, or the wrapper component). Cover it with a test that renders the real widget, and
  remove the app's test workaround once the app uses the fixed version.

## Reuse before adding

Before writing a new class, mixin, token or helper, search the project and its design system for one that already
does the job: screen-reader-only classes, focus-ring mixins, color tokens, a component's accessible-name option, an
existing live-region/notification service. A second copy drifts from the first.

Design systems often ship accessibility **services** too, and these come first:

| Need | Look for | Instead of |
|---|---|---|
| Move focus, keep the focus ring only for keyboard users | A focus service (`focusElement`, input-modality signal) | `el.focus()` plus your own keyboard/mouse tracking |
| Keep Tab inside a container | A focus-trap helper | A hand-written `keydown` Tab handler |
| Announce a result that appears without moving focus | A live announcer service (`announce(message, politeness)`) | A new `role="status"` / `aria-live` element |
| Follow the root font size (for px-only libraries) | A root-font-size service or signal | Reading `getComputedStyle(document.documentElement)` and your own observers |

Prefer their injection tokens over the classes when both exist: the app can then override or disable them, so
handle a missing (null) service with a plain fallback.

## Contrast

- Text: 4.5:1 (3:1 for ≥ 24 px, or ≥ 18.66 px bold). UI components, icons, focus indicators: 3:1.
- Use the design system's tokens. When picking a lighter-looking replacement, compute the ratio against the
  **actual** background (page, card, hover state) instead of white.
- A brand or accent color that fails: list every background it is used on (white, tinted card, hover, selected,
  highlighted row) and test each candidate token against all of them. If none passes everywhere, use a different
  shade per background. Define new colors as tokens next to the existing ones, and flag them for the design owner.
- Disabled controls are exempt, but placeholder text is not.
- Don't rely on color alone: add text, an icon, a pattern or an underline.

## Incomplete results

axe reports `incomplete` when it can't decide. Resolve each by hand, and record the result:

| Typical reason | How to resolve |
|---|---|
| Text on a background image or gradient | Run `scripts/contrast-sample.mjs <url> <selector>` (samples the real pixels behind the text and reports the worst case); if it passes, note it as verified |
| Element "partially obscured" | Usually a scroll container clipping it at scan time: scroll to the top (or the relevant position) in the test setup and re-scan |
| Hidden or zero-size content | Confirm it is intentionally hidden from everyone |
| Pseudo-element content | Inspect computed styles |

Never turn off a rule to clear an incomplete. If it can't be proven either way, keep it as a documented manual
check.
