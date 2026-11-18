# Core path: any app without an adapter

Use for every app that isn't Angular: React, Vue, Svelte, Solid, Lit, plain TypeScript or
JavaScript. The app installs the framework-free core, `@absaoss-cps/ui-watchtower`, and creates
one engine itself. React and Vue add `react.md` / `vue.md` on top of this file, for where things
go and the router binding. The API is in `ui-watchtower-api.md` (the "API" below).

## Step 1 · Detect — also check

- **A build that resolves npm packages** (Vite, webpack, Rollup, esbuild, a framework CLI). The
  package ships ES modules only. A page that loads scripts without a build → stop and ask.
- **TypeScript's `moduleResolution`**: `bundler`, `node16` or `nodenext` read the package's
  `exports`, which the `/rum` and `/rxjs` entry points need. With `node` / `node10`, those imports
  don't resolve — tell the user; changing it is their call.
- **Entry module** (`src/main.ts`, `src/main.tsx`, `src/index.js`) and how the app reads its
  build-time config (`import.meta.env`, `process.env`, an `environment` file) — the identity and
  the off switch come from there.
- **RxJS**: only if the app already uses it is `/rxjs` worth anything. Never install it for
  telemetry.

## Step 2 · Install

```bash
npm view @absaoss-cps/ui-watchtower@latest peerDependencies   # the aws-rum-web range
npm install @absaoss-cps/ui-watchtower@latest
npm install "aws-rum-web@<that range>"   # only if THIS realm sends to RUM (standalone app or shell)
```

The core has no framework peers, so the latest always fits. Never install the Angular adapter
here.

## Step 3 · The engine module

One module creates everything once, at startup; app code imports `telemetry` from it. Never one
engine per component, and never created inside a component, hook or render function. Don't wrap
it in a service or facade either: code uses `telemetry.scenarios`, `telemetry.bi` and
`telemetry.logging` directly.

```ts
// src/telemetry/telemetry.ts
import './telemetry.schema'; // the vocabulary (Step 4)
import { uwtCreateTelemetry, UwtNoopLogApiProvider } from '@absaoss-cps/ui-watchtower';
import { UwtRumTelemetrySink } from '@absaoss-cps/ui-watchtower/rum';
import { AppRumCredentialsProvider } from './rum-credentials.provider';

// From the app's own config (Vite's import.meta.env here); derive nothing from browser globals
// unguarded (server rendering).
const identity = {
  application: 'my-app',
  environment: import.meta.env.MODE, // e.g. 'dev' | 'qa' | 'prod'
  version: import.meta.env.VITE_APP_VERSION
};

/** Read once, at startup: the same value goes to everything created here. */
const enabled = true;

/** The RUM destination; exported for page views (Step 6). */
export const destination = new UwtRumTelemetrySink({
  identity,
  credentialsProvider: new AppRumCredentialsProvider(),
  enabled
});
destination.init(); // never awaited: a slow broker never delays the page

export const telemetry = uwtCreateTelemetry({
  identity,
  destination,
  logApi: new UwtNoopLogApiProvider(), // or new AppLogApiProvider() — see below
  enabled
});
```

Import it from the entry module (`import './telemetry/telemetry';`) so the engine exists before
the first render and the first navigation. `uwtCreateTelemetry` throws when `identity`,
`destination` or `logApi` is missing — a wiring error, fixed in the wiring, never caught.

**Destination by role** (SKILL.md Step 3):

| Role | `destination` |
|---|---|
| Standalone app, sends to RUM | `UwtRumTelemetrySink` as above, with `init()` |
| Shell hosting fragments | the same, plus a `UwtTelemetryBroadcastHost` — `micro-frontends.md` |
| Fragment inside a shell | `UwtBroadcastTelemetrySink` — `micro-frontends.md` |
| RUM not available yet | `new UwtNoopTelemetrySink()`: no `/rum` import, no credentials, no `init()` |
| Own backend | a class extending `UwtTelemetrySink` (API §8) |

