# Troubleshooting & Known Issues (v0.8.x)

Read this FIRST when a fragment is broken. Each entry: symptom → cause → fix. The
issue numbers reference github.com/web-fragments/web-fragments/issues — check there for
the current status, since this is a fast-moving beta.

## Module / import errors

### `Cannot find module 'web-fragments/middleware'`
**Cause:** stale docs. That entry point never existed. **Fix:** import web middleware from
`web-fragments/gateway` (`getWebMiddleware`), node middleware from
`web-fragments/gateway/node` (`getNodeMiddleware`).

### `gateway.register is not a function`
**Cause:** the method is `registerFragment`, not `register`. **Fix:** rename the call.

### Types don't resolve under `moduleResolution: "nodenext"` (issue #284)
**Symptom:** TS can't find the library's type declarations when the consumer uses
`nodenext`/`node16` resolution. **Fix options:** set the host tsconfig to
`"moduleResolution": "bundler"` if your toolchain allows; or add a local module
declaration shim; or pin/upgrade to a release where the `exports` `types` conditions are
fixed. Verify the installed version's `package.json` `exports` includes `types` for each
entry. Track issue #284.

## Build / bundler errors

### `htmlrewriter` error when host is Angular (issue #280, resolved via config)
**Fix** in the host app's `angular.json` build target:
```jsonc
"outputMode": "server",
"externalDependencies": ["web-fragments/gateway", "web-fragments/gateway/node", "htmlrewriter"]
```
Marking those as external stops the Angular bundler from trying to bundle the
WASM-backed `htmlrewriter` dependency.

### Edge/worker build fails importing node middleware
**Cause:** `web-fragments/gateway/node` pulls in Node APIs. **Fix:** in edge/worker
runtimes import `getWebMiddleware` from `web-fragments/gateway` instead.

## Runtime: fragment doesn't appear

### Blank fragment / asset 404s
**Cause #1 (most common):** the fragment build's asset directory and the gateway's asset
`routePattern` prefix don't match. **Fix:** align Vite `build.assetsDir` (or the
framework's base/public path) with the `/__wf/<id>/:_*` pattern. See
`fragment-authoring.md`.
**Cause #2:** the **host-route** `routePattern` doesn't match the URL where
`<web-fragment>` is placed. **Fix:** add/adjust a pattern for that route.

### `The <web-fragment> is missing fragment-id attribute!`
**Fix:** add `fragment-id` to the element; it must equal a registered `fragmentId` —
**case-sensitive exact match** (`UserProfile` ≠ `user-profile`).

### Element does nothing / not upgraded
**Cause:** `initializeWebFragments()` not called, or called after the element connected.
**Fix:** call it once, as early as possible in the host client bootstrap.

### Fragment silently fails to load (no error), hidden iframe never loads
**Cause:** the fragment endpoint responds with `X-Frame-Options: DENY` (or
`frame-ancestors 'none'`), blocking the hidden iframe the gateway uses as the JS context.
**Fix:** remove it / use `SAMEORIGIN`, and allow framing via
`frame-ancestors 'self' <gateway-origin>`. Full model: `csp-and-iframe.md`.

### Route matches too much / wrong fragment served / sub-paths 404
**Cause:** path-to-regexp v6 — `/products` does **not** match `/products/123` (use
`/products/:_*`). Also the gateway returns the **first** matching pattern (no specificity
ordering yet), so a broad pattern can shadow a specific one. **Fix:** use `:_*` for
sub-paths; register **specific patterns before broad ones**. See `piercing-and-performance.md`.

### Fragment renders but in the wrong place / layout shift on first paint
**Cause:** the app shell lacks a `<web-fragment fragment-id="…">` on the pierced route, so the
gateway appends the host at the end of `<body>` as a fallback; or `piercingStyles` doesn't
position `web-fragment-host[data-piercing="true"]`. **Fix:** add the placeholder on the route
and style the pre-pierce host. See `piercing-and-performance.md`.

### Gateway not detected / no error surfaced (issue #288)
There is currently no built-in custom error handling when the gateway middleware isn't
present in the request path. **Mitigation:** verify the middleware is installed and ordered
before catch-all routes; add your own guard/logging until first-class handling lands.

## Runtime: SSR / hydration / streaming

### Next.js fragments don't hydrate (issue #290, OPEN bug)
Server piercing may render but client hydration is unreliable on Next.js hosts. **Mitigate:**
try `piercing: false` to isolate piercing vs hydration; track issue #290; don't promise full
Next.js support without testing the current release.

### JS assets truncated mid-stream via `getNodeMiddleware` (issue #293, OPEN bug)
**Symptom:** fragment JS cut off / parse errors when proxied through the Node middleware,
caused by a `Content-Length`/`Content-Encoding` mismatch after undici transparently
decompresses the upstream response. **Mitigations:** prefer the Web middleware where the
runtime allows; ensure the fragment origin's compression headers are consistent; track
issue #293. Suspect this when assets load fine directly from the fragment origin but break
when proxied through a Node host.

### Fragment styles accumulate / old pages' CSS bleeds into new ones during SPA nav
**Symptom:** a fragment that does client-side routing (e.g. Astro `<ClientRouter />`) and
injects per-route `<style>`/`<link>` into `<head>` leaves the previous route's styles
behind. They pile up node-by-node on every navigation and earlier rules keep applying.
**Cause:** reframed relocates head `<style>`/`<link>` out of `wf-head` to apply them inside
the shadow tree, so the framework's head-swap (which cleans `document.head` = `wf-head`)
never removes them. **Fix:** keep the fragment's `<head>` CSS stable across navigations
(one shared stylesheet loaded once; scope per-page rules under a body class), or drop
client-side routing for that fragment. Tracked upstream as
[#297](https://github.com/web-fragments/web-fragments/issues/297). Full verified analysis +
repro: `references/frameworks-astro.md` → "Bug: head styles accumulate".

### Styles bleed between fragment and host
Should not happen — fragments live in a shadow root. If it does, confirm
`initializeWebFragments()` ran and the fragment is actually inside `<web-fragment-host>`
(inspect the shadow root in dev tools). Pre-pierce flashes can be smoothed with
`piercingClassNames` / `FragmentGatewayConfig.piercingStyles`.

## Architecture constraints (not bugs)

- **The gateway is mandatory** (issue #278). There is no server-less mode yet; a
  service-worker gateway is in progress. Fragments cannot federate without it.
- **Each fragment gets its own JS context** (`wf:<fragment-id>`, a hidden iframe). This is
  by design — it's how isolation works. Removing the `<web-fragment>` element tears the
  context down and frees its memory.
- **Passing synchronous host→fragment inputs** is not yet supported (feature request
  #289). Communicate via shared DOM, navigation, URL, or `postMessage`-style channels.

## Fast diagnosis checklist
1. Run `scripts/doctor.mjs <project>` — catches import path, `register` vs
   `registerFragment`, asset/routePattern mismatch, missing middleware.
2. Dev tools: is there a `wf:<id>` iframe context? Is the DOM inside a shadow root?
3. Network tab: do `/__wf/<id>/…` asset requests 200 on the **host** origin?
4. Confirm the installed version (`node_modules/web-fragments/package.json`) and its
   `exports` map before trusting any external doc.
