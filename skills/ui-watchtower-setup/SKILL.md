---
name: ui-watchtower-setup
description: >
  Installs and wires the @absaoss-cps/ngx-ui-watchtower telemetry library in an Angular app:
  destination per app role (AWS CloudWatch RUM, micro-frontend shell or fragment, no-op),
  credentials, log provider, typed name vocabulary, route-navigation tracking as proof, migration of
  a hand-written RumService, and tests. Use when asked to add, install, set up or wire
  ngx-ui-watchtower, UI telemetry or CloudWatch RUM in an Angular app, replace a RumService, or
  connect a micro-frontend shell or fragment. NOT for: instrumenting the app's own journeys or BI
  events (→ ui-watchtower-integration), dashboards, non-Angular apps.
license: Apache-2.0
compatibility: >
  Requires an Angular application within the peer range of a published
  @absaoss-cps/ngx-ui-watchtower release — the latest, or an older compatible one (checked at run
  time with npm view) — and npm registry access.
---

# ui-watchtower-setup

Sets up [`@absaoss-cps/ngx-ui-watchtower`](https://www.npmjs.com/package/@absaoss-cps/ngx-ui-watchtower)
in an existing Angular application: install, wire the providers for the app's role, declare the
name vocabulary, prove the pipeline with route-navigation tracking, test, verify.

**Scope:** infrastructure plus exactly one working scenario (route navigation). Measuring the app's
own journeys and interactions is the follow-up skill, `ui-watchtower-integration` — hand over to it at
the end (Step 9).

The library has three concerns: **scenarios** (did a user journey succeed, how long did it take),
**BI events** (did a meaningful thing happen) and **logs** (what happened in one run). Scenarios and
BI events go to **one destination** per JavaScript realm (normally AWS CloudWatch RUM). Logs always go
to the app's own log backend, never to the destination.

## Reference files — load on demand

| Load | When |
|---|---|
| [ngx-ui-watchtower-api](../shared/references/ngx-ui-watchtower-api.md) ([remote](https://github.com/AbsaOSS/agentic-toolkit/blob/master/skills/shared/references/ngx-ui-watchtower-api.md)) | Always, before writing code — exact imports, signatures, defaults, test harness |
| `references/rum-migration.md` | The app already sends RUM events itself (`aws-rum-web`, a `RumService`) |
| `references/micro-frontends.md` | The app hosts embedded fragments, or is a fragment inside a shell |

Templates in `assets/` are copied into the app and adapted: `telemetry.schema.ts`,
`rum-credentials.provider.ts`, `log-api.provider.ts`, `route-navigation-telemetry.service.ts`, and the
specs for the last two (`*.spec.ts`).

## Workflow

Copy this checklist and track progress:

```
- [ ] Step 1: Detect the app's shape (read-only)
- [ ] Step 2: Install the package
- [ ] Step 3: Wire providers for this realm's role
- [ ] Step 4: Declare the name vocabulary
- [ ] Step 5: Migrate an existing RUM integration (only if one exists)
- [ ] Step 6: Proof — route-navigation tracking
- [ ] Step 7: Update and add tests
- [ ] Step 8: Validate (build, tests, type-check, live debug output)
- [ ] Step 9: Hand over
```

### Step 1 · Detect (read-only)

Read before writing anything — extend the app, don't restructure it.

1. **Angular version.** Not Angular → stop. Compare the app's `@angular/core` and `rxjs` with the
   library's range from the registry, never from memory:
   `npm view @absaoss-cps/ngx-ui-watchtower@latest peerDependencies`.
   - Inside → install the latest version.
   - Older → the newest release whose peers fit (`npm view … versions`), pinned; none → stop.
   - Newer → stop and tell the user. Never `--force` or `--legacy-peer-deps`.
   - Note the chosen release's `aws-rum-web` range too — Step 2 installs within it.
2. **Package manager** — from the lockfile (`package-lock.json`, `yarn.lock`, `pnpm-lock.yaml`), a
   `packageManager` field, or `cli.packageManager` in `angular.json`. Use it for every install and
   script run; never default to npm.
3. **Bootstrap style** — standalone (`app.config.ts`, `bootstrapApplication`) or NgModule
   (`providers` in `app.module.ts`). Providers go in the same place either way.
4. **SSR** — `app.config.server.ts`, `server.ts`, `@angular/ssr`. Affects only code *you* write
   (Step 3); the library is SSR-safe.
5. **Test runner** — Jest, Karma or Vitest, and which specs build the root providers or render
   components that will inject telemetry services (they need providers in Step 7).
6. **Existing telemetry** — search for `aws-rum-web`, `recordEvent`, `recordPageView`, `pinUserId`,
   `addSessionAttributes`, a `RumService`, or another analytics SDK. If RUM is already wired, Step 5
   applies. If ngx-ui-watchtower is partly wired, run only the steps for what is missing; if
   nothing is, offer `ui-watchtower-integration`.
7. **Realm role** — standalone app, **shell** that embeds fragments (Web Fragments, Module
   Federation, iframes on the same origin), or **fragment** inside a shell. Look for
   `<web-fragment>`, fragment gateways, remote-entry config. A Module Federation remote loaded
   through `loadChildren`/`loadComponent` runs in the host's injector — give it no providers of
   its own.
8. **Router** — `provideRouter` / `RouterModule.forRoot`; note any `matcher` routes, or that there is
   no router at all (Step 6).
9. **Sign-in** — an auth service, OIDC/MSAL library or session store, and where sign-in and
   sign-out complete. Note which **opaque** user id it exposes (a subject or object id — never an
   email or username).

Ask the user only what the code cannot answer, in one message:

- The `application` name to report (unique per app and per fragment), if not obvious.
- **Log backend**: does one exist to send log records to (endpoint, existing service)?
- **RUM**: the endpoint that returns the RUM app-monitor config and short-lived AWS credentials
  (typically a backend "broker"), or whether RUM is not ready yet (→ `'noop'` for now).
- **User id**: if the app has sign-in but exposes no opaque id, which one to use — or skip it.

### Step 2 · Install

```bash
# npm / Yarn / pnpm — use the one detected in Step 1
npm install @absaoss-cps/ngx-ui-watchtower@latest   # or the pinned version chosen in Step 1
npm install "aws-rum-web@<range from Step 1>"   # only if THIS realm sends to RUM (standalone app or shell)
```

When `aws-rum-web` is installed, add `"allowedCommonJsDependencies": ["shimmer"]` to the app's build
options in `angular.json` (a CommonJS transitive dependency; otherwise every build warns). If a strict
`tsc` run fails inside `aws-rum-web`'s bundled `rrweb` typings, set `"skipLibCheck": true` in the
app tsconfig(s).

### Step 3 · Wire providers

`provideUwtTelemetry(identity)` registers **configuration only**. Every realm must also bind
**exactly one destination**; injecting a telemetry service without one fails at bootstrap with
`NG0201` — by design; fix the wiring, never add a fallback provider "to make it start". Two
different destinations also fail bootstrap.

**Destination by realm role:**

| Role | Destination | Also |
|---|---|---|
| Standalone app, sends to RUM | `provideUwtTelemetryRumSink()` (from `/rum`) | `UWT_RUM_CREDENTIALS_PROVIDER` → `assets/rum-credentials.provider.ts` |
| Shell hosting fragments | `provideUwtTelemetryRumSink()` | + `provideUwtTelemetryBroadcastHost(channelId)` + a log provider — `references/micro-frontends.md` |
| Fragment inside a shell | `provideUwtTelemetrySink('broadcast')` + lazy `UWT_BROADCAST_CHANNEL` factory | nothing else — `references/micro-frontends.md` |
| RUM not available yet | `provideUwtTelemetrySink('noop')` | explicit opt-out; everything runs, nothing ships; swap the one line later |
| Own backend | `provideUwtTelemetryDestination(MySink)` (a class extending `UwtTelemetrySink`) | see the API reference, "Custom destination" |

**Log provider:**

| App has a log backend? | Do |
|---|---|
| Yes | Implement `UwtLogApiProvider` from `assets/log-api.provider.ts` (it uses `fetch`; switch to `HttpClient` if the backend needs auth an interceptor adds), bind `{ provide: UWT_LOG_API_PROVIDER, useExisting: … }`, declare logger names in `UwtLoggerNames` |
| No | Don't inject `UwtLoggerService`, don't pass `withLogging()`, don't declare `UwtLoggerNames`. A **shell** still binds `{ provide: UWT_LOG_API_PROVIDER, useClass: UwtNoopLogApiProvider }` — the host requires one |

**Identity** — `application`, `environment`, `version` (plus optional `eventNamespace`, default
`com.uwt`; leave it unless Step 5 needs it). Reuse the app's environment files where they exist;
if you derive a value from browser globals (e.g. hostname), guard it — this also runs during server
rendering:

```ts
// standalone: app.config.ts — NgModule: the same entries in AppModule `providers`
import { ApplicationConfig } from '@angular/core';
import { provideUwtTelemetry } from '@absaoss-cps/ngx-ui-watchtower';
import {
  UWT_RUM_CREDENTIALS_PROVIDER,
  provideUwtTelemetryRumSink
} from '@absaoss-cps/ngx-ui-watchtower/rum';
import { AppRumCredentialsProvider } from './telemetry/rum-credentials.provider';
import { environment } from '../environments/environment';
import './telemetry/telemetry.schema'; // side-effect import — Step 4

export const appConfig: ApplicationConfig = {
  providers: [
    // …existing providers, unchanged
    provideUwtTelemetry({
      application: 'my-app',
      environment: environment.name, // e.g. 'dev' | 'qa' | 'prod'
      version: environment.version
    }),
    provideUwtTelemetryRumSink(),
    { provide: UWT_RUM_CREDENTIALS_PROVIDER, useExisting: AppRumCredentialsProvider }
  ]
};
```

- Register the providers **unconditionally** in the shared config. Do not split them between browser
  and server configs and do not wrap them in a platform check — every browser-touching path in the
  library is already a no-op on the server.
- Start with **no** `withScenarios` / `withBIEvents` / `withLogging` / `withRedaction` features. Add
  one only for a stated reason, and record the reason in a comment.
- Credentials: copy `assets/rum-credentials.provider.ts`, point it at the broker endpoint and adapt
  the response check. It returns `null` (RUM off) for a disabled, incomplete or expired answer
  and throws when the request fails, so a refresh retries instead of ending RUM. It sets
  `disableAutoPageView: true` (page views come from Step 6). Don't write an initializer — the sink
  calls it. It uses `fetch`; switch to `HttpClient` if an interceptor adds the broker's auth.
- **User identity** (only when the app has sign-in): inject `UwtTelemetrySink` as a field of the
  sign-in service (not inside a callback — `NG0203`), then `setUserId(opaqueId)` on sign-in and
  `setUserId(undefined)` on sign-out. Never an email or username. Fragments leave this to the shell.

### Step 4 · Declare the vocabulary

Copy `assets/telemetry.schema.ts` to the app (e.g. `src/app/telemetry/telemetry.schema.ts`). It
augments the library's name registries, so scenario, step, BI event (and logger) names become
compile-checked. Setup declares only the route-navigation names; `ui-watchtower-integration` adds the
app's own later.

- A name is a **metric dimension**: a typo or an interpolated id silently starts a second metric
  series. Never build a name from data (`` step(`load-${id}`) `` is wrong).
- Kebab-case for scenario and step names (`route-navigation`, `customers-load`, `fetch`); snake_case for BI
  events (`export_clicked`). One JSDoc line per name saying what it measures.
- Keep the side-effect import `import './telemetry/telemetry.schema';` where the providers are
  configured (`app.config.ts` or `AppModule`).

### Step 5 · Existing RUM integration (conditional)

If Step 1 found the app sending RUM events itself, follow `references/rum-migration.md` before
Step 6 — replacing a hand-written `RumService` naively breaks existing dashboards. Personal data the
old code sends today is fixed immediately, even if the migration has to wait.

### Step 6 · Proof — route-navigation tracking

One real scenario proves the whole pipeline. Copy `assets/route-navigation-telemetry.service.ts`
next to the schema and add `provideRouteNavigationTelemetry()` next to `provideRouter(...)` (a
`start()` in the root component would miss a blocking initial navigation). It works unchanged for
static, `:param`, lazy and redirected routes; a `matcher` route needs
`data: { telemetryPath: 'files/:path' }`. Keep the asset's behaviour — its comments explain it.
To start the clock at the click rather than at `NavigationStart`, call
`markNavigationIntent()` first in click handlers that navigate — most useful where the handler does
work before `router.navigate…`.

**Page views** — where RUM is the destination, bind `ROUTE_PAGE_VIEW_RECORDER` so page views use
the route template (automatic ones would send `/customers/42`; with `'noop'`, bind nothing):

```ts
import { inject } from '@angular/core';
import { UwtRumTelemetrySink } from '@absaoss-cps/ngx-ui-watchtower/rum';
import { ROUTE_PAGE_VIEW_RECORDER } from './telemetry/route-navigation-telemetry.service';

{
  provide: ROUTE_PAGE_VIEW_RECORDER,
  useFactory: () => {
    const rum = inject(UwtRumTelemetrySink);
    return (route: string) => rum.recordPageView(route);
  }
}
```

In a fragment, skip this step by default — the shell's router measures navigations that change the
page URL. Add it only if the fragment has internal routes the shell never routes.

**No router:** skip this step and the binding, and remove `disableAutoPageView: true` from the
credentials provider — RUM's one automatic page view per load is then right.

### Step 7 · Tests

- Every existing spec that now (directly or through a component) injects a telemetry service needs
  providers, or it fails with `NG0201`:

  ```ts
  providers: [
    provideUwtTelemetry(
      { application: 'my-app-test', environment: 'test', version: '0.0.0' },
      withScenarios({ defaultTimeoutMs: 0 }) // no scenario timers left running in tests
    ),
    provideUwtTelemetrySink('noop'),
    // only where UwtLoggerService is injected:
    { provide: UWT_LOG_API_PROVIDER, useClass: UwtNoopLogApiProvider }
  ]
  ```
- Copy the two spec templates next to their assets: `route-navigation-telemetry.service.spec.ts`
  (a recording sink and its own route table — add the app's own route shapes, e.g. its `:param`
  routes) and, for RUM, `rum-credentials.provider.spec.ts` (adapt the broker answer to the real
  one). They are written for Vitest. Under Jest, replace `vi.` with `jest.` (fake timers take
  `doNotFake` instead of `toFake`; `vi.stubGlobal('fetch', f)` becomes `globalThis.fetch = f`, and
  jsdom under Jest has no `Response`, so answer with `{ ok, status, json: async () => body }`);
  under Karma, use Jasmine's clock and spies. Check the tests bite: remove the `complete()` call in
  the service, confirm a test fails, restore it.
- jsdom has no `BroadcastChannel`: the broadcast sink and host degrade to no-ops in tests. Expected —
  don't polyfill it.

### Step 8 · Validate

Run, through the detected package manager, until all are green:

1. **Build** the app (including the server build when SSR is on).
2. **Unit tests.**
3. **Type-check:** `tsc -p tsconfig.app.json --noEmit` and the spec tsconfig — passing tests prove
   nothing about types (Vitest never type-checks), and a solution-style root tsconfig checks nothing.
4. **Live check** in the browser with the debug flags (no reload needed):

   ```js
   localStorage.setItem('debugScenario', 'true');
   localStorage.setItem('debugLogger', 'true'); // only with a log backend
   ```

   Each console line is `[<application>][<concern>] …`, and its second argument is the exact object
   handed to the sink. Confirm one `route-navigation` line per navigation with the right status and a
   template `route`, and that nothing is logged during server rendering.

Don't finish until build, tests and type-check are green. The `assets/` templates use current
Angular router and DI APIs; if the app's Angular version has changed one, adapt the template to the
app's version — never silence the error.

### Step 9 · Hand over

Report what was wired (role, destination, credentials endpoint, log provider, user identity) and
any follow-ups.
Then tell the user the next step: **to measure the app's own journeys and interactions, use the
`ui-watchtower-integration` skill** — it asks what they want to learn, proposes, and implements. For
a shell, also hand over the fragment contract from `references/micro-frontends.md`.

## Gotchas

- **`/rum` is a separate entry point for a reason.** Import RUM symbols only from
  `@absaoss-cps/ngx-ui-watchtower/rum`, and never re-export them from a shared barrel — that pulls
  `aws-rum-web` into every consumer's build. No deep imports (`…/src/lib/…`) either.
- **Telemetry never throws into the app** — every entry point fails open. Don't wrap calls in
  try/catch.
- **Redaction never scrubs URL path segments** (only query strings and fragments; `scanValuePatterns`
  only scrubs metadata and message values). Keep personal data out of URLs and report route
  templates, never resolved paths.

## Out of scope

- Instrumenting the app's own journeys and BI events → `ui-watchtower-integration`.
- CloudWatch dashboards, RUM extended metrics, alarms, Logs Insights queries.
- Sending the scenario id to the backend as a correlation header — the library ships no HTTP
  interceptor on purpose. Offer it as a follow-up, restricted to the app's own API origins.
- The fragment teams' own setup when this app is a shell — hand them the fragment contract.
- Upgrading Angular, OpenTelemetry, and non-Angular frameworks.
