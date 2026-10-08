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
`rum-credentials.provider.ts`, `log-api.provider.ts`, `route-navigation-telemetry.service.ts`.

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

1. **Angular version vs the supported range.** Not Angular at all → stop. Otherwise read the
   app's `@angular/core` and `rxjs` versions (installed, or else the ranges in `package.json`), and
   the library's supported range from the registry — never from memory; it changes with releases:
   `npm view @absaoss-cps/ngx-ui-watchtower@latest peerDependencies`.
   - **Inside the range** → install the latest version (Step 2).
   - **Older than the range** → find the newest version whose peers fit
     (`npm view @absaoss-cps/ngx-ui-watchtower versions --json`, then `npm view …@<version>
     peerDependencies` per candidate). If one exists, offer it, pinned; the API reference describes
     the latest version, so the installed typings win where they differ. If none fits, stop: an
     Angular upgrade is out of scope.
   - **Newer than the range** → the library doesn't support this Angular yet. Stop and tell the
     user. Never install with `--force` or `--legacy-peer-deps`: a peer range is the library's
     compatibility contract with Angular's compiler and runtime.
2. **Package manager** — from the lockfile (`package-lock.json`, `yarn.lock`, `pnpm-lock.yaml`), a
   `packageManager` field, or `cli.packageManager` in `angular.json`. Use it for every install and
   script run; never default to npm.
3. **Bootstrap style** — standalone (`app.config.ts`, `bootstrapApplication`) or NgModule
   (`providers` in `app.module.ts`). Providers go in the same place either way
   (`makeEnvironmentProviders` works in both).
4. **SSR** — `app.config.server.ts`, `server.ts`, `@angular/ssr`. Affects only code *you* write
   (Step 3, Gotchas); the library is SSR-safe.
5. **Test runner** — Jest, Karma or Vitest, and which specs build the root providers or render
   components that will inject telemetry services (they need providers in Step 7).
6. **Existing telemetry** — search for `aws-rum-web`, `recordEvent`, `recordPageView`, `pinUserId`,
   `addSessionAttributes`, a `RumService`, or another analytics SDK. If RUM is already wired, Step 5
   applies. If ngx-ui-watchtower is already partly wired, keep what exists and run only the steps
   for what is missing (destination and credentials, `telemetry.schema.ts`, user identity, the
   route-navigation proof, spec providers). If nothing is missing, say so and offer
   `ui-watchtower-integration`.
7. **Realm role** — standalone app, **shell** that embeds fragments (Web Fragments, Module
   Federation, iframes on the same origin), or **fragment** inside a shell. Look for
   `<web-fragment>`, fragment gateways, remote-entry config.
