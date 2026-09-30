# Embedding an Astro Site as a Fragment (incl. Client Router)

**Verified** (`web-fragments@0.8.2` + `astro@5`, Playwright). A static Astro build embeds
cleanly, and `<ClientRouter />` performs real SPA navigation inside the fragment: link
clicks swap content with no full reload, JS state (`sessionStorage`) persists, and all
nav/asset fetches route through the gateway on the host's **single origin**.

**Watch:** the top browser URL does **not** change on fragment-internal SPA nav (stays at the
host route). Fragment-internal routes aren't address-bar deep-linkable in this setup — design
host-level routing if you need that.

## Working configuration

One rule (as with any fragment): **namespace pages AND assets under one prefix**, route that
whole prefix to the fragment.

```js
// 1. astro.config.mjs — namespace everything under base
import { defineConfig } from 'astro/config';   // NB: astro/config, not 'astro' (Astro 5)
export default defineConfig({
  base: '/astro',           // pages -> /astro/, /astro/page2/ ; assets -> /astro/_astro/...
  trailingSlash: 'always',
  build: { format: 'directory' },
});
```
```astro
---
// 2. layout — view transitions
import { ClientRouter } from 'astro:transitions';
---
<html><head><ClientRouter /></head><body><slot /></body></html>
```
```js
// 3. fragment endpoint — serve the static build mounted at the SAME base
fragApp.use('/astro', express.static('astro-fragment/dist', { extensions: ['html'] }));

// 4. host gateway — one routePattern covers pages + _astro assets + client-router fetches
const gateway = new FragmentGateway();
gateway.registerFragment({ fragmentId: 'astro', endpoint: 'http://localhost:5400',
  piercing: false, routePatterns: ['/astro/:_*'] });
app.use(getNodeMiddleware(gateway, { mode: 'development' }));
```
```html
<!-- 5. host shell — plain HTML resolves the client via an import map; src = fragment entry -->
<script type="importmap">{ "imports": { "web-fragments": "/_wf/elements.js" } }</script>
<web-fragment fragment-id="astro" src="/astro/"></web-fragment>
<script type="module">import { initializeWebFragments } from 'web-fragments'; initializeWebFragments();</script>
```
Serve the client bundle: `app.use('/_wf', express.static('node_modules/web-fragments/dist'))`.
`src="/astro/"` sets the initial route (the element sits on host `/`, outside `/astro/:_*`).

**Pitfalls:** `defineConfig` from `astro/config` (not `'astro'`); `base` must namespace pages
*and* assets so one `/astro/:_*` pattern catches all (too-narrow → 404s mid-nav); mount the
static build at the same base on the endpoint; give `<web-fragment>` a `src` when the host
route differs from the entry route; don't expect the address bar to track internal nav.

## ⚠️ Bug: head `<style>`/`<link>` accumulate across ClientRouter navigation

> **Filed upstream: [#297](https://github.com/web-fragments/web-fragments/issues/297)**
> (reproduced + verified locally; the bundled repro is what was reported). Tangential older
> tickets: #119 (head/body support, closed), #78 (`@import` piercing, closed).

When a fragment uses `<ClientRouter />` and each route injects its own CSS into `<head>`
(e.g. a `[...path].astro` catch-all where each page does `<Fragment set:html={beforeHeadEnd}
/><ClientRouter /><Fragment set:html={afterHeadEnd} />`), **the previous route's `<style>`
and `<link>` are not removed on navigation — they accumulate unbounded, and earlier pages'
rules keep applying.**

Traversing sites a → b → c → a → b, nodes present in the fragment shadow tree after each nav:

| Step | inline `<style>` left behind | total `<style>` | total `<link>` |
|---|---|---|---|
| a | a | 3 | 1 |
| b | a, b | 5 | 2 |
| c | a, b, c | 7 | 3 |
| a (revisit) | a, b, c, a | 9 | 4 |
| b (revisit) | a, b, c, a, b | 11 | 5 |

Nothing is ever removed; revisits add duplicates. With distinct rules on a shared
`#site-name`, leftovers visibly stack — by site C the element wears A's background + B's
border + C's italic at once. (Identical selectors hide it: last-inserted wins so the current
color looks right, but nodes still leak and unrelated rules still bleed.)

