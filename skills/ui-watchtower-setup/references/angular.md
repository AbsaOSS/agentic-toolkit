# Angular path: the adapter

Use when the app is Angular. It installs the adapter, `@absaoss-cps/ngx-ui-watchtower`, which
brings the core with it, and wires providers instead of creating an engine. Imports, providers and
the test harness are in `ngx-ui-watchtower-api.md`; behaviour is in `ui-watchtower-api.md`.

## Step 1 · Detect — also check

1. **Version.** Compare the app's `@angular/core` and `rxjs` with the adapter's range from the
   registry, never from memory: `npm view @absaoss-cps/ngx-ui-watchtower@latest peerDependencies`.
   - Inside → install the latest version.
   - Older → the newest release whose peers fit (`npm view … versions`, skipping prereleases such
     as `-stage` or `-rc`), pinned; none → stop.
   - Newer → stop and tell the user. Never `--force` or `--legacy-peer-deps`.
   - Note the chosen release's `aws-rum-web` range too — Step 2 installs within it.
2. **Package manager** — also `cli.packageManager` in `angular.json`.
3. **Bootstrap style** — standalone (`app.config.ts`, `bootstrapApplication`) or NgModule
   (`providers` in `app.module.ts`). Providers go in the same place either way.
4. **SSR** — `app.config.server.ts`, `server.ts`, `@angular/ssr`. The adapter is SSR-safe; only
   code *you* write needs a guard.
5. **Tests** — Jest, Karma or Vitest, and which specs build the root providers or render
   components that will inject telemetry services (they need providers in Step 7).
6. **Module Federation** — a remote loaded through `loadChildren` / `loadComponent` runs in the
   host's injector: give it no providers of its own.
7. **Router** — `provideRouter` / `RouterModule.forRoot`; note any `matcher` routes.

## Step 2 · Install

```bash
npm install @absaoss-cps/ngx-ui-watchtower@latest   # or the pinned version from Step 1
npm install "aws-rum-web@<range from Step 1>"   # only if THIS realm sends to RUM
```

Never add `@absaoss-cps/ui-watchtower` yourself: the adapter depends on its own version, and a
second copy breaks name declarations and `instanceof` (`npm ls @absaoss-cps/ui-watchtower` shows
one). When `aws-rum-web` is installed, add `"allowedCommonJsDependencies": ["shimmer"]` to the
app's build options in `angular.json` (a CommonJS transitive dependency; otherwise every build
warns).

**Templates:** change every `@absaoss-cps/ui-watchtower` module specifier in the copied
`telemetry.schema.ts`, `rum-credentials.provider.ts` and `log-api.provider.ts` to
`@absaoss-cps/ngx-ui-watchtower` (and `…/rum`) — the `declare module` line included.

## Step 3 · Providers

`provideUwtTelemetry(identity)` registers **configuration only**. Every realm also binds
**exactly one destination**; injecting a telemetry service without one fails at bootstrap with
`NG0201` — by design; fix the wiring, never add a fallback provider "to make it start". Two
different destinations also fail bootstrap.

| Role | Providers |
|---|---|
| Standalone app, sends to RUM | `provideUwtTelemetryRumSink()` (from `/rum`) + `{ provide: UWT_RUM_CREDENTIALS_PROVIDER, useClass: AppRumCredentialsProvider }` |
| Shell hosting fragments | the same + `provideUwtTelemetryBroadcastHost(channelId)` + a log provider — `micro-frontends.md` |
| Fragment inside a shell | `provideUwtTelemetrySink('broadcast', { channelName })` — `micro-frontends.md` |
| RUM not available yet | `provideUwtTelemetrySink('noop')` |
| Own backend | `provideUwtTelemetryDestination(MySink)` (`ngx-ui-watchtower-api.md` §5) |

