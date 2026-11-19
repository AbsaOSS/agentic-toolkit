---
name: ui-watchtower-setup
description: >
  Installs and wires the ui-watchtower telemetry library in a frontend app — the Angular adapter
  @absaoss-cps/ngx-ui-watchtower in Angular apps, the framework-free core @absaoss-cps/ui-watchtower
  in any other app (any framework, or none): destination per app role (AWS CloudWatch RUM with its
  automatic page views, micro-frontend shell or fragment, no-op), credentials, log provider, typed
  name vocabulary, migration of a hand-written RUM integration, tests, and a confirmation that it
  works, chosen with the user. Use when asked to add, install, set up or wire ui-watchtower,
  ngx-ui-watchtower, UI telemetry or CloudWatch RUM in a web app, replace a RumService or an
  aws-rum-web wrapper, connect a micro-frontend shell or fragment, or turn telemetry off in some
  environments. NOT for: instrumenting the app's own journeys or BI events
  (→ ui-watchtower-integration), dashboards, server-side or native mobile apps.
license: Apache-2.0
compatibility: >
  Requires a browser app built from npm packages (a bundler or a framework CLI) and npm registry
  access. An Angular app must be within the peer range of a published
  @absaoss-cps/ngx-ui-watchtower release — the latest, or an older compatible one (checked at run
  time with npm view).
---

# ui-watchtower-setup

Sets up ui-watchtower in an existing frontend application: install, wire the destination for the
app's role, declare the name vocabulary, test, and confirm that telemetry arrives.

**Scope:** infrastructure, plus a confirmation the user chooses (Step 6). RUM works out of the box —
its automatic page views included — so setup adds no routing code unless the user asks for it.
Measuring the app's own journeys and interactions is the follow-up skill,
`ui-watchtower-integration` — hand over to it at the end (Step 9).

The library has three concerns: **scenarios** (did a user journey succeed, how long did it take),
**BI events** (did a meaningful thing happen) and **logs** (what happened in one run). Scenarios and
BI events go to **one destination** per JavaScript realm (normally AWS CloudWatch RUM). Logs always go
to the app's own log backend, never to the destination.

## Two paths, one workflow

