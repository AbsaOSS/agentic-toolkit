# Web Fragments API Reference (v0.8.x)

Source of truth: the `web-fragments` package `exports` map and TypeScript sources.
This file mirrors them so you never need to open `node_modules` source.

## Contents
- [Entry points](#entry-points)
- [Client elements](#client-elements)
- [`FragmentGateway`](#fragmentgateway)
- [`FragmentConfig`](#fragmentconfig)
- [`FragmentGatewayConfig`](#fragmentgatewayconfig)
- [Middleware](#middleware)
- [`FragmentMiddlewareOptions`](#fragmentmiddlewareoptions)
- [Route patterns](#route-patterns)
- [Deprecations](#deprecations)

## Entry points

```jsonc
// node_modules/web-fragments/package.json -> exports
{
  ".":              "./dist/elements.js",        // client elements
  "./gateway":      "./dist/gateway.js",         // gateway + web middleware
  "./gateway/node": "./dist/gateway/node.js"     // node middleware
}
```

| Specifier | Named exports |
|---|---|
| `web-fragments` | `initializeWebFragments`, `WebFragment`, `WebFragmentHost` |
| `web-fragments/gateway` | `FragmentGateway`, `getWebMiddleware`, type `FragmentConfig`, type `FragmentMiddlewareOptions` |
| `web-fragments/gateway/node` | `getNodeMiddleware` |

There is intentionally **no** `web-fragments/middleware` and **no** `web-fragments/client`.
If you see those in a doc or blog, they are stale.

## Client elements

```ts
import { initializeWebFragments } from 'web-fragments';
initializeWebFragments();
```
`initializeWebFragments()` calls `customElements.define('web-fragment', WebFragment)` and
`customElements.define('web-fragment-host', WebFragmentHost)`. Call it once, as early as
possible in the host's client bootstrap (before any `<web-fragment>` is parsed/connected).

### `<web-fragment>`
| Attribute | Required | Meaning |
|---|---|---|
| `fragment-id` | **yes** | Matches a registered `FragmentConfig.fragmentId`. Missing → throws `The <web-fragment> is missing fragment-id attribute!` |
| `src` | no | Optional initial route/URL for this fragment instance. |

On `connectedCallback` the element looks for an existing pierced `<web-fragment-host
fragment-id="…">` (server-rendered) and adopts it; otherwise it creates one. A mismatched
`fragment-id` between `<web-fragment>` and a contained `<web-fragment-host>` throws.

### `<web-fragment-host>`
Internal element that owns the fragment's shadow root + reframed iframe context. It is
produced by piercing (server) or by `<web-fragment>` itself (client). You normally never
author it directly. Exposed mainly so frameworks/tests can reference the class.

## `FragmentGateway`

```ts
import { FragmentGateway } from 'web-fragments/gateway';

class FragmentGateway {
  constructor(config?: FragmentGatewayConfig);
  registerFragment(fragmentConfig: FragmentConfig): void;
  matchRequestToFragment(urlPath: string, requestFragmentId?: string): FragmentConfig | null;
}
```
- `registerFragment` — register one fragment. Call once per fragment. **Not** `register`.
- `matchRequestToFragment` — used internally by the middleware to route a request to a
  fragment; useful in custom middleware / tests.

## `FragmentConfig`

```ts
interface FragmentConfig {
  /** Unique id; must equal the <web-fragment fragment-id>. */
  fragmentId: string;                              // REQUIRED

  /** path-to-regexp v6 patterns this fragment serves (assets + host routes). */
  routePatterns: string[];                         // REQUIRED

  /** Fragment app origin URL, or a fetch-compatible function. */
  endpoint: string | typeof fetch;                 // REQUIRED

  /** Server-side pierce the fragment into the shell. Default: true. */
  piercing?: boolean;

  /** Classes applied to the fragment before piercing for a seamless visual swap.
   *  Recommended selector: :not(web-fragment) > web-fragment-host[fragment-id="<id>"] */
  piercingClassNames?: string[];

  /** Fragment response headers to forward into the combined gateway response. */
  forwardFragmentHeaders?: string[];

  /** Extra headers on the iframe STUB response (the init doc), NOT the fragment content.
   *  Names normalized to HTTP-Header-Case. For CSP/X-Frame-Options on content, set them on
   *  the fragment endpoint itself. See csp-and-iframe.md. */
  iframeHeaders?: Record<string, string>;

  /** Fallback when fetching the fragment's SSR markup fails (4xx/5xx/throw). Without it, a
   *  failure falls back to a generic gateway error response. With overrideResponse:true the
   *  returned response REPLACES the whole page (e.g. auth redirect). */
  onSsrFetchError?: (
    req: Request,
    failedResOrError: Response | Error,
  ) => SSRFetchErrorResponse | Promise<SSRFetchErrorResponse>;

  // --- deprecated ---
  /** @deprecated use endpoint */            upstream?: string;
  /** @deprecated use piercingClassNames */  prePiercingClassNames?: string[];
}

interface SSRFetchErrorResponse {
  response: Response;
  overrideResponse?: boolean;
}
```

### About `routePatterns`
You almost always register **two kinds** of patterns:
1. **Asset pattern** — a unique prefix the fragment serves its JS/CSS/static files under,
   e.g. `'/__wf/<unique>/:_*'`. Must line up with the fragment build's asset output dir.
2. **Host route pattern(s)** — the URL(s) in the *host* app where the fragment is mounted,
   e.g. `'/'`, `'/dashboard/:_*'`. Must match where `<web-fragment>` is placed.

`/x` does **not** match `/x/123` — use `/x/:_*` for sub-paths. Matching returns the **first**
matching pattern (no specificity ordering yet — `matchRequestToFragment` TODO), so register
**specific patterns before broad ones**. Details: `piercing-and-performance.md`.

## `FragmentGatewayConfig`

```ts
interface FragmentGatewayConfig {
  /** Global CSS injected to style fragments during piercing. */
  piercingStyles?: string;
  /** @deprecated use piercingStyles */
  prePiercingStyles?: string;
}
```
Passing `prePiercingStyles` logs a red deprecation warning at runtime. Use `piercingStyles`.

## Middleware

```ts
// Web / Fetch runtimes:
import { getWebMiddleware } from 'web-fragments/gateway';
function getWebMiddleware(
  gateway: FragmentGateway,
  options?: FragmentMiddlewareOptions,
): (request: Request, next: () => Promise<Response>) => Promise<Response>;

// Node (Express/Connect) runtimes:
import { getNodeMiddleware } from 'web-fragments/gateway/node';
function getNodeMiddleware(
  gateway: FragmentGateway,
  options?: FragmentMiddlewareOptions,
): (req, res, next) => void;
```
The node middleware internally adapts Node req/res to the Web `Request`/`Response` the
gateway works with (`web-to-node-adapter`). Use the entry point that matches your runtime;
do not import the node one into an edge/worker build.

## `FragmentMiddlewareOptions`

```ts
interface FragmentMiddlewareOptions {
  additionalHeaders?: HeadersInit;          // headers added to gateway responses
  mode?: 'production' | 'development';       // default 'development'
}
```
Set `mode: 'production'` for deployed builds; `development` enables dev-friendly behavior
(e.g. a fallback reframed HTML document) and more verbose handling.

## Deprecations (rewrite on sight)

| Deprecated | Use instead |
|---|---|
| `FragmentConfig.upstream` | `FragmentConfig.endpoint` |
| `FragmentConfig.prePiercingClassNames` | `FragmentConfig.piercingClassNames` |
| `FragmentGatewayConfig.prePiercingStyles` | `FragmentGatewayConfig.piercingStyles` |
| import `web-fragments/middleware` | `web-fragments/gateway` (web) / `web-fragments/gateway/node` (node) |
