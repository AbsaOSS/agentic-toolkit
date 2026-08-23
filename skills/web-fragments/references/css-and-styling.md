# CSS & Styling Across the Fragment Boundary

How styles interact between a host page and an embedded fragment. **All claims are
empirically verified** (`web-fragments@0.8.x`, Playwright computed-style reads on both
sides), identical in **pierced and non-pierced** modes.

## Structure (what renders)

```
<web-fragment>                     ← light DOM
  #shadow-root
    <web-fragment-host>
      #shadow-root                 ← THE style boundary
        <style>…fragment styles…</style>
        <wf-document><html>…fragment body…</html></wf-document>
  <iframe name="wf:<id>" hidden>   ← reframed JS context (scripts run here)
```
Fragment markup + styles live in the **`web-fragment-host` shadow root**, so scoping follows
normal **Shadow DOM** rules → the behaviors below.

## Verified behaviors

1. **Selector rules don't cross the boundary, either direction.** Host `.card{…}` doesn't
   style a fragment `.card`, and vice versa. Host and fragment can reuse class names with
   zero collision. *(Host `.leak-class{magenta}` → fragment element stayed black.)*
2. **Inherited properties flow host → fragment.** `font-family`, `color`, `line-height`,
   etc. cascade down across the boundary. The host's typography/color baseline bleeds into
   every fragment. *(Host `body{font-family:Georgia}` → fragment text = Georgia.)*
3. **Custom properties (vars) inherit host → fragment.** They're inherited properties, so
   host `:root{--brand:red}` is visible as `var(--brand)` inside the fragment. Great for
   theming; risky if a fragment unknowingly reads a host token of the same name. *(`--brand`
   resolved to red inside the fragment.)*
4. **`:root` is DEAD inside a fragment.** It matches only the document root, which doesn't
   exist in a shadow tree, so a fragment's `:root{--brand:purple}` is a **no-op**. *(Tried to
   override `--brand` via `:root`; value stayed the inherited host red.)* → use `:host`.
5. **`:host` works** — sets properties on the shadow host, inherited by descendants. *(`:host{
   --accent:orange}` resolved to orange inside the fragment.)* Define fragment tokens here.
6. **Vars do NOT leak fragment → host.** Inheritance is downward only. *(Host reading
   `var(--host-accent)` defined in the fragment → unset/black.)*
7. **`@layer` is tree-scoped.** Host and fragment layer orderings are independent; neither
   reorders the other. *(Both had `base` then `theme`; each resolved to its own `theme`.)*

## Practical guidance

- **Expect host inheritance to reach the fragment.** To insulate, neutralize at the
  boundary: `:host { all: initial }` (aggressive) or set the inherited props you care about
  explicitly on `:host` (`font-family`, `color`, `line-height`).
- **Never put fragment tokens on `:root`** — silently dead; use `:host` (or a wrapper class).
- **Theme fragments via host `:root` tokens on purpose.** Define `--color-*`/`--space-*` on
  the host `:root`; fragments consuming `var(--…)` inherit them. This is the supported theming
  channel (Shadow DOM blocks reaching into a fragment's styles directly).
- **No prefixing needed** for host↔fragment class collisions (behavior #1 isolates them).
- **Host-side:** to keep a token out of fragments, scope it under a host-only wrapper class,
  not `:root`/`html`. Inherited props (font/color) still flow down unless the fragment
  overrides them at `:host`.

## Reproduce
`scripts/experiments/css-vars-isolation/` (host `index.html` + `fragment.html`) +
`scripts/experiments/measure-css.cjs` — launches Chromium, traverses the nested shadow roots,
prints computed `color`/`font-family`/var values for host and fragment probes. Run:
`NODE_PATH=<playground>/node_modules node measure-css.cjs`. To test a new question, add a
probe with a known expected color in `fragment.html` and read it through the path
`web-fragment ▸ shadowRoot ▸ web-fragment-host ▸ shadowRoot ▸ #your-id`.