**Log provider** — with a log backend: `{ provide: UWT_LOG_API_PROVIDER, useClass:
AppLogApiProvider }` (`assets/log-api.provider.ts`). Without one: don't inject `UwtLoggerService`,
don't pass `withLogging()`, don't declare `UwtLoggerNames`; a **shell** still binds `{ provide:
UWT_LOG_API_PROVIDER, useClass: UwtNoopLogApiProvider }` — the host requires one.

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
    { provide: UWT_RUM_CREDENTIALS_PROVIDER, useClass: AppRumCredentialsProvider }
  ]
};
```

- Register the providers **unconditionally** in the shared config. Don't split them between
  browser and server configs or wrap them in a platform check — every browser-touching path in
  the adapter is already a no-op on the server.
- Start with **no** `withScenarios` / `withBIEvents` / `withLogging` / `withRedaction` features.
  Add one only for a stated reason, and record the reason in a comment.
- **Off in some environments** (only when the user asks): keep every provider and add one
  feature, `withTelemetryEnabled(...)`, with a value from the environment files or a factory that
  reads config already available at bootstrap (read once, at startup):
  `provideUwtTelemetry(identity, withTelemetryEnabled(environment.name !== 'dev'))`. Never omit or
  wrap providers per environment or swap in `'noop'` (SKILL.md Step 3).
- The templates are plain classes, created by `useClass`. To use `HttpClient` (when an interceptor
  adds the broker's or log backend's auth), give the class a `private readonly http =
  inject(HttpClient)` field.
- **User identity**: inject `UwtTelemetrySink` as a field of the sign-in service (not inside a
  callback — `NG0203`), then `setUserId(...)` as in SKILL.md Step 3.

## Step 6 · Confirm the setup

The option the user chose in Step 1 (SKILL.md Step 6).

**Picked app telemetry** — inject the service for the concern where the action happens and call
it there, e.g. a BI event in the handler of the app's main button:

```ts
private readonly bi = inject(UwtBITelemetryService);

protected exportCsv(): void {
  this.bi.track('my-app-export-clicked', { format: 'csv' });
  // …the existing handler, unchanged
}
```

For a scenario around a load the user waits for, inject `UwtScenarioTelemetryService`, start it
before the request, and settle it: `traceScenario` on the `HttpClient` call (with `catchError`
settling `fail` with only the error class and HTTP status first — never the raw
`HttpErrorResponse`), and `cancel` in `ngOnDestroy`.

**Temporary check** — one marked app initializer in the app's providers (`app.config.ts`, or
`AppModule` `providers`), and its entry in `UwtBIEventNames`:

```ts
// TEMPORARY: setup check — remove
provideAppInitializer(() => inject(UwtBITelemetryService).track('my-app-setup-checked')),
```

It touches no component, so no spec needs new providers for it. It runs at startup, so set the
debug flag (`localStorage.setItem('debugBI', 'true')`) and reload once. Remove both afterwards
(SKILL.md Step 6).

**Route-navigation tracking** (only when the user chose it) — copy
`assets/route-navigation-tracker.ts` and `assets/route-navigation.angular.ts` (and their specs) next
to the schema, and add `provideRouteNavigationTelemetry()` next to `provideRouter(...)` — a
`start()` in the root component would miss a blocking initial navigation. It works unchanged for
static, `:param`, lazy and redirected routes; a `matcher` route needs
`data: { telemetryPath: 'files/:path' }`. To start the clock at the click, inject
`RouteNavigationTelemetryService` and call `markNavigationIntent()` first in click handlers that
navigate — most useful where the handler does work before `router.navigate…`.

Where RUM is the destination, it also takes over page views: add `disableAutoPageView: true` to the
credentials provider's config (and to its spec's three config expectations), and bind
`ROUTE_PAGE_VIEW_RECORDER` (with `'noop'`, do neither):

```ts
import { inject } from '@angular/core';
import { UwtRumTelemetrySink } from '@absaoss-cps/ngx-ui-watchtower/rum';
import { ROUTE_PAGE_VIEW_RECORDER } from './telemetry/route-navigation.angular';

{
  provide: ROUTE_PAGE_VIEW_RECORDER,
  useFactory: () => {
    const rum = inject(UwtRumTelemetrySink);
    return (route: string) => rum.recordPageView(route);
  }
}
```

## Step 7 · Tests

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
- With route-navigation tracking, the binding's spec, `route-navigation.angular.spec.ts`, runs the
  real Router in TestBed with a recording sink and its own route table — add the app's own route
  shapes.

## Step 8 · Validate — specifics

- Build with the server build too when SSR is on.
- Type-check with `tsc -p tsconfig.app.json --noEmit` and the spec tsconfig — a solution-style
  root tsconfig checks nothing.
- The templates use current Angular router and DI APIs; if the app's Angular version changed one,
  adapt the template to the app's version — never silence the error.
