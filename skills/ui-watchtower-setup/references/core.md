# Core path: any app without an adapter

Use for every app that isn't Angular, whatever framework it uses, or none. The app installs the
framework-free core, `@absaoss-cps/ui-watchtower`, and creates one engine itself. Only Angular has
an adapter; for any other framework, call the core directly and don't build framework-specific
wrappers around it. The API is in `ui-watchtower-api.md` (the "API" below).

## Step 1 · Detect — also check

- **A build that resolves npm packages** (Vite, webpack, Rollup, esbuild, a framework CLI). The
  package ships ES modules only. A page that loads scripts without a build → stop and ask.
- **TypeScript's `moduleResolution`**: `bundler`, `node16` or `nodenext` read the package's
  `exports`, which the `/rum` and `/rxjs` entry points need. With `node` / `node10`, those imports
  don't resolve — tell the user; changing it is their call.
- **Entry module** (`src/main.ts`, `src/index.js`) and how the app reads its
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
import { version } from '../../package.json'; // see "Identity values" below
import { uwtCreateTelemetry, UwtNoopLogApiProvider } from '@absaoss-cps/ui-watchtower';
import { UwtRumTelemetrySink } from '@absaoss-cps/ui-watchtower/rum';
import { AppRumCredentialsProvider } from './rum-credentials.provider';

const identity = {
  application: 'my-app',
  environment: import.meta.env.MODE, // e.g. 'dev' | 'qa' | 'prod'
  version
};

/** Read once, at startup: the same value goes to everything created here. */
const enabled = true;

/** The RUM destination; exported for route-tracking page views (Step 6) and migration parity. */
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

**Identity values.** `uwtCreateTelemetry` throws when `application`, `environment` or `version` is
missing, so a value that is `undefined` at runtime blanks the page at startup. Take each from
something that exists in every build, and check the built app, not only the tests:

- `version`: the app's own `package.json` version, as above. Vite and esbuild bundle only the named
  field; with webpack, import the default (`import pkg from '../../package.json'`, then
  `pkg.version`); TypeScript needs `resolveJsonModule`. No `version` in `package.json`, or a
  monorepo where it isn't the release's: a constant kept in step by hand, with a comment saying so.
- `environment`: the build's own name. Vite's `import.meta.env.MODE` is `production` for every
  deployed build; if the app tells `qa` from `prod` some other way (a config file, a hostname map),
  use that. Don't read `import.meta.env.VITE_…` variables the app never defines: Vite leaves them
  `undefined`.
- Derive nothing from browser globals unguarded (server rendering).

Import it from the entry module (`import './telemetry/telemetry';`) so the engine exists before
the app renders anything. `uwtCreateTelemetry` throws when `identity`,
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

**Server rendering** (a framework that renders pages on the server): the module can load there
— the core touches no browser global when imported, and the RUM sink never starts without a page
— but telemetry is called only from code that runs in the browser (event handlers, code that runs
once the page has loaded), so nothing is recorded while rendering on the server.

**`dispose()`** — an app's engine lives as long as the page: don't dispose it. Only a realm that
goes away while the page stays (a fragment the shell unmounts) disposes: the engine, then what it
created for it (`micro-frontends.md`).

## Step 6 · Confirm the setup

The option the user chose in Step 1 (SKILL.md Step 6); app code reaches the engine by importing
`telemetry` from the engine module.

**Picked app telemetry** — call the API where the action happens, e.g. a BI event in the handler
of the app's main button:

```ts
import { telemetry } from './telemetry/telemetry';

exportButton.addEventListener('click', () => {
  telemetry.bi.track('my-app-export-clicked', { format: 'csv' });
  // …the existing handler, unchanged
});
```

For a scenario around a load the user waits for, use API §4, "With promises": start it before the
request, `complete` on the result, `fail` with only an error class and HTTP status, `cancel` when
the load is dropped.

**Temporary check** — one marked call in the entry module, right after the engine import, and its
entry in `UwtBIEventNames`:

```ts
// TEMPORARY: setup check — remove
import { telemetry } from './telemetry/telemetry';
telemetry.bi.track('my-app-setup-checked');
```

It runs at startup, so set the debug flag (`localStorage.setItem('debugBI', 'true')`) and reload
once. Remove both afterwards (SKILL.md Step 6).

**Route-navigation tracking** (only when the user chose it) — copy
`assets/route-navigation-tracker.ts` next to the schema and create the tracker once, in its own
module:

```ts
// src/telemetry/route-navigation.ts
import { RouteNavigationTracker } from './route-navigation-tracker';
import { destination, telemetry } from './telemetry';

export const navigationTracker = new RouteNavigationTracker({
  startScenario: (options) => telemetry.scenarios.start(options),
  // Only where RUM is the destination (else drop it and the `destination` import): page views
  // under the route template, with `disableAutoPageView: true` in the credentials provider.
  recordPageView: (route) => destination.recordPageView(route)
});
```

There is no ready binding outside Angular: write a small one on the app's router, called before
its first navigation. For each navigation, with an id of your choice, call `start(id)` when it
starts and `recognized(id, template)` once its route matched, then exactly one of:

- `end(id)` — it completed;
- `redirected(id)` — a guard or loader sent it elsewhere; the next `start` continues the same
  journey;
- `cancel(id, { reason, incomplete? })` — a newer navigation replaced it (`superseded`), or a guard
  said no (`incomplete: true`);
- `skip(id, reason)` — the router never ran it (the current URL again). A redirect that lands on the
  page the user is already on also ends here, after `redirected`; otherwise that navigation stays
  open until its 30 s timeout;
- `fail(id, error)` — it threw.

Each call is documented in the tracker; `assets/route-navigation.angular.ts` maps one router's
events completely. The binding needs the route **template** (`/customers/:id`): a router that
exposes only the resolved path, or no navigation events, can't use route tracking — say so and offer
the other two options. Never send resolved paths. Test the binding with the router in memory, one
test per outcome, as `route-navigation.angular.spec.ts` does for Angular.

## Step 7 · Tests

Specs that import code using the engine get a test engine from one mock of the engine module in
the test setup file (`setupFiles`), so no spec builds the real destination — the snippet is in API
§11, with how to assert on what is sent. With route-tracking page views, the tracker also calls
`destination.recordPageView`: give the mock destination one (a class extending
`UwtNoopTelemetrySink` with `recordPageView(): void {}`).

- The spec templates (SKILL.md Step 7) use Vitest's globals (`globals: true`; otherwise import
  `describe`, `it`, `expect`, `vi` from `vitest`).
- **Jest**: in the setup mock, use `jest.mock` with `require` inside the factory. Jest must also
  transform the package, which is ES modules only (`.mjs`): cover `\.mjs$` in `transform` and let
  `transformIgnorePatterns` through `node_modules/@absaoss-cps/`. Run one spec that imports it
  before going on.