8. **Router** — `provideRouter` / `RouterModule.forRoot`; note any `matcher` routes (Step 6).
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
npm install aws-rum-web          # only if THIS realm sends to RUM (standalone app or shell)
```

If the install reports a peer conflict, stop and report it — don't override it.

`aws-rum-web` is an optional peer: a fragment or a `'noop'` app never needs it, because everything
RUM-related lives in the separate entry point `@absaoss-cps/ngx-ui-watchtower/rum`.

When `aws-rum-web` is installed, add `"allowedCommonJsDependencies": ["shimmer"]` to the app's build
options in `angular.json` (a CommonJS transitive dependency; otherwise every build warns). If a strict
`tsc` run fails inside `aws-rum-web`'s bundled `rrweb` typings, set `"skipLibCheck": true` in the
app tsconfig(s).

### Step 3 · Wire providers

`provideUwtTelemetry(identity)` registers **configuration only**. Every realm must also bind
**exactly one destination**; injecting a telemetry service without one fails at bootstrap with
`NG0201` — by design, so a forgotten destination is caught on the first run, not on an empty
dashboard. Two different destinations also fail bootstrap.

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
| Yes | Implement `UwtLogApiProvider` from `assets/log-api.provider.ts`, bind `{ provide: UWT_LOG_API_PROVIDER, useExisting: … }`, declare logger names in `UwtLoggerNames` |
| No | Don't inject `UwtLoggerService`, don't pass `withLogging()`, don't declare `UwtLoggerNames`. A **shell** still binds `{ provide: UWT_LOG_API_PROVIDER, useClass: UwtNoopLogApiProvider }` — the host requires one |

**Identity** — `application`, `environment`, `version` (plus optional `eventNamespace`, default
`com.uwt`; leave it unless Step 5 needs it). Reuse the app's environment files where they exist.
Anything you compute here runs during server rendering too, so guard browser globals:

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
- Credentials: copy `assets/rum-credentials.provider.ts`, point it at the broker endpoint from Step 1
  and adapt the response check. `load()` validates every required field and returns `null` on
  **any** failure or incomplete answer (that disables RUM for the session; the app keeps working).
  It also sets `disableAutoPageView: true` — page views come from Step 6, under the route template. `provideUwtTelemetryRumSink()` calls it from its own
  non-blocking initializer — don't write one. The asset uses `fetch`, which bypasses `HttpClient`
  interceptors: if the broker needs auth that an interceptor adds, call it through `HttpClient`
  (`firstValueFrom`) instead.
- **User identity** (only when Step 1 found sign-in): where sign-in completes, call
  `inject(UwtTelemetrySink).setUserId(opaqueId)`; on sign-out, `setUserId(undefined)` — that starts
  a fresh RUM session. Never an email or username. In a fragment, leave it to the shell: a
  fragment's `setUserId` is forwarded and changes the shell's user.

### Step 4 · Declare the vocabulary

Copy `assets/telemetry.schema.ts` to the app (e.g. `src/app/telemetry/telemetry.schema.ts`). It
augments the library's name registries, so scenario, step, BI event (and logger) names become
compile-checked. Setup declares only the route-navigation names; `ui-watchtower-integration` adds the
app's own later.

- A name is a **metric dimension**: a typo or an interpolated id silently starts a second metric
  series. Never build a name from data (`` step(`load-${id}`) `` is wrong).
- Kebab-case for scenario and step names (`route-navigation`, `customers-load`, `fetch`); snake_case for BI
  events (`export_clicked`). One JSDoc line per name saying what it measures.
- Augmentation applies program-wide, but keep `import './telemetry/telemetry.schema';` in the files
  that own the wiring (provider config, the router telemetry service) so it never becomes orphaned.
- Declare `UwtLoggerNames` only if the app has a log backend (Step 3).

### Step 5 · Existing RUM integration (conditional)

If Step 1 found the app sending RUM events itself, load `references/rum-migration.md` and follow it
**before** Step 6. The library emits its own event types and payloads; replacing a hand-written
`RumService` naively changes what reaches CloudWatch and breaks existing dashboards. Migrate first,
diff the wire, delete last — and keep exactly one page-view recorder. If you can't run the app to
diff the wire, don't delete the old service; leave that as a follow-up. One exception to "parity
first": personal data or raw free text the old code sends today is fixed immediately, even when the
migration is blocked — tell the owners of the affected dashboards.

### Step 6 · Proof — route-navigation tracking

One real scenario proves the whole pipeline (providers, destination, vocabulary, tests) and is
useful in every app. Copy `assets/route-navigation-telemetry.service.ts` next to the schema and call
its `start()` once from the root component's constructor (or from an app initializer). It works
unchanged for static, `:param`, lazy (`loadChildren`) and redirected routes. Only a `matcher` route
needs one thing: a `data: { telemetryPath: 'files/:path' }` entry naming its segment (otherwise it
reports `(matcher)`).

**Page views** — in a realm that sends to RUM (standalone app or shell), bind the asset's
`ROUTE_PAGE_VIEW_RECORDER` so each completed navigation records one page view under its route
template; the credentials provider has turned automatic page views off, which would send the
resolved path (`/customers/42`) — a PII and cardinality problem, since path segments are not
redacted:

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

With a `'noop'` destination, bind nothing; when you later switch to RUM, add this binding with the
sink. If an existing RUM integration records page views (Step 5), keep exactly one recorder.

In a fragment, skip this step by default — the shell's router measures navigations that change the
page URL. Add it only if the fragment has internal routes the shell never routes.

What the asset gets right, and why — keep these if you change it:

1. **Recorded when the navigation ends, backdated** to the click or the first `NavigationStart` —
   a scenario's `route` can't change after it starts, and only the end knows the final template.
   The template comes from the matched route config, never the URL.
2. **Keyed by navigation id**, never one "current" field — one navigation can supersede another.
3. **Guard and resolver redirects are one journey** under the final template, with
   `redirectedFrom` (the source template) in metadata; `NavigationSkipped` releases a carried
   redirect, or it leaks into an unrelated navigation.
4. **Statuses:** a guard returning `false` or a resolver with no data is `incomplete`; superseded,
   aborted or skipped is `abandoned`; an error is `failure`. A navigation superseded before its URL
   was recognized records nothing.
5. **No URL ever reaches telemetry.** An unmatched URL fails as `(unrecognized)` with a generic
   error — the router's own error quotes the URL. Reasons come from the router's `code`; its
   `reason` text is never sent (empty in production, can contain URLs in development).
6. **Click-intent backdating:** `markNavigationIntent()` from nav-link click handlers; a mark older
   than 2 s is discarded.

### Step 7 · Tests

The library ships no test doubles on purpose — the harness is a few lines.

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
- Add a spec for the route-navigation service with a **recording sink** (pattern in the API
  reference, "Testing"), using the app's real route shapes: a successful navigation records
  `success` with the route **template** (`/customers/:id`, never a resolved id — assert the id
  appears nowhere in the payload), a guard rejection records `incomplete` with reason
  `guard-rejected`, not `failure`, and, where the page-view recorder is bound, one page view per
  completed navigation under the template. Check the test bites:
  remove the `complete()` call and confirm it fails, then restore it.
- jsdom has no `BroadcastChannel`: the broadcast sink and host degrade to no-ops in tests. Expected —
  don't polyfill it.

### Step 8 · Validate

Run, through the detected package manager, until all are green:

1. **Build** the app (including the server build when SSR is on).
2. **Unit tests.**
3. **Type-check** for real: `tsc --noEmit` against a solution-style root tsconfig (`"files": []` +
   `"references"`) checks nothing — run `tsc -p tsconfig.app.json --noEmit` and the spec tsconfig, or
   `tsc --build`. Passing tests prove nothing about types: Vitest (esbuild) never type-checks, and
   Jest only does when ts-jest diagnostics are on.
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

- **No default destination** — `NG0201` at bootstrap means a destination (or, for the logger and the
  broadcast host, a log provider) is missing. Fix the wiring; never add a fallback provider "to make
  it start".
- **One destination per realm, never two.** Another destination *replaces* RUM; it never runs beside
  it. A fragment never gets the RUM sink.
- **`/rum` is a separate entry point for a reason.** Import RUM symbols only from
  `@absaoss-cps/ngx-ui-watchtower/rum`, and never re-export them from a shared barrel — that pulls
  `aws-rum-web` into every consumer's build. No deep imports (`…/src/lib/…`) either.
- **`route` is a metric dimension** — a template (`/customers/:id`), never a resolved URL; one series
  per customer is both a cardinality and a PII problem.
- **One page-view recorder, under the template.** Automatic RUM page views use the resolved path —
  keep `disableAutoPageView: true` with the Step 6 recorder, never both and never the automatic one
  alone.
- **Telemetry never throws into the app** — every entry point fails open. Don't wrap calls in
  try/catch.
- **Redaction cannot be fully disabled**, and URL **path** segments are not scrubbed — only query
  strings and fragments. Keep personal data out of URLs, or enable `withRedaction({ scanValuePatterns:
  ['email'] })`.

## Out of scope

- Instrumenting the app's own journeys and BI events → `ui-watchtower-integration`.
- CloudWatch dashboards, RUM extended metrics, alarms, Logs Insights queries.
- Sending the scenario id to the backend as a correlation header — the library ships no HTTP
  interceptor on purpose. Offer it as a follow-up, restricted to the app's own API origins.
- The fragment teams' own setup when this app is a shell — hand them the fragment contract.
- Upgrading Angular, OpenTelemetry, and non-Angular frameworks.