| The app | Installs | Path reference |
|---|---|---|
| Angular (`@angular/core`, started with `bootstrapApplication` or an NgModule) | the adapter, [`@absaoss-cps/ngx-ui-watchtower`](https://www.npmjs.com/package/@absaoss-cps/ngx-ui-watchtower) — it brings the core | `references/angular.md` |
| Any other app — any framework, or none | the core, [`@absaoss-cps/ui-watchtower`](https://www.npmjs.com/package/@absaoss-cps/ui-watchtower) | `references/core.md` |

Angular has an adapter (providers and services); every other app uses the core directly, through
one engine module it creates at startup. Don't add framework-specific wrappers for a framework
without an adapter. The steps below are the same for every app; the path reference says how to do
each one there.

## Reference files — load on demand

| Load | When |
|---|---|
| [ui-watchtower-api](../shared/references/ui-watchtower-api.md) ([remote](https://github.com/AbsaOSS/agentic-toolkit/blob/master/skills/shared/references/ui-watchtower-api.md)) | Always, before writing code — the engine, behaviour, defaults, the RUM broker contract, test harness |
| [ngx-ui-watchtower-api](../shared/references/ngx-ui-watchtower-api.md) ([remote](https://github.com/AbsaOSS/agentic-toolkit/blob/master/skills/shared/references/ngx-ui-watchtower-api.md)) | Angular path — imports, providers, services, TestBed |
| The path reference above | Always, once Step 1 has chosen the path |
| `references/rum-migration.md` | The app already sends RUM events itself (`aws-rum-web`, a `RumService`) |
| `references/micro-frontends.md` | The app hosts embedded fragments, or is a fragment inside a shell |

Templates in `assets/` are copied into the app and adapted:

| Template | When |
|---|---|
| `telemetry.schema.ts` | Always (Step 4) |
| `rum-credentials.provider.ts` and its spec | The realm sends to RUM (Step 3) |
| `log-api.provider.ts` | The app has a log backend (Step 3) |
| `route-navigation-tracker.ts` and its spec | Only if the user chooses route-navigation tracking (Step 6) |
| `route-navigation.angular.ts` and its spec | The same, in an Angular app |

They import from the core; on the Angular path, change those imports to the adapter
(`angular.md`, Step 2).

## Workflow

Copy this checklist and track progress:

```
- [ ] Step 1: Detect the app's shape and path, and ask what can't be read (read-only)
- [ ] Step 2: Install the package
- [ ] Step 3: Wire the destination for this realm's role
- [ ] Step 4: Declare the name vocabulary
- [ ] Step 5: Migrate an existing RUM integration (only if one exists)
- [ ] Step 6: Confirm the setup, the way the user chose
- [ ] Step 7: Update and add tests
- [ ] Step 8: Validate (build, tests, type-check, live debug output)
- [ ] Step 9: Hand over (the report ends with the pointer to ui-watchtower-integration)
```

### Step 1 · Detect (read-only)

Read before writing anything — extend the app, don't restructure it.

1. **Path**, from `package.json` and the entry module: Angular → the adapter; anything else → the
   core (table above). Read the path reference now, and do its Step 1 checks too (the Angular one
   checks the adapter's peer range). In a monorepo, set up the app the user named.
2. **Package manager** — from the lockfile (`package-lock.json`, `yarn.lock`, `pnpm-lock.yaml`) or
   a `packageManager` field. Use it for every install and script run; never default to npm.
3. **Entry and config** — where the app starts, and where its build-time configuration lives
   (environment files, `import.meta.env`): the identity comes from there.
4. **Server rendering** — Angular SSR, or any framework that renders pages on the server. It
   affects only code *you* write (Step 3); the library touches no browser global on the server.
5. **Test runner** — Vitest, Jest or Karma, and which specs will reach telemetry through what they
   import, inject or render (they need a test engine in Step 7).
6. **Existing telemetry** — search for `aws-rum-web`, `recordEvent`, `recordPageView`, `pinUserId`,
   `addSessionAttributes`, a `RumService`, or another analytics SDK. If RUM is already wired, Step 5
   applies. If ui-watchtower is partly wired, run only the steps for what is missing; if nothing
   is, offer `ui-watchtower-integration` — unless the request is itself a wiring change (e.g.
   turning telemetry off in some environments, Step 3), which you make here.
7. **Realm role** — standalone app, **shell** that embeds fragments (Web Fragments, iframes on the
   same origin, separately started apps), or **fragment** inside a shell. Look for
   `<web-fragment>`, fragment gateways, remote-entry config. Code that runs in the host's realm (a
   Module Federation remote) is no realm of its own — `references/micro-frontends.md`.
8. **Router** — which one, and whether it exposes route templates (`/customers/:id`), or no router
   at all. It matters only if the user picks route-navigation tracking in Step 6.
9. **Sign-in** — an auth service, OIDC/MSAL library or session store, and where sign-in and
   sign-out complete. Note which **opaque** user id it exposes — it must be a UUID, which RUM
   requires (MSAL's `localAccountId`; an OIDC `sub` often isn't one) — never an email or username.
10. **Confirmation candidates** — two to four simple things *this* app does that one BI event or one
    scenario could confirm the setup with: its main button (`Export CSV`), a form submit
    (`Create note`), the first data load the user waits for (`GET /api/customers`), a
    journey-ending error. Name the real component and call; never a generic list.

Ask the user only what the code cannot answer, in one message:

- The `application` name to report (unique per app and per fragment), if not obvious.
- The **name prefix** for scenario, BI event and logger names (kebab-case, e.g. `customer-portal`):
  suggest the `application` name or a short form of it, and let the user confirm or change it.
- **Log backend**: does one exist to send log records to (endpoint, existing service)?
- **RUM**: the endpoint that returns the RUM app-monitor config and short-lived AWS credentials
  (typically a backend "broker"), or whether RUM is not ready yet (→ the no-op sink for now).
- **User id**: if the app has sign-in but exposes no opaque UUID, which one to use — or skip it.
- **Fragment**: the shell's `eventNamespace` (default `com.uwt`), unless the shell's code or
  contract shows it.
- **How to confirm the setup works** (Step 6), with the options in this order:
  1. route-navigation tracking, kept in the app — only if the router exposes route templates; it
     replaces RUM's automatic page views with page views under the route template;
  2. one or two of the candidates from item 10, named concretely, kept in the app;
  3. nothing permanent — you check with temporary code and remove it.

  With no answer, use option 3: never assume routing or permanent telemetry is wanted.

### Step 2 · Install

Install this path's package only — the commands and checks are in the path reference — plus
`aws-rum-web`, within the range the package's peers allow, only if **this** realm sends to RUM (a
standalone app or a shell, never a fragment). Use the package manager from Step 1; never `--force`
or `--legacy-peer-deps`. If a strict `tsc` run fails inside `aws-rum-web`'s bundled `rrweb`
typings, set `"skipLibCheck": true` in the app tsconfig(s).

### Step 3 · Wire the destination

Every realm has **one engine and exactly one destination**. In Angular, providers build it; on the
core, one engine module creates it at startup. What to choose is here; the code for each choice is
in the path reference's Step 3.

**Destination by realm role:**

| Role | Destination | Also |
|---|---|---|
| Standalone app, sends to RUM | the RUM sink (from `/rum`) | the credentials provider, `assets/rum-credentials.provider.ts` |
| Shell hosting fragments | the RUM sink | + a broadcast host + a log provider — `references/micro-frontends.md` |
| Fragment inside a shell | the broadcast sink, on the shell's channel | nothing else — `references/micro-frontends.md` |
| RUM not available yet | the no-op sink | explicit opt-out; everything runs, nothing ships; switching to RUM later takes more than one line — Step 9. Not for turning telemetry off per environment — see below |
| Own backend | a class extending `UwtTelemetrySink` | API reference §8 |

**Log provider:**

| App has a log backend? | Do |
|---|---|
| Yes | Copy `assets/log-api.provider.ts`, point it at the backend, and declare logger names in `UwtLoggerNames` |
| No | No logging and no logger names. The core's engine still takes `new UwtNoopLogApiProvider()`; in Angular, only a **shell** binds it — the host requires one |

**Identity** — `application`, `environment`, `version` (plus optional `eventNamespace`, default
`com.uwt`; leave it unless Step 5 needs it, or this is a fragment: then use the shell's —
`references/micro-frontends.md`). Reuse the app's configuration where it exists; if you derive a
value from browser globals (e.g. hostname), guard it — this also runs during server rendering.

- Start with **no** configuration overrides (Angular features `withScenarios`, `withBIEvents`,
  `withLogging`, `withRedaction`; the core's `scenarios`, `bi`, `logging`, `redaction`). Add one
  only for a stated reason, and record the reason in a comment.
- **Telemetry off in some environments** (only when the user asks): one switch, read once at
  startup from configuration available then — `withTelemetryEnabled(...)` in Angular, `enabled` on
  the core. Off means fully inert: no credentials fetch, no RUM SDK download, no broadcast channel,
  no page listeners; app code keeps working unchanged. Never do this by omitting or wrapping the
  wiring per environment or by swapping in the no-op sink — wiring errors would then only show up
  in some environments, and the no-op sink still times, redacts and listens. Tests keep telemetry
  on and never turn it off — not even in an extra off-path test; the switch is the library's, and
  it's tested there. In a shell with fragments, see `references/micro-frontends.md`.
- **Credentials**: copy `assets/rum-credentials.provider.ts`, point it at the broker endpoint and
  adapt the response check. It returns `null` (RUM off) for a disabled, incomplete or expired
  answer and throws when the request fails, so the library retries — at startup and on refresh —
  instead of ending RUM. It leaves page views automatic, RUM's default; only route-navigation
  tracking (Step 6, option 1) changes that. Don't call it yourself or write an initializer for it —
  the RUM sink calls it. It uses `fetch`; the path reference says how to use the app's HTTP client
  instead when that adds the broker's auth.
- **User identity** (only when the app has sign-in): `setUserId(opaqueId)` on sign-in and
  `setUserId(undefined)` on sign-out — or straight from the auth state stream, initial `undefined`
  included: signing out while nobody is signed in does nothing. Call it as early as possible (e.g.
  once MSAL has initialized), since events carry `signedIn` only after the first call. The id must
  be a UUID; never an email or username. Fragments leave this to the shell.

### Step 4 · Declare the vocabulary

Copy `assets/telemetry.schema.ts` next to the rest of the telemetry code (e.g.
`src/telemetry/telemetry.schema.ts`; `src/app/telemetry/` in Angular). It augments the library's
name registries, so scenario, step, BI event (and logger) names become compile-checked. Replace
the template's `my-app` prefix with the one confirmed in Step 1. Setup declares only the names the
telemetry kept in Step 6 uses — none for a temporary check; `ui-watchtower-integration` adds the
app's own later.

- A name is a **metric dimension**: a typo or an interpolated id silently starts a second metric
  series. Never build a name from data (`` step(`load-${id}`) `` is wrong).
- **kebab-case only** — never snake_case or a mix (the library's own values, such as the
  `scenario-start` / `scenario-end` step markers, are kebab-case too):
  - scenarios `<prefix>-<thing>-<action>`, the action a verb (`my-app-customers-load`);
  - BI events `<prefix>-<thing>-<past-tense verb>` (`my-app-export-clicked`);
  - loggers `<prefix>-<area>` (`my-app-checkout`);
  - steps and aggregates without the prefix — they only appear inside a prefixed scenario —
    `<action>` or `<thing>-<action>` (`fetch`, `render`, `row-format`).
- One JSDoc line per name saying what it measures.
- Keep the side-effect import `import './telemetry.schema';` where telemetry is set up: the engine
  module, or `app.config.ts` / `AppModule` in Angular.

### Step 5 · Existing RUM integration (conditional)

If Step 1 found the app sending RUM events itself, follow `references/rum-migration.md` before
Step 6 — replacing a hand-written `RumService` naively breaks existing dashboards. Personal data the
old code sends today is fixed immediately, even if the migration has to wait.

### Step 6 · Confirm the setup

Prove that telemetry reaches the destination, in the way the user chose in Step 1 (option 3 when
nobody answered). The code for each option is in the path reference's Step 6.

1. **Route-navigation tracking** (only when chosen). Copy `assets/route-navigation-tracker.ts` and
   bind it to the router: the Angular Router with `route-navigation.angular.ts`; any other router
   with a small binding you write on its navigation events (`core.md`, Step 6). Set its
   `NAVIGATION_SCENARIO` to `<prefix>-route-navigate`, declared in the schema. Bind it before the
   initial navigation runs. Keep the template's behaviour — its comments explain it: one scenario
   per navigation under the route **template** (`/customers/:id`, never the resolved URL); a redirect
   is one scenario under its final template; a guard's "no" is `incomplete`, a superseded
   navigation `abandoned`, a hang `timeout` after 30 s; failures keep only an error class and an HTTP
   status. Where RUM is the destination, it also takes over page views: add
   `disableAutoPageView: true` to the credentials provider (and to the three config expectations in
   its spec), and give the tracker the RUM sink's `recordPageView`. Never both automatic and
   tracked page views.
2. **The app telemetry the user picked** — one or two items, kept. Implement each minimally, where
   the action happens: a BI event in the handler, or a scenario that settles `complete`, `fail`
   (only an error class and HTTP status, never the raw error) or `cancel` when its owner goes away.
   Declare the names (Step 4), call the scenario or BI API directly — never a wrapper — and test
   each outcome (Step 7). Anything beyond that is `ui-watchtower-integration`'s job.
3. **Temporary check** — nothing stays in the app:
   1. Note the files you touch. Add one call marked `// TEMPORARY: setup check — remove`, e.g. a BI
      event `<prefix>-setup-checked` sent once at startup, and its schema entry.
   2. Run the app with the debug flags on (Step 8) and confirm the event's console line; with RUM,
      also confirm the RUM batch request in DevTools → Network (`dataplane.rum.<region>…`), next to
      the page view RUM records by itself.
   3. Remove the call and the schema entry, check the touched files are back to their state before
      the check, and re-run the build and the tests.

   If you can't drive a browser, ask the user to load the page once while the call is in place and
   tell you what the console shows, then remove it. If nobody can, remove it anyway and report the
   live check as not done. Never hand over with temporary code in place.

In a fragment, confirm through the shell with option 2 or 3 — its events show up with its own
`application` prefix. Navigations that change the page URL are the shell's.

### Step 7 · Tests

- Every existing spec that now reaches telemetry (directly or through what it renders) needs a test
  engine: test providers in Angular (without them, `NG0201`), one mock of the engine module in the
  test setup file on the core. The path reference's Step 7 has it.
- For RUM, copy `rum-credentials.provider.spec.ts` next to its provider and adapt the broker answer
  to the real one.
- For the telemetry kept in Step 6: the tracker's and the binding's specs for route-navigation
  tracking (add the app's own route shapes, e.g. its `:param` routes), or one test per outcome of
  the picked items (API reference §11). A temporary check leaves no test behind.
- The spec templates are written for Vitest. Under Jest, replace `vi.` with `jest.` (fake timers
  take `doNotFake` instead of `toFake`; `vi.stubGlobal('fetch', f)` becomes `globalThis.fetch = f`,
  and jsdom under Jest has no `Response`, so answer with `{ ok, status, json: async () => body }`) —
  `core.md` adds what Jest needs for the core; under Karma, use Jasmine's clock and spies.
- Check the tests bite: remove the settle or `track` call the kept telemetry depends on, confirm a
  test fails, restore it.
- jsdom has no `BroadcastChannel`: the broadcast sink and host degrade to no-ops in tests. Expected —
  don't polyfill it.

### Step 8 · Validate

Run, through the detected package manager, until all are green:

1. **Build** the app (including the server build when SSR is on).
2. **Unit tests.**
3. **Type-check** with the app's own script if it has one (e.g. `tsc -b`), else `tsc --noEmit -p`
   on the app's and the specs' tsconfig (Angular: `angular.md`, Step 8) — passing tests prove
   nothing about types (Vitest never type-checks).
4. **Live check** in the browser with the debug flags (read on every event, so no reload is
   needed for events sent after you set them; an event sent at startup needs one reload):

   ```js
   localStorage.setItem('debugScenario', 'true');
   localStorage.setItem('debugBI', 'true');
   localStorage.setItem('debugLogger', 'true'); // only with a log backend
   ```

   Each console line is `[<application>][<concern>] …`, and its second argument is the exact
   object handed to the destination. Confirm a line for the telemetry kept in Step 6 — one
   `<prefix>-route-navigate` line per navigation with a template `route`, or the picked events
   with the right status — and that nothing is logged during server rendering. A temporary check
   was already confirmed and removed in Step 6: here, confirm that its event no longer appears.
   Where the off switch turns telemetry off, no lines appear — check in an environment where it is
   on, then confirm the off one stays silent.

Don't finish until build, tests and type-check are green. The templates use current router and
framework APIs; if the app's version has changed one, adapt the template to the app's version —
never silence the error.

### Step 9 · Hand over

Report what was wired (path, role, destination, credentials endpoint, log provider, user identity),
how the setup was confirmed (and, for a temporary check, that it was removed), and any follow-ups.
With the RUM destination, also report:
- **Page views:** without route-navigation tracking, RUM records them by itself, one per page load
  and route change, under the URL path (`pageIdFormat: 'PATH'`), ids included (`/customers/42`). If
  a path can carry personal data (an email, a name), say so and offer route-navigation tracking.
  With it, the tracker records one per completed navigation under the route template
  (`/customers/:id`), and RUM's automatic ones are off (`disableAutoPageView: true`).
- **What it keeps in the browser**, for the app's cookie or privacy notice: the RUM client's cookies
  `cwr_s` (session id; by default the session ends after 30 minutes without an event) and `cwr_u`
  (user id, kept for `userIdRetentionDays` — 30 days by default — and shared by every app on the
  hostname), and the library's `localStorage` entry `ngx-ui-watchtower.sessionStarts` (up to five
  recent session ids with their start times; the core keeps the name). On shared devices, suggest
  `userIdRetentionDays: 0` (no user cookie); where several apps with their own app monitors share a
  hostname, `cookieAttributes: { unique: true }` keeps their sessions apart (the session cookie is
  then `cwr_s_<app monitor id>`). Both settings come from the broker's config.

With the no-op sink, hand over the switch to RUM as a checklist — it is more than one line: install
`aws-rum-web` (Step 2, and in Angular the `shimmer` allowance), and replace the no-op sink with the
RUM sink plus the credentials provider (Step 3); with route-navigation tracking, also give the
tracker the page views and set `disableAutoPageView: true` (Step 6).
End the report with the next step, every time and however short the report is — it is the only way
the user learns that their own journeys are still unmeasured: **to measure the app's own journeys and interactions, use the
`ui-watchtower-integration` skill** — it asks what they want to learn, proposes, and implements. For
a shell, also hand over the fragment contract from `references/micro-frontends.md`.

## Gotchas

- **`/rum` is a separate entry point for a reason.** Import RUM symbols only from the package's
  `/rum` entry point (`@absaoss-cps/ui-watchtower/rum`, or `@absaoss-cps/ngx-ui-watchtower/rum` in
  Angular), and never re-export them from a shared barrel — that pulls `aws-rum-web` into every
  consumer's build. No deep imports (`…/src/lib/…`, `…/fesm2022/…`) either.
- **Telemetry never throws into the app** — every call fails open. Don't wrap calls in try/catch.
- **Page views are RUM's.** Leave `disableAutoPageView` unset unless route-navigation tracking
  records page views instead (Step 6, option 1). With it off and nothing recording them, RUM
  records no page views at all.
- **Redaction never scrubs URL path segments** (only query strings and fragments; `scanValuePatterns`
  only scrubs metadata and message values). Keep personal data out of URLs, and give scenario
  `route` fields and metadata route templates, never resolved paths.
- **The trace header follows redirects.** RUM adds `X-Amzn-Trace-Id` (`traceparent` with
  `enableW3CTraceId`) to requests whose URL starts with the page's origin — in current releases,
  absolute same-origin URLs only, so relative calls (`/api/…`) get none. Such a request to an
  endpoint that redirects to another origin (an S3 download, an SSO login) fails CORS unless that
  origin allows the header. Look for such endpoints, list them, and fix it at the target.

## Out of scope

- Instrumenting the app's own journeys and BI events → `ui-watchtower-integration`.
- CloudWatch dashboards, RUM extended metrics, alarms, Logs Insights queries.
- Unreleased features (ui-watchtower #29): sending the scenario id to the backend, the X-Ray header
  on relative URLs, the shell tracing fragments' requests. Use one only once the installed
  package's typings have it (API reference §13).
- The fragment teams' own setup when this app is a shell — hand them the fragment contract.
- Upgrading the framework, OpenTelemetry, server-side and native mobile apps.
