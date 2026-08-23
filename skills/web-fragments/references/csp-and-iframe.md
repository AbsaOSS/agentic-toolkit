# CSP & iframe framing

The gateway runs each fragment's JS in a **hidden iframe** (the reframed context) whose `src`
points at the fragment. So the fragment must be **framable** by the host/gateway origin. Get
this wrong and the fragment **silently fails** — the iframe just never loads. (Source: the
reframed loader explicitly warns when the iframe response carries `X-Frame-Options: deny`,
`reframed.ts`.)

## Rules

**Fragment endpoint** (the thing being framed) must NOT block framing:
- ❌ `X-Frame-Options: DENY` → change to `SAMEORIGIN` or remove.
- ❌ `Content-Security-Policy: frame-ancestors 'none'`.
- ✅ `Content-Security-Policy: frame-ancestors 'self' <gateway-origin>` (allow the host to frame it).
- Cloudflare Pages fragment routes (`public/_headers`):
  ```
  /<fragment-route>/*
    Content-Security-Policy: frame-ancestors 'self' <gateway-origin>
    X-Frame-Options: ALLOWALL
  ```

**Host / app shell** CSP must allow the fragment to be embedded + run:
```
Content-Security-Policy:
  default-src 'self';
  frame-src 'self' <fragment-origin>;
  script-src 'self' 'unsafe-inline';   /* SSR frameworks often inject inline scripts; use nonces if you can */
```
If a fragment loads assets from a CDN, add those origins to `script-src` / `style-src`.

## `iframeHeaders` ≠ fragment-content headers

`FragmentConfig.iframeHeaders` sets headers on the **iframe stub** response — the tiny
document the gateway returns for the iframe init request (`sec-fetch-dest` is normalized to
`empty` for that fetch) — **not** on the fragment's content response. Use it for auth/tracing
headers on the stub only. Header names are normalized to HTTP-Header-Case
(`fragment-gateway.ts`). For CSP/X-Frame-Options on the *content*, set them on the fragment
endpoint itself (above).

## Quick check
- Fragment blank, no errors? Inspect the hidden `wf:<id>` iframe in dev tools and check the
  fragment endpoint's response headers for `X-Frame-Options`/`frame-ancestors`.
- `scripts/doctor.mjs` flags an `X-Frame-Options: DENY` set in project source.
