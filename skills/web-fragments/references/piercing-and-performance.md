# Piercing & Performance

All claims below are **confirmed in the gateway source** (`src/gateway/middleware/web.ts`,
`fragment-gateway.ts`, `web-fragment-host.ts`) unless marked.

## Piercing (SSR composition)

Piercing server-side-renders the fragment's markup into the app-shell response, removing the
client round-trip on first load. It's the primary perf feature; `piercing` defaults to `true`.

- **Fires only on hard navigation:** the gateway pierces when `sec-fetch-dest: document`
  (`fetchingToPierce` in web.ts). Soft navs (fetch/XHR) take the non-pierced path. So piercing
  helps full-page loads, not in-app fetches.
- **HTML rewrite:** the gateway rewrites the fragment's `<html>`/`<head>`/`<body>` to
  `<wf-html>`/`<wf-head>`/`<wf-body>` (web.ts). The fragment must return **real HTML with
  those tags** and `content-type: text/html`.
- **Pre-pierce styling (avoid CLS):** the gateway emits
  `<web-fragment-host … data-piercing="true">`. Position it via `piercingStyles` targeting
  `web-fragment-host[data-piercing="true"]` (e.g. `position`, `z-index`) so it lands in the
  right place before portaling; the attribute is removed after portaling (web-fragment-host.ts).
- **Missing placeholder = layout shift:** if the app shell lacks a `<web-fragment
  fragment-id="…">` on the matching route, the gateway appends the host at the end of
  `<body>` as a fallback — piercing still works but the fragment appears out of place.
- **HTMLRewriter engine** *(per PR #294 / maintainers):* native on Cloudflare Workers
  (streams the combined response before the fragment fetch finishes); WASM on Node buffers the
  whole fragment first — a latency limitation.

## Caching & headers

- **`Vary: sec-fetch-dest`** is appended to gateway responses to prevent BFCache serving the
  wrong (pierced vs not) variant (web.ts). Don't let a proxy strip it.
- **iframe stub** is cached `max-age=3600, public, stale-while-revalidate=31536000` by default
  (web.ts). Only override via `iframeHeaders` if you need a shorter TTL.
- **Forward fragment cache headers:** `forwardFragmentHeaders: ['cache-control']` so the
  fragment's `Cache-Control` reaches the combined response (else the host's is used). Same
  mechanism for other fragment response headers the host needs (`Set-Cookie`, custom).

## `mode: 'production'` vs `'development'`

Set `mode: 'production'` when deployed. Development mode disables compression passthrough to
work around a miniflare bug that mangles `content-length` on compressed/chunked responses
(cloudflare/workers-sdk#6577, web.ts) and is otherwise dev-oriented (verbose errors). Wrong
`mode` in prod = avoidable overhead / leaked error detail.

## Route-pattern specificity

`matchRequestToFragment` returns the **first** matching pattern — there is **no specificity
ordering yet** (explicit `// TODO: path matching needs to take pattern specificity into
account` in fragment-gateway.ts). Consequences:
- **List more specific patterns first**; an overly broad `/:_*` earlier will shadow them and
  also try to serve routes that should fall through to the app shell.
- `/products` does **not** match `/products/123` (path-to-regexp v6) — use `/products/:_*`.

## onSsrFetchError

- Without an `onSsrFetchError` handler, a failed fragment fetch falls back to the gateway's
  default (`defaultOnSsrFetchError`, `overrideResponse: false`) — a generic error response to
  the user. Provide one to serve a friendly fallback.
- `overrideResponse: true` makes the returned `response` **replace the entire page** (the
  middleware `throw`s it) — useful for auth redirects. Return `content-type: text/html`.
