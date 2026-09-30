# Host (Shell) Integration Recipes

Wiring the gateway into the **host** per runtime. Every recipe assumes you bootstrapped the
client once (`initializeWebFragments()` at the earliest entry), placed `<web-fragment
fragment-id="…">`, and built a shared gateway module:

```ts
// gateway.ts
import { FragmentGateway } from 'web-fragments/gateway';
export const gateway = new FragmentGateway();
gateway.registerFragment({
  fragmentId: 'my-fragment',
  endpoint: process.env.MY_FRAGMENT_ENDPOINT ?? 'http://localhost:5173',
  routePatterns: ['/__wf/my-fragment/:_*', '/'],
});
```
Pick **Web (Fetch)** middleware OR **Node** middleware per server — never both.

## Express / Connect (Node)

```ts
import express from 'express';
import { getNodeMiddleware } from 'web-fragments/gateway/node';
import { gateway } from './gateway';

const app = express();
app.use(getNodeMiddleware(gateway, { mode: 'production' }));
// ... your existing routes / static serving AFTER the fragment middleware
app.listen(3000);
```
Register the fragment middleware **before** your catch-all/static handlers so fragment
asset + proxy requests are intercepted first.

## Cloudflare Pages

`functions/_middleware.ts` (Pages Functions run the Web middleware):
```ts
import { getWebMiddleware } from 'web-fragments/gateway';
import { gateway } from '../gateway';

const fragmentMiddleware = getWebMiddleware(gateway, { mode: 'production' });

export const onRequest: PagesFunction = async (context) => {
  return fragmentMiddleware(context.request, () => context.next());
};
```
Reference implementation: `web-fragments/web-fragments` repo →
`e2e/pierced-react/functions/_middleware.ts`.

## Cloudflare Workers

```ts
import { getWebMiddleware } from 'web-fragments/gateway';
import { gateway } from './gateway';

const fragmentMiddleware = getWebMiddleware(gateway, { mode: 'production' });

export default {
  async fetch(request, env, ctx) {
    return fragmentMiddleware(request, async () => {
      // your origin handler when no fragment route matches
      return new Response('Not found', { status: 404 });
    });
  },
};
```

## Vercel Edge Middleware

`middleware.ts` at project root:
```ts
import { getWebMiddleware } from 'web-fragments/gateway';
import { gateway } from './gateway';

export const config = { matcher: '/:path*' };
const fragmentMiddleware = getWebMiddleware(gateway, { mode: 'production' });

export default async function middleware(request: Request) {
  return fragmentMiddleware(request, () => fetch(request)); // fall through to origin
}
```

## Netlify Edge Functions

`netlify/edge-functions/web-fragments.ts`:
```ts
import { getWebMiddleware } from 'web-fragments/gateway';
import { gateway } from '../../gateway.ts';

const fragmentMiddleware = getWebMiddleware(gateway, { mode: 'production' });

export default async (request: Request, context) =>
  fragmentMiddleware(request, () => context.next());

export const config = { path: '/*' };
```

## Hono

```ts
import { Hono } from 'hono';
import { getWebMiddleware } from 'web-fragments/gateway';
import { gateway } from './gateway';

const app = new Hono();
const fragmentMiddleware = getWebMiddleware(gateway, { mode: 'production' });

app.use('*', async (c, next) => {
  return fragmentMiddleware(c.req.raw, async () => {
    await next();
    return c.res;
  });
});
```

## Angular (host)

Angular SSR hosts hit a known `htmlrewriter` resolution error during build (issue #280).
Fix in `angular.json` for the host app's build target:
```jsonc
{
  "outputMode": "server",
  "externalDependencies": [
    "web-fragments/gateway",
    "web-fragments/gateway/node",
    "htmlrewriter"
  ]
}
```
Then add the Node or Web middleware in your Angular SSR server entry depending on your
deploy target (Express adapter → `getNodeMiddleware`; edge → `getWebMiddleware`).

## Next.js (host)

> ⚠️ **Open bug: Next.js does not hydrate fragments** (issue #290) — SSR piercing renders but
> client hydration is unreliable. Try `piercing: false` to isolate; track #290 and confirm
> against the latest release before committing to a Next.js host.

Wiring (`middleware.ts`, Edge runtime) follows the Vercel pattern above with `getWebMiddleware`.

## Vite SPA dev server

For a pure SPA host in dev, run the gateway as a Vite plugin/connect middleware using the
Node middleware (Vite's dev server is connect-based):
```ts
// vite.config.ts
import { getNodeMiddleware } from 'web-fragments/gateway/node';
import { gateway } from './gateway';

export default {
  plugins: [{
    name: 'web-fragments-gateway',
    configureServer(server) {
      server.middlewares.use(getNodeMiddleware(gateway, { mode: 'development' }));
    },
  }],
};
```

## Cross-cutting rules
- The **host-route** `routePattern` must match the URL where `<web-fragment>` is placed,
  or the gateway never serves that fragment.
- The **asset** `routePattern` prefix must match the fragment build's asset output dir.
- One `FragmentGateway` instance can hold many `registerFragment` calls — register every
  fragment the host embeds.
- Pick Web **or** Node middleware to match the runtime; importing `gateway/node` into an
  edge/worker bundle will fail.