**Root cause:** reframed renders the doc as `wf-html`/`wf-head`/`wf-body` and patches
`document.head` → `wf-head`. To apply head `<style>`/`<link>` in the shadow tree it
**relocates them out of `wf-head`** (probe: `wf-head` empty while nodes pile up elsewhere).
Astro's swap cleans `document.head` (= `wf-head`), but the relocated nodes aren't there, so
they're never removed. The two head strategies don't compose. (An `astro:after-swap` cleanup
of `document.head` can't reach the relocated nodes either.)

**Mitigations:** keep the fragment's `<head>` stable — load one shared stylesheet once,
scope per-page rules under a body class/attribute instead of swapping `<link>`/`<style>` per
route (stable head ⇒ no accumulation). Or drop `<ClientRouter />` and use the smooth-swap
recipe below.

## Smooth page transitions WITHOUT ClientRouter (avoids #297)

**Verified working.** Keep `<head>` stable, intercept internal link clicks, `fetch` the
target, and swap **only the content region** inside `document.startViewTransition()`.
(`document.startViewTransition` is available in the reframed context — verified — so this is a
real crossfade.)

Why simpler options fail: native cross-document VT (`@view-transition`) and plain `<a>` links
both trigger a real navigation, which **navigates the top window out of the embed**;
CSS-entrance animation still needs a swap and gives no crossfade.

**Link handling — you need not tag every link.** Opt-in (`a[data-swap]`) is explicit but
verbose; **opt-out (recommended, verified)** intercepts all `<a>` and falls through for
anything that shouldn't swap. Verified: untagged internal links (`/astro/*`) soft-swap; an
out-of-namespace link falls through to a real navigation.

```html
<head>
  <style>
    #content { view-transition-name: wf-content; }      /* loaded ONCE, never swapped */
    [data-site="a"] #site-name { color: red; }
    [data-site="b"] #site-name { color: green; }
    ::view-transition-old(wf-content), ::view-transition-new(wf-content) { animation-duration: 300ms; }
  </style>
</head>
<body>
  <nav><a href="/astro/smooth/a/">A</a> <a href="/astro/smooth/b/">B</a></nav>  <!-- no tagging -->
  <main id="content" data-site="a"> … page content … </main>
  <script is:inline>
    async function navigate(url, push) {
      const html = await (await fetch(url)).text();
      const next = new DOMParser().parseFromString(html, 'text/html').querySelector('#content');
      const cur = document.querySelector('#content');
      if (!next || !cur) { location.href = url; return; }            // graceful fallback
      const swap = () => cur.replaceWith(next);                       // reframed adopts the node;
      if (typeof document.startViewTransition === 'function')         // use importNode if a browser balks
        document.startViewTransition(swap); else swap();
      if (push) history.pushState({}, '', url);
    }
    document.addEventListener('click', (e) => {                       // OPT-OUT filter
      const a = e.target.closest && e.target.closest('a[href]');
      if (!a || e.defaultPrevented) return;
      if (e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return; // new tab/window
      if (a.target && a.target !== '_self') return;                  // target="_blank"
      if (a.hasAttribute('download') || a.getAttribute('rel') === 'external') return;
      const url = new URL(a.href, location.href);
      if (url.origin !== location.origin) return;                    // external site
      if (!url.pathname.startsWith('/astro/')) return;               // outside this fragment's routes
      if (url.pathname === location.pathname && url.hash) return;     // same-page anchor
      e.preventDefault();
      navigate(url.pathname + url.search, true);
    });
    window.addEventListener('popstate', () => navigate(location.pathname, false));
  </script>
</body>
```
The two fragment-critical guards are `url.origin !== location.origin` and
`!url.pathname.startsWith('/astro/')` — both must do a real navigation, not a swap.

Verified across a → b → c → a → b: head `<style>` count stays **constant** (vs ClientRouter's
3→5→7→9→11), content swaps, scoped colors correct, no stale styles, stays embedded. Top URL
stays at the host route; `history.pushState` keeps back/forward working. Tradeoff: ~20 lines
of swap logic and you forgo Astro's per-element `transition:name` beyond what you wire.

## Reproduce
Bundled under `scripts/experiments/` (run with `NODE_PATH=<playground>/node_modules node <probe>` after `npm i && astro build` in the fragment and `node server.mjs` in the host):
- `astro-fragment/` + `astro-host/server.mjs` — minimal Astro app + express host/gateway.
- `measure-astro.cjs` — basic ClientRouter embed (SPA-vs-reload + network).
- `astro-fragment/src/pages/[...path].astro` + `measure-head.cjs` — the #297 accumulation/pollution repro.
- `astro-fragment/src/{layouts/SmoothLayout.astro, pages/smooth/[site].astro}` + `measure-smooth.cjs` / `measure-optout.cjs` — smooth-swap (stable head) + opt-out link handling.
