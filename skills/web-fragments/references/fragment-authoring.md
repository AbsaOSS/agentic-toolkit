# Authoring a Fragment App

A **fragment** is just a standalone web app served over HTTP. It does not import
`web-fragments` itself — the host embeds it. The only fragment-side concern is making its
**assets resolve under a unique, predictable path** so the gateway can route them on the
host origin without colliding with the host's or other fragments' assets.

The canonical example is `web-fragments/party-button-fragment` (a Vite + vanilla TS app
that shoots confetti). Its shape:

```
party-button-fragment/
├── index.html          # plain HTML, loads /src/main.ts
├── src/main.ts         # the fragment's client code
├── public/             # static assets
├── package.json        # vite + wrangler (deployed to Cloudflare, but any host works)
└── vite.config.ts      # <-- the important part: assetsDir
```

`index.html` is unremarkable:
```html
<!doctype html>
<html lang="en">
  <head><meta charset="UTF-8" /><title>Web Fragment Party Button!</title></head>
  <body>
    <button>🎉 Let's party! 🥳</button>
    <script type="module" src="/src/main.ts"></script>
  </body>
</html>
```

## The one rule that matters: unique asset path

The fragment must emit its build assets under a unique directory so they can be addressed
as `/__wf/<unique-id>/…` on the host origin. With Vite:

```ts
// vite.config.ts
import { defineConfig } from 'vite';

export default defineConfig({
  build: {
    assetsDir: '__wf/dev.web-fragments.demos.party-button/', // unique per fragment
  },
});
```

Then in the host gateway the **asset routePattern uses the same prefix**:
```ts
gateway.registerFragment({
  fragmentId: 'party-button',
  endpoint: 'https://party-button.example.dev',
  routePatterns: [
    '/__wf/dev.web-fragments.demos.party-button/:_*', // ← matches assetsDir above
    '/',                                              // host route(s)
  ],
});
```
If these two prefixes drift apart, the host page loads but the fragment's JS/CSS 404 and
the fragment appears blank. This is the single most common authoring mistake.

**Naming the unique id:** use a reverse-DNS-ish slug you control, e.g.
`__wf/<org>.<app>.<fragment>/`. It only needs to be globally unique across fragments
embedded in the same host.

## Tech stack & framework choice
Any stack works — vanilla, React, Angular, Qwik, full-stack frameworks. The fragment can
have its own nested routes, layouts, data fetching, and form handling. Constraints:
- Serve real HTML on the fragment's routes (the gateway fetches SSR markup for piercing).
- Keep asset URLs under the unique prefix (configure the bundler's asset/base path).
- For frameworks with a configurable base/public path, set it to the same `__wf/<id>/`.

## Deploying a fragment
Deploy anywhere that serves the built HTML + assets over HTTP: Cloudflare
(`wrangler deploy`), a Node server, static host + edge, etc. The party-button example uses:
```jsonc
// package.json scripts
{
  "dev": "vite",
  "build": "tsc && vite build",
  "preview": "vite build && vite preview",
  "deploy": "pnpm build && wrangler deploy"
}
```
The host references the deployed URL via `FragmentConfig.endpoint`. Fragment and host
deploy and version **independently** — that is the whole point of the architecture.

## Local dev
Run the fragment on its own port (`vite` → e.g. `http://localhost:5173`) and point the
host gateway's `endpoint` at it with `mode: 'development'`. Use `scripts/scaffold-fragment.mjs`
to generate this skeleton instead of hand-writing it.
