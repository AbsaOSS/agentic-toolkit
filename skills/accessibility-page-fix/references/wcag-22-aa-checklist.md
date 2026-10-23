# WCAG 2.2 AA checklist

Use this to decide how each criterion is checked on a page. **axe** column: ✅ well covered, ◐ partly, ✗ not
detectable (needs manual check). Level A criteria are included because AA conformance requires them too.

## Contents

- [Perceivable](#perceivable)
- [Operable](#operable)
- [Understandable](#understandable)
- [Robust](#robust)
- [New in WCAG 2.2](#new-in-wcag-22)

## Perceivable

| Criterion | axe | How to check | Typical fix |
|---|---|---|---|
| 1.1.1 Non-text content | ◐ | Every image/icon has suitable text alternative, or is hidden if decorative | `alt` text; `alt=""` for decoration; `aria-label` on icon-only controls; `aria-hidden` on decorative SVG |
| 1.2.x Time-based media | ✗ | Captions, transcripts, audio description exist for video/audio | Add captions/transcripts; usually a content task, flag it |
| 1.3.1 Info and relationships | ◐ | Inspect the accessibility tree: headings, lists, tables, form labels, groups | Real `h1–h6`, `ul/ol`, `table/th`, `label`, `fieldset/legend`, landmarks |
| 1.3.2 Meaningful sequence | ✗ | Reading order (DOM order) matches visual order | Reorder DOM instead of using CSS `order`/absolute positioning |
| 1.3.3 Sensory characteristics | ✗ | Instructions don't rely only on shape, color, position ("the red button on the right") | Add text labels |
| 1.3.4 Orientation | ◐ | Page works in portrait and landscape | Remove orientation locks |
| 1.3.5 Identify input purpose | ✅ | Personal-data fields have `autocomplete` | Add correct `autocomplete` tokens |
| 1.4.1 Use of color | ✗ | Information isn't conveyed by color alone (errors, links in text, charts) | Add icon, text, underline, pattern |
| 1.4.2 Audio control | ✗ | Auto-playing audio >3 s can be paused | Remove autoplay or add control |
| 1.4.3 Contrast (minimum) | ◐ | Text 4.5:1, large text 3:1; check **incomplete** results by hand (images, gradients, clipped areas) | Use design tokens with enough contrast; fix backgrounds |
| 1.4.4 Resize text | ✗ | 200% text size with no loss of content or function | Use relative units (rem/em/%), avoid fixed heights, allow wrapping |
| 1.4.5 Images of text | ✗ | Text is real text, not an image | Replace with styled text |
| 1.4.10 Reflow | ✗ | 320 CSS px wide (400% zoom), no 2D scrolling | Responsive layout, `min-width: 0`, wrap, avoid fixed widths |
| 1.4.11 Non-text contrast | ◐ | UI component borders/icons/focus indicators and meaningful graphics ≥ 3:1 | Darker borders/icons, stronger focus ring |
| 1.4.12 Text spacing | ✗ | Apply line-height 1.5, paragraph spacing 2×, letter 0.12em, word 0.16em: nothing clipped | No fixed heights on text containers; no `overflow:hidden` on text |
| 1.4.13 Content on hover or focus | ✗ | Popups on hover/focus are dismissible (Esc), hoverable, persistent | Add Esc handling, keep popup open while pointer is over it |

## Operable

| Criterion | axe | How to check | Typical fix |
|---|---|---|---|
| 2.1.1 Keyboard | ◐ | Everything usable with keyboard only | Native controls (`button`, `a[href]`, `input`); not clickable `div`/`span` |
| 2.1.2 No keyboard trap | ✗ | Focus can always move away (Tab/Esc) | Fix focus traps outside modal dialogs; dialogs trap *and* release on close |
| 2.1.4 Character key shortcuts | ✗ | Single-key shortcuts can be turned off/remapped or work only on focus | Require a modifier or add a setting |
| 2.2.1 Timing adjustable | ✗ | Session/time limits can be extended | Warn and offer extension |
| 2.2.2 Pause, stop, hide | ◐ | Moving/auto-updating content >5 s has pause/stop (carousels!) | Add pause control; no autoplay |
| 2.3.1 Three flashes | ✗ | No content flashes more than 3×/s | Remove flashing |
| 2.4.1 Bypass blocks | ✅ | Skip link or landmarks to jump to main content | `main` landmark, skip link |
| 2.4.2 Page titled | ✅ | Unique, descriptive `<title>` that updates on route change | Set title per page/route |
| 2.4.3 Focus order | ✗ | Tab order is logical | Match DOM to visual order; avoid positive `tabindex` |
| 2.4.4 Link purpose (in context) | ◐ | Link text makes sense with its context | Descriptive text or `aria-label` |
| 2.4.5 Multiple ways | ✗ | More than one way to find a page (nav, search, sitemap) | Site-level; flag only |
| 2.4.6 Headings and labels | ✗ | Headings/labels describe their content | Rewrite text |
| 2.4.7 Focus visible | ◐ | Keyboard focus is always visible | Don't `outline: none` without a replacement; use `:focus-visible` |
| 2.5.1 Pointer gestures | ✗ | Multi-point/path gestures have single-pointer alternative | Add buttons |
| 2.5.2 Pointer cancellation | ✗ | Actions fire on release (`click`), not press | Use `click`; allow abort |
| 2.5.3 Label in name | ◐ | Accessible name contains the visible label text | Start the name with the visible text |
| 2.5.4 Motion actuation | ✗ | Shake/tilt actions have alternatives | Add controls |

## Understandable

| Criterion | axe | How to check | Typical fix |
|---|---|---|---|
| 3.1.1 Language of page | ✅ | `<html lang>` is set and valid | Add `lang` |
| 3.1.2 Language of parts | ◐ | Passages in another language have `lang` | Add `lang` on the element |
| 3.2.1 On focus | ✗ | Focus alone never changes context (navigates, submits) | Move actions to explicit controls |
| 3.2.2 On input | ✗ | Changing a field's value doesn't auto-submit/navigate without warning | Add a submit button or warn |
| 3.2.3 Consistent navigation | ✗ | Repeated navigation appears in the same order on every page | Shared layout |
| 3.2.4 Consistent identification | ✗ | Same function → same label/icon everywhere | Standardise names |
| 3.3.1 Error identification | ✗ | Errors are described in text and tied to the field | `aria-describedby`, error summary |
| 3.3.2 Labels or instructions | ◐ | Every input has a visible label and needed instructions | `label for`, hints |
| 3.3.3 Error suggestion | ✗ | Errors suggest how to fix | Better messages |
| 3.3.4 Error prevention (legal, financial, data) | ✗ | Submissions can be reviewed/reversed/confirmed | Confirm step or undo |

## Robust

| Criterion | axe | How to check | Typical fix |
|---|---|---|---|
| 4.1.2 Name, role, value | ✅ | Every control has name, role and state in the accessibility tree | Native elements; `aria-expanded/selected/checked/pressed`; valid ARIA only |
| 4.1.3 Status messages | ✗ | Success/error/progress messages are announced without moving focus | `role="status"` / `aria-live="polite"`; `role="alert"` for urgent |

(4.1.1 Parsing was removed in WCAG 2.2.)

## New in WCAG 2.2

| Criterion | Level | axe | How to check | Typical fix |
|---|---|---|---|---|
| 2.4.11 Focus not obscured (minimum) | AA | ✗ | Tab through the page with sticky headers/footers/cookie banners: the focused element is never completely hidden | `scroll-padding`, avoid covering sticky UI, `scroll-margin` |
| 2.5.7 Dragging movements | AA | ✗ | Anything done by dragging also works with a single click/tap or buttons | Add up/down buttons, click-to-move |
| 2.5.8 Target size (minimum) | AA | ◐ (`target-size`) | Pointer targets ≥ 24×24 CSS px, or 24 px of clear space around them | Padding/min-size; larger hit area via pseudo-element |
| 3.2.6 Consistent help | A | ✗ | Help (contact, chat, FAQ) is in the same place across pages | Shared layout |
| 3.3.7 Redundant entry | A | ✗ | Information already entered in a process isn't asked again | Prefill or let users select |
| 3.3.8 Accessible authentication (minimum) | AA | ✗ | Logins don't require remembering/transcribing/solving puzzles; paste and password managers work | Allow paste, `autocomplete`, alternatives |
