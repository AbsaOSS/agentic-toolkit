---
name: web-fragments
description: >-
  Build, embed, debug, and deploy micro-frontends with the Web Fragments framework
  (the `web-fragments` npm package by web-fragments.dev / Cloudflare). Use whenever the user
  works with web-fragments, the `<web-fragment>` element, `FragmentGateway`,
  `registerFragment`, `getWebMiddleware` / `getNodeMiddleware`, fragment "piercing", or the
  "reframed" iframe isolation — and more broadly when they want to incrementally migrate,
  decompose, or compose a web frontend from independently deployed micro-frontends that
  share one DOM, even if they don't name the library. Covers authoring a fragment, wiring it
  into a host app, gateway/route-pattern config, styling across the shadow boundary, and
  troubleshooting hydration/asset/type errors. Prefer this skill over guessing the API — the
  framework is beta (v0.8.x) and several public docs are stale.
---

# Web Fragments

Framework-/platform-agnostic micro-frontend architecture. Each micro-frontend's client JS
runs in an isolated context (a hidden iframe = *reframed*) while all fragments **share one
DOM, navigation, and history** — "containers for web frontends." Beta v0.8.x, in production
at Cloudflare.

**Don't read `node_modules/web-fragments/` source for the API — it's captured here and in
`references/`.** web-fragments.dev docs are partly stale; when they disagree with this skill,
trust the skill (verify via the package's `exports` map in `node_modules/web-fragments/package.json`).

## Mental model: 3 pieces

1. **Fragment app** — a *standalone* app (any stack) at an HTTP endpoint serving its own
   HTML + assets; doesn't know it's a fragment. → `references/fragment-authoring.md`
2. **Host (shell)** — the existing app that embeds fragments: calls `initializeWebFragments()`
   once + places `<web-fragment fragment-id="…">`. → `references/host-integration.md`
3. **Gateway** — **mandatory** middleware on the host server (issue #278): proxies fragment
   requests onto the host's single origin and *pierces* SSR markup into the shell.

Flow: browser → host origin → gateway matches `routePatterns` → proxies to fragment
`endpoint` → response composed into the host page.

## Public API (v0.8.x) — exactly three entry points

There is **no** `web-fragments/middleware` entry point (a stale doc claims one).

| Import | Exports |
|---|---|
| `web-fragments` | `initializeWebFragments()`, `WebFragment`, `WebFragmentHost` |
| `web-fragments/gateway` | `FragmentGateway`, `getWebMiddleware`, types `FragmentConfig`, `FragmentMiddlewareOptions` |
| `web-fragments/gateway/node` | `getNodeMiddleware` |

**Client (host bootstrap):**
```ts
import { initializeWebFragments } from 'web-fragments';
initializeWebFragments(); // defines the custom elements; call as early as possible
```
```html
<web-fragment fragment-id="party-button"></web-fragment>
```
`fragment-id` is required (throws without it); `src` is optional. `<web-fragment-host>` is
internal — you rarely author it.

**Gateway (host server):**
```ts
import { FragmentGateway } from 'web-fragments/gateway';
const gateway = new FragmentGateway(/* { piercingStyles?: string } */);
gateway.registerFragment({                 // method is registerFragment, NOT register
  fragmentId: 'party-button',              // required; must match the element's fragment-id
  endpoint: 'https://party-button.example.dev', // required; URL string OR a fetch-compatible fn
  routePatterns: ['/__wf/party-button/:_*', '/'], // required (path-to-regexp v6): assets + host route(s)
  piercing: true,                          // optional, default true; false = client-only
  // piercingClassNames, forwardFragmentHeaders, iframeHeaders, onSsrFetchError — see api-reference
});
```
Full `FragmentConfig` + deprecated aliases (`upstream`→`endpoint`,
`prePiercingClassNames`→`piercingClassNames`): `references/api-reference.md`.

**Middleware (pick ONE per host runtime):**
```ts
import { getWebMiddleware } from 'web-fragments/gateway';        // Web/Fetch: CF, Vercel, Netlify, Hono, SW
const mw = getWebMiddleware(gateway, { mode: 'development' });   // 'production' | 'development'

import { getNodeMiddleware } from 'web-fragments/gateway/node';  // Node: Express / Connect
app.use(getNodeMiddleware(gateway));
```
Per-framework wiring: `references/host-integration.md`.

## Workflow (add a fragment to an app)

1. **Fragment app** serves its own HTML+assets, emitting assets under a **unique** path
   (e.g. Vite `build.assetsDir: "__wf/<id>/"`) that lines up with the asset `routePattern`.
2. **Bootstrap** the host client: `initializeWebFragments()` at the earliest entry.
3. **Place** `<web-fragment fragment-id="…">` at the chosen host route.
4. **Register**: `new FragmentGateway()` + `registerFragment(...)` with two patterns (assets +
   host route). The host-route pattern MUST match where the element lives (step 3).
5. **Install** the middleware matching the runtime (Web vs Node).
6. **Verify** (below), then deploy — fragment and host ship independently.

## Verify

Fragment renders as **nested shadow roots**: `<web-fragment>` ▸ shadowRoot ▸
`<web-fragment-host>` ▸ shadowRoot ▸ `<wf-document>`, plus a hidden `<iframe name="wf:<id>">`
running its scripts. In dev tools: fragment DOM is in the main document but inside a shadow
root (style isolation); a `wf:<id>` context exists; removing the element tears it down;
asset requests hit `/__wf/<id>/…` on the **host** origin (proxied).

Automated: `node scripts/doctor.mjs <project-dir>` flags the common wiring mistakes (wrong
import path, `register` vs `registerFragment`, asset/routePattern mismatch, missing
middleware). Use it whenever a fragment "doesn't show up" or assets 404.

## Bundled resources

Load only the reference matching the task:
- `references/api-reference.md` — every export, full `FragmentConfig`/options, deprecations. Writing/reviewing gateway/element code.
- `references/host-integration.md` — middleware wiring per framework (Express, CF Pages/Workers, Vercel, Netlify, Hono, Angular, Next.js, Vite SPA).
- `references/fragment-authoring.md` — build a fragment from scratch: structure, Vite `assetsDir`, route patterns, deploy.
- `references/troubleshooting.md` — known issues/gotchas (hydration, asset truncation, nodenext types, Angular htmlrewriter, style accumulation). Read FIRST when broken.
- `references/css-and-styling.md` — **verified** style behavior across the shadow boundary (`:root` vs `:host`, `@layer`, what inherits/leaks).
- `references/csp-and-iframe.md` — CSP / `X-Frame-Options` / `frame-ancestors` so the gateway's hidden iframe isn't blocked. Read when a fragment silently fails to load or you're setting security headers.
- `references/piercing-and-performance.md` — piercing internals (`sec-fetch-dest` hard-nav, `data-piercing` styling, HTMLRewriter), caching (`Vary`, stub TTL, `forwardFragmentHeaders`), `mode:production`, route specificity. Read for perf/piercing/CLS work.
- `references/frameworks-astro.md` — **verified** Astro recipe: embedding, `<ClientRouter />`, the head-accumulation bug (#297), and smooth transitions without ClientRouter.

Scripts (run, don't read): `scripts/scaffold-fragment.mjs` (generate a Vite fragment +
gateway snippet); `scripts/doctor.mjs` (static-check a project).

**Official slash commands** (PR #294, ship with the package under `.claude/commands/`):
`/web-fragments:init-fragment | gateway-config | debug-fragment | fragment-test |
migrate-to-fragments | fragment-csp | fragment-perf` — explicit task runners. They complement
this skill: the skill auto-triggers and supplies verified knowledge; the commands run a
specific job on request. Use them when the user invokes one or wants a guided scaffold/audit.

## Top gotchas (full list: references/troubleshooting.md)

- **Wrong middleware import.** No `web-fragments/middleware`. Web = `web-fragments/gateway`; Node = `web-fragments/gateway/node`.
- **`registerFragment`, not `register`.**
- **Asset path ↔ routePattern mismatch** — #1 cause of 404'd assets / blank fragments. Fragment asset dir and gateway asset `routePattern` must share the prefix.
- **Gateway is mandatory** — no server-less mode yet (#278).
- **`nodenext`** type resolution may fail (#284); **Angular host** needs `outputMode:"server"` + `externalDependencies` (#280).
- **`:root` is dead inside a fragment; use `:host`.** Host `:root` vars + inherited props (font/color) flow in; selector rules don't. → `css-and-styling.md`.
- **`X-Frame-Options: DENY` on the fragment endpoint silently kills it** — it blocks the gateway's hidden iframe. Allow framing (`frame-ancestors 'self' <gateway-origin>`). → `csp-and-iframe.md`.
- **Piercing fires only on hard navigation** (`sec-fetch-dest: document`); set `mode:'production'` when deployed; register specific routePatterns before broad ones (first-match-wins). → `piercing-and-performance.md`.