**Log provider** — the engine always needs one. With a log backend: `new AppLogApiProvider()`
from `assets/log-api.provider.ts` (it uses `fetch`; use the app's HTTP client instead if that is
what adds the backend's auth), and declare logger names. Without one: `new
UwtNoopLogApiProvider()`; don't use `telemetry.logging` and don't declare `UwtLoggerNames`.

**Overrides** (`scenarios`, `bi`, `logging`, `redaction`) — none at first; add one only for a
stated reason, in a comment. In development, `report: uwtConsoleReporter` (API §10) prints what
telemetry skips or drops (the Angular adapter does this by itself); pass it only in development
builds.

**Off in some environments** (only when the user asks; SKILL.md Step 3): set `enabled` from the
app's config and pass it to the engine, the RUM sink and, in a shell or fragment, the broadcast
classes and the connection. Everything else stays as it is.

**Credentials**: `new AppRumCredentialsProvider()` from `assets/rum-credentials.provider.ts`. It
uses `fetch`; use the app's HTTP client instead if that is what adds the broker's auth.

**User identity** (only with sign-in): `telemetry.setUserId(opaqueId)` where sign-in completes
and `telemetry.setUserId(undefined)` on sign-out — or from the auth state stream, initial
`undefined` included. A fragment leaves this to the shell.

**Server rendering** (Next.js, Nuxt, Remix, SvelteKit, Astro…): the module can load on the server
— the core touches no browser global when imported, and the RUM sink never starts without a page
— but telemetry is called only from code that runs in the browser (effects, `onMounted`, event
handlers), so nothing is recorded while rendering on the server.

**`dispose()`** — an app's engine lives as long as the page: don't dispose it. Only a realm that
goes away while the page stays (a fragment the shell unmounts) disposes: the engine, then what it
created for it (`micro-frontends.md`).

## Step 6 · Route navigation

Copy `assets/route-navigation-tracker.ts` next to the schema and create the tracker once, in its
own module:

```ts
// src/telemetry/route-navigation.ts
import { RouteNavigationTracker } from './route-navigation-tracker';
import { destination, telemetry } from './telemetry';

export const navigationTracker = new RouteNavigationTracker({
  startScenario: (options) => telemetry.scenarios.start(options),
  // Only where RUM is the destination (else drop it and the `destination` import): page views
  // under the route template.
  recordPageView: (route) => destination.recordPageView(route)
});
```

Then bind the router: React Router → `react.md`, Vue Router → `vue.md`.

**Other routers** (Svelte, Solid, TanStack, a meta-framework's own router…): write a small binding
on the router's navigation events, with `assets/route-navigation.vue.ts` as the model — `start(id)`
when a navigation starts, `recognized(id, template)` once its route matched, then exactly one of
`end`, `redirected`, `cancel`, `skip` or `fail` (each documented in the tracker). It needs the
route **template** (`/customers/:id`). A router that exposes only the resolved path, or no
navigation events: skip this step and record no page views — keep `disableAutoPageView: true`,
since automatic ones would send the resolved paths — and say so in the hand-over. Never send
resolved paths.

## Step 7 · Tests

Specs that import code using the engine get a test engine from one mock of the engine module in
the test setup file, so no spec builds the real destination (its `init()` would call the
broker). Mirror the module's exports:

```ts
// src/test-setup.ts — listed in the test runner's `setupFiles`
vi.mock('./telemetry/telemetry', async () => {
  const { uwtCreateTelemetry, UwtNoopLogApiProvider, UwtNoopTelemetrySink } =
    await import('@absaoss-cps/ui-watchtower');
  // A no-op destination with the RUM sink's page-view method, which the route tracker calls.
  class TestSink extends UwtNoopTelemetrySink {
    recordPageView(): void {}
  }
  const destination = new TestSink();
  return {
    destination,
    telemetry: uwtCreateTelemetry({
      identity: { application: 'my-app-test', environment: 'test', version: '0.0.0' },
      destination,
      logApi: new UwtNoopLogApiProvider(),
      scenarios: { defaultTimeoutMs: 0 }, // no scenario timers left running in tests
      document: null // no page lifecycle in unit tests
    })
  };
});
```

To assert on what is sent, a spec builds its own engine with API §11's recording sink.

- The spec templates (SKILL.md Step 7) use Vitest's globals (`globals: true`; otherwise import
  `describe`, `it`, `expect`, `vi` from `vitest`).
- **Jest**: in the setup mock, use `jest.mock` with `require` inside the factory. Jest must also
  transform the package, which is ES modules only (`.mjs`): cover `\.mjs$` in `transform` and let
  `transformIgnorePatterns` through `node_modules/@absaoss-cps/`. Run one spec that imports it
  before going on.
