# ui-watchtower API reference (core)

The public surface of `@absaoss-cps/ui-watchtower`, the framework-independent core (latest
release, 0.1.1; if the installed typings differ, they win). It works in any frontend — plain
JavaScript or TypeScript, in any framework — and touches no browser global when
imported. An Angular app uses the adapter instead, `@absaoss-cps/ngx-ui-watchtower`
(`ngx-ui-watchtower-api.md`), which wraps these same objects; everything below about behaviour
(§3–§12) applies to it too. Import only from the entry points in §1 — no deep imports.

## Contents

1. [Packages and imports](#1-packages-and-imports)
2. [The engine](#2-the-engine)
3. [Identity and configuration defaults](#3-identity-and-configuration-defaults)
4. [Scenarios](#4-scenarios)
5. [BI events](#5-bi-events)
6. [Logging](#6-logging)
7. [RUM sink and credentials](#7-rum-sink-and-credentials)
8. [Custom destination](#8-custom-destination)
9. [What reaches the wire](#9-what-reaches-the-wire)
10. [Debug flags and the reporter](#10-debug-flags-and-the-reporter)
11. [Testing](#11-testing)
12. [Shell and fragments](#12-shell-and-fragments)
13. [Not yet released](#13-not-yet-released)

## 1. Packages and imports

| Package                          | Use it when                                                       |
|----------------------------------|-------------------------------------------------------------------|
| `@absaoss-cps/ngx-ui-watchtower` | The app is Angular. Installing it installs the core too: never add `@absaoss-cps/ui-watchtower` to an Angular app (a second copy at another version breaks name declarations and `instanceof`; `npm ls @absaoss-cps/ui-watchtower` shows one). |
| `@absaoss-cps/ui-watchtower`     | Any other app: no adapter needed.                                 |

```ts
// '@absaoss-cps/ui-watchtower' — the engine, contracts, no-op and broadcast destinations
import {
  uwtCreateTelemetry,                                    // §2
  UwtTelemetrySink, UwtNoopTelemetrySink,                // destinations (§8)
  UwtNoopLogApiProvider,                                 // "no log backend" (§6)
  UwtTelemetryBroadcastHost, UwtBroadcastTelemetrySink,  // shell and fragments (§12)
  UwtBroadcastLogApiProvider, uwtConnectBroadcastChannel, UWT_DEFAULT_BROADCAST_CHANNEL,
  uwtClassifyTelemetryEvent, uwtMarkSessionStart,        // custom sinks (§8)
  uwtConsoleReporter, uwtIsDebugEnabled,                 // §10
  uwtRedactMetadata, uwtNormalizeError, uwtScrubString, uwtRedactConfigFor // custom sinks
} from '@absaoss-cps/ui-watchtower';
import type {
  UwtTelemetry, UwtTelemetryOptions, UwtTelemetryIdentity, UwtTelemetryMetadata,
  UwtTelemetryError, UwtScenario, UwtScenarioOptions, UwtScenarioOutcome, UwtScenarioRecord,
  UwtScenarioStatus, UwtBIEventName, UwtLogApiProvider, UwtLogQuery, UwtLogRecord, UwtLogDetail,
  UwtReporter,
  // registries augmented by telemetry.schema.ts
  UwtScenarioNames, UwtScenarioSteps, UwtBIEventNames, UwtLoggerNames
} from '@absaoss-cps/ui-watchtower';

// '@absaoss-cps/ui-watchtower/rum' — the AWS CloudWatch RUM destination (needs aws-rum-web)
import { UwtRumTelemetrySink } from '@absaoss-cps/ui-watchtower/rum';
import type {
  UwtRumCredentialsProvider, UwtRumBootstrap, UwtRumCredentials, UwtRumAppMonitorConfig,
  UwtRumTelemetrySinkOptions
} from '@absaoss-cps/ui-watchtower/rum';

// '@absaoss-cps/ui-watchtower/rxjs' — only in apps that already use RxJS (needs rxjs)
import { traceScenario } from '@absaoss-cps/ui-watchtower/rxjs';
```

Install the core, plus `aws-rum-web` only for `/rum` and `rxjs` only for `/rxjs` (both are
optional peers). Use `import type` for the credential types, so a credentials provider carries no
runtime dependency on `/rum`.

## 2. The engine

One engine per application — or per fragment in a composed page — created once at startup and
shared, never one per component:

```ts
const telemetry: UwtTelemetry = uwtCreateTelemetry({
  identity: { application: 'my-app', environment, version },  // §3
  destination,            // a UwtTelemetrySink: scenarios, BI events and mirrored errors (§7, §8, §12)
  logApi,                 // a UwtLogApiProvider: where logs go and are read back from (§6)
  scenarios: { /* … */ }, // optional overrides per concern (§3): scenarios, bi, logging, redaction
  enabled,                // false makes everything inert (below); default true
  document,               // the page whose lifecycle settles and flushes; the global one by default,
                          // null for none (server rendering)
  report                  // receives what is skipped or dropped (§10); nothing is reported without one
});

telemetry.scenarios;      // §4      telemetry.bi; // §5      telemetry.logging; // §6
telemetry.setUserId(id);  // the destination's user (§7); undefined or '' signs out
telemetry.flush(beacon?); // hands queued work to the destination
telemetry.dispose();      // see below
```

Every call is fail-open: telemetry never throws into the app. `uwtCreateTelemetry` itself throws
when `identity` (its `application`, `environment` or `version`), `destination` or `logApi` is
missing — a wiring error surfaces at startup.

`dispose()` stops watching the page, settles scenarios still in flight as `abandoned`
(`abandonedBy: 'disposed'`; core 0.1.0 records `'page-hidden'`, as on unload) and flushes.
The destination and log store are the app's: dispose them yourself, after the engine. Every
`dispose()` can be called more than once.

**Turning telemetry off** — `enabled: false`. Keep the same calls and the same wiring, so it fails
the same way everywhere; read the switch once at startup (no runtime toggling, e.g. for consent).
Pass the same value to what you create for the engine: `enabled` on the RUM sink (no credentials
fetch, no SDK download), the broadcast classes and `uwtConnectBroadcastChannel` (no channel). When
off:

- `scenarios.start()` returns an inert `UwtScenario` (own `id`, the given `name`, chainable) that
  records nothing and **never settles**; `find` / `findByName` / `getActive` find nothing,
  `onSettled` listeners never run, `traceScenario` passes values and errors through.
- `bi.track()` does nothing; `logging.getLogger()` returns an inert logger; `logging.query()`
  resolves `[]` without calling the log provider.
- The bundle doesn't shrink.

`new UwtNoopTelemetrySink()` is not the same: it only stops shipping.

## 3. Identity and configuration defaults

```ts
interface UwtTelemetryIdentity {
  application: string;      // unique per app and per fragment; becomes a session attribute
  environment: string;      // 'dev' | 'qa' | 'prod' …
  version: string;
  eventNamespace?: string;  // default 'com.uwt' → com.uwt.scenario, com.uwt.scenario.step, com.uwt.bi
}
```

| Override (engine option) | Options and defaults                                                                                                        |
|--------------------------|-----------------------------------------------------------------------------------------------------------------------------|
| `scenarios`              | `defaultTimeoutMs: 30_000` (0 disables), `emitLifecycleEvents: false`, `maxSteps: 50`, `userTimings: false`, `markCleanupFallbackMs: 300_000`, `redact: true` |
| `bi`                     | `dedupWindowMs: 400`, `dedupMaxKeys: 100`, `redact: true`                                                                     |
| `logging`                | `minLevel: 'log'` (`'log' \| 'warn' \| 'error'`), `levels?` per logger name, `mirrorErrorsToRum: false`, `redact: true`        |
| `redaction`              | `extraKeyPatterns: []`, `maxStringLength: 1024`, `maxKeys: 50`, `maxStackLength: 2048`, `includeStack: true`, `stripUrlQuery: true`, `scanValuePatterns: []` (`'email' \| 'creditCard' \| 'ssn' \| 'ipv4' \| 'phone'`), `extraValuePatterns: []`, `extraValueTransforms: []` |

Always on, even with `redact: false`: the credential key denylist (`password`, `secret`, `token`,
`auth`, `credential`, `cookie`, `api-key`, `bearer`, `jwt`, `signature`, `session-key`, `ssn` —
substring, case-insensitive), the size caps, error normalization to `{ name, message, stack? }`, and
`extraValueTransforms`. URL query strings and fragments are stripped; **path segments are not** — so
an HTTP error object passed as `error` sends its message, which often quotes the request URL path
(ids included). Send its class and status instead (`safeHttpFailure` in the integration patterns).

## 4. Scenarios

```ts
const scenario = telemetry.scenarios.start({
  name: 'my-app-customers-load', // declared in UwtScenarioNames
  feature?: 'customers',    // free-form classification (plain string)
  operation?: 'list',       // free-form classification (plain string)
  route?: '/customers/:id', // a TEMPLATE, never a resolved URL
  parentScenarioId?: string,
  startedAt?: number,       // epoch ms (Date.now()) — backdate to the click
  timeoutMs?: number,       // default 30_000; 0 disables
  metadata?: UwtTelemetryMetadata
});
```

| Member                                        | Notes                                                                                         |
|-----------------------------------------------|-----------------------------------------------------------------------------------------------|
| `step(name, metadata?)`                       | Opens a step (declared in `UwtScenarioSteps`); closes the previous one                         |
| `endStep(detail?)` / `failStep(error, detail?)` | Close the open step explicitly                                                                |
| `aggregateStart(name)` / `aggregateEnd(name)` | Sum repeated work (per-row formatting) into one total + call count instead of N steps         |
| `setData(metadata)`                           | Merge attributes onto the record (re-capped at `maxKeys`)                                      |
| `complete(outcome?)`                          | → `success`                                                                                    |
| `fail(outcome?)`                              | → `failure`; pass `{ error, statusCode? }`                                                     |
| `cancel(outcome?)`                            | → `abandoned`; pass `{ reason }`; stamps `metadata.abandonedBy: 'caller'`                      |
| `incomplete(outcome?)`                        | → `incomplete`                                                                                 |
| `settle(status, outcome?, error?)`            | For code mapping an external status; prefer the named methods                                 |
| `id`, `name`, `status`, `isSettled`, `delta`  | `id` is the correlation id                                                                     |
| `toRecord()`                                  | Deep-cloned snapshot; `status` undefined while running                                         |

`UwtScenarioOutcome = { message?, reason?, metadata?, statusCode?, error? }`. `reason` is a short,
low-cardinality grouping key (`'superseded'`, `'no-results'`). Settling is absorbing: the first
settle wins, later calls are ignored. Timeout settles as `timeout` automatically.

**With promises** (no RxJS needed) — settle on every path, and cancel when the work is dropped:

```ts
const scenario = telemetry.scenarios.start({ name: 'my-app-customers-load' });
try {
  scenario.step('fetch');
  const customers = await api.customers({ signal });
  scenario.complete({ metadata: { count: customers.length } });
} catch (error) {
  if (signal.aborted) scenario.cancel({ reason: 'superseded' }); // a newer load, or unmount
  else scenario.fail({ error: safeHttpFailure(error) });
}
```

**With RxJS** — `traceScenario(scenario, options?, report?)` from `/rxjs`: `complete()` on source
completion, `fail({ error })` on error. On an unsubscribe before either, it depends on whether a
value got through. Before any value it calls `cancel(cancelOutcome)`: a superseding `switchMap` or
a teardown records `abandoned`. After a value it calls `complete()` with the outcome mapped from the
last value, so `firstValueFrom()`, and `take(1)`/`first()` placed after it, record `success`. For a
multi-value stream (polling, progress, a websocket), where stopping after a value means the user
gave up, pass `valueThenTeardown: 'cancel'`.

```ts
interface UwtTraceScenarioOptions<T> {
  outcome?: (value: T) => UwtScenarioOutcome | void;   // from the last emitted value
  cancelOutcome?: UwtScenarioOutcome | (() => UwtScenarioOutcome | void);
  valueThenTeardown?: 'complete' | 'cancel';           // teardown after a value; default 'complete'
}
```

Extras: `telemetry.scenarios.find(id)`, `findByName(name)`, `getActive()`, and
`onSettled(listener)` (a deep-cloned record per settled scenario; returns an unsubscribe
function). On `pagehide` every in-flight scenario settles as `abandoned` (`abandonedBy:
'page-hidden'`); on `visibilitychange` to hidden the destination flushes and scenarios keep
running. More than 50 active scenarios is reported as a likely leak.

## 5. BI events

```ts
telemetry.bi.track(
  'my-app-export-clicked',                        // declared in UwtBIEventNames
  { format: 'csv' },                              // flat metadata
  { scenarioId: scenario.id, feature: 'reports' } // optional: join to a journey
);
```

What the destination receives is always `record('{ns}.bi', event)` — `com.uwt.bi` by default — with

```ts
event = { eventName, eventTime /* ISO string */, metadata?, scenarioId?, feature?, application, sessionId?, userId? }
```

There is no per-event type override. To keep an old dashboard's event type, use `eventNamespace` or
a raw `destination.record()` (rum-migration.md §2).

The name is in **`eventName`** (not `name`). A test with a recording sink asserts on
`payload.eventName` and `payload.metadata`.

Identical events (name + scenarioId + feature + metadata) within 400 ms collapse into one — no
click throttling needed. Type any parameter that carries an event name as `UwtBIEventName`, not
`string`, or it stops compiling once the registry is augmented.

## 6. Logging

Only with a log backend; otherwise `new UwtNoopLogApiProvider()`.

```ts
const logger = telemetry.logging.getLogger('my-app-checkout'); // declared in UwtLoggerNames

logger.log('Submitting order');
logger.warn('Retrying payment', { metadata: { attempt: 2 } });
logger.error('Payment failed', { error, correlationId: scenario.id, context: 'checkout' });
// never a raw HTTP error object as `error` — its message quotes the request URL (§3)

telemetry.logging.query({ correlationId: scenario.id }); // → your provider's query()
```

`UwtLogDetail = { context?, metadata?, error?, correlationId? }`. Loggers are named — there is no
unnamed `log()`. `correlationId = scenario.id` is what joins log lines to a journey.

```ts
interface UwtLogApiProvider {
  send(record: UwtLogRecord): void;          // must not throw; batching/retries/auth are yours
  query(filter: UwtLogQuery): Promise<UwtLogRecord[]>;
  flush?(): void;                            // called when the page is hidden or closed
}
interface UwtLogQuery { correlationId?; logger?; minLevel?; from?; to?; limit? }
```

Records are sent as they are written. Browsers reject `keepalive` requests once all in flight exceed
64 KiB, so one request per record sends with `keepalive` only while the page is hidden; Safari still
says `visible` while a page that is reloading or navigating away hides, so such a provider can lose
a record written as the page goes, in Safari. A provider that batches adds `flush()` and sends from
it with `navigator.sendBeacon` or a `keepalive` request every time.

`UwtNoopLogApiProvider` is the explicit "no log backend": discards records, `query()` returns `[]`.

## 7. RUM sink and credentials

```ts
const destination = new UwtRumTelemetrySink({
  identity,                 // the engine's
  credentialsProvider,      // below
  enabled                   // the engine's switch (§2)
});
destination.init();         // never awaited: a slow broker never delays the page
```

```ts
interface UwtRumCredentialsProvider {
  /** Called at startup and again ~5 min before each credential expiry. `null` disables RUM. */
  load(): Promise<UwtRumBootstrap | null>;
}
interface UwtRumBootstrap { config: UwtRumAppMonitorConfig; credentials?: UwtRumCredentials }
interface UwtRumCredentials { accessKeyId; secretAccessKey; sessionToken; expiration } // all strings
```

| `load()` returns            | Effect                                                                                       |
|-----------------------------|----------------------------------------------------------------------------------------------|
| `null`                      | RUM off for the rest of the page; mid-session it tears the running client down                |
| throws / rejects            | Retried. At startup with a random wait that grows from up to 1 s to up to 60 s, for 5 minutes, events buffered (at most 100); on a refresh every 30 s, keeping the current credentials |
| `{ config, credentials }`   | Normal path                                                                                  |
| `{ config }` only           | Only for an app monitor allowing unauthenticated access                                       |

`UwtRumAppMonitorConfig` requires `applicationId`, `region`, `applicationVersion`; it mirrors the
`aws-rum-web` config otherwise (`sessionSampleRate`, `sessionEventLimit` (default 200),
`telemetries`, `allowCookies`, `disableAutoPageView`, `pageIdFormat`, `pagesToInclude/Exclude`,
`enableXRay`, `endpoint`, …). Deliberately absent: `identityPoolId`/`guestRoleArn` (Cognito — use
your broker), `endpointUrl`, `sessionId`, `userId`. Leave `telemetries` out of broker JSON where you
can: a list replaces the library's default, whose `http` entry adds the X-Ray header to requests
whose URL starts with the page's origin — absolute same-origin URLs only, so a relative call
(`/api/...`) gets no header (relative URLs come with ui-watchtower #29, §13). If the broker sends
one, take names only (`['errors', 'http']`): settings that need a
`RegExp` or a function (`pagesToExclude`, or `urlsToExclude`, `ignore` inside `telemetries`, and
`addXRayTraceIdHeader` unless it's a boolean) can't travel as JSON. If one arrives as a string, the
sink doesn't start RUM for the page and reports it (each setting and its expected type, never the
value), rather than let the SDK throw or record what the filters should exclude. Set them in code.

A same-origin endpoint that redirects to another origin (a download that 302s to S3, an SSO login)
passes the trace header on, and the request fails unless that origin allows it in CORS:
`x-amzn-trace-id`, or `traceparent` with `enableW3CTraceId` (the SDK sends one or the other). Fix it
at the target.

User identity: `telemetry.setUserId(id)` takes a UUID — RUM's API accepts nothing else (MSAL's
`localAccountId`, not `homeAccountId`; an OIDC `sub` often isn't one). `undefined` or `''` signs
out: a new session with a new anonymous id, but only when someone was signed in, so it can follow
an auth state stream directly. Call it as early as possible — events carry `signedIn` only after the
first call (§9).

Page views are automatic by default (RUM records one per page load and route change, under the URL
path); leave `disableAutoPageView` unset. `destination.recordPageView(pageId)` is for an app that
opts into recording route-template page ids itself: it sets `disableAutoPageView: true` — never
both. `dispose()` stops the
client.

## 8. Custom destination

```ts
export class MyBackendSink extends UwtTelemetrySink {
  record(eventType: string, payload: object, metadata?: UwtTelemetryMetadata): void {
    const event = uwtClassifyTelemetryEvent(eventType, payload); // kind: scenario | scenario-step | bi | unknown
    // …send; never throw, never block
  }
  recordError(error: UwtTelemetryError, metadata?: UwtTelemetryMetadata): void {}
  getSessionId(): string | undefined { return undefined; }
  setUserId(userId: string | undefined): void {}   // undefined and '' both mean signed out
  getUserId(): string | undefined { return undefined; }
  flush(beacon?: boolean): void {}
}

const telemetry = uwtCreateTelemetry({ identity, destination: new MyBackendSink(), logApi });
```

Payloads arrive already redacted; the engine guards every call into the destination. A destination
that owns its sessions calls `uwtMarkSessionStart(sessionId)` when it starts one, so scenario
records carry `sessionElapsed`; without it they simply omit the field.

## 9. What reaches the wire

| Event type (`{ns}` = `com.uwt`) | When                                                    | Payload                                   |
|---------------------------------|---------------------------------------------------------|-------------------------------------------|
| `{ns}.scenario`                 | Once per scenario, at settlement                         | `UwtScenarioRecord`                       |
| `{ns}.scenario.step`            | Per closed step — only with `emitLifecycleEvents: true` | step + scenario identity                  |
| `{ns}.bi`                       | Per `track()` call (after dedup)                         | `UwtBIEvent`                              |

Every RUM event's metadata also carries `application`, `environment`, `appVersion` and, once the app
has called `setUserId`, `signedIn: true | false`. Anonymous ids are random UUIDs too, so `signedIn`
is what tells them from real users: count distinct anonymous users as distinct user ids where
`signedIn` is `false`.

A settled scenario record (abridged):

```json
{
  "scenarioId": "250514ab-…", "scenarioName": "my-app-table-load", "feature": "table",
  "status": "abandoned", "reason": "superseded",
  "startTime": "2026-09-05T11:11:04.211Z", "endTime": "2026-09-05T11:11:04.273Z",
  "delta": 62, "elapsed": 3037, "sessionElapsed": 845200, "stepCount": 1,
  "steps": [
    { "name": "scenario-start", "startOffset": 0, "stepDelta": 0, "status": "success" },
    { "name": "fetch", "startOffset": 1, "stepDelta": 61, "status": "abandoned", "reason": "superseded" },
    { "name": "scenario-end", "startOffset": 62, "stepDelta": 0, "status": "abandoned" }
  ],
  "previousStep": "fetch", "metadata": { "abandonedBy": "caller" },
  "application": "my-app", "sessionId": "…", "userId": "…"
}
```

`delta` is the duration; `elapsed` is a timeline position (ms since page load), and
`sessionElapsed` one in the RUM session (ms since the session started — it survives reloads; absent
until the session's start is known, and always absent with `suppressSessionStartEvent`, cookies off,
`localStorage` blocked, a session that began on a page in `pagesToExclude`, or a clock set back past
the session's start). Steps carry no copy: a step sits at `sessionElapsed - (elapsed -
step.elapsed)`. `scenario-start` / `scenario-end` are written by the library and don't count toward
`stepCount`. `sessionId` / `userId` appear once the RUM client has started and a user is signed in.

## 10. Debug flags and the reporter

`localStorage` keys `debugScenario`, `debugBI`, `debugLogger` (`'true'` or `'1'`; `debugLogger` also
accepts a comma-separated list of logger names). Read on every emit — no reload. `debugScenario`
also mirrors scenarios to `performance.mark/measure` (DevTools → Performance → Timings). One console
line per event actually sent: `[<application>][scenario|bi|log] …`, second argument = the exact
object handed to the destination or log provider. `uwtIsDebugEnabled(flag, name?)` reads the same
flags.

`report` (engine and destination option) receives what telemetry skips (`'error'`) or drops
(`'warn'`); `uwtConsoleReporter` prints both — typically in development only. Configuration
problems (`'config'`: a second broadcast host, RUM settings of the wrong type) are printed to the
console even without a reporter: they are never silent.

## 11. Testing

Build the engine with a recording destination; `defaultTimeoutMs: 0` keeps tests free of timers:

```ts
const events: { eventType: string; payload: Record<string, unknown> }[] = []; // reset per test

class RecordingSink extends UwtTelemetrySink {
  record(eventType: string, payload: object): void {
    events.push({ eventType, payload: payload as Record<string, unknown> });
  }
  recordError(): void {}
  getSessionId(): string | undefined { return 'session-1'; }
  setUserId(): void {}
  getUserId(): string | undefined { return undefined; }
  flush(): void {}
}

const telemetry = uwtCreateTelemetry({
  identity: { application: 'my-app-test', environment: 'test', version: '0.0.0' },
  destination: new RecordingSink(),
  logApi: new UwtNoopLogApiProvider(),
  scenarios: { defaultTimeoutMs: 0 },
  document: null // no page lifecycle in unit tests
});

// expect(events).toEqual([
//   expect.objectContaining({ eventType: 'com.uwt.scenario',
//     payload: expect.objectContaining({ scenarioName: 'my-app-customers-load', status: 'success' }) })
// ]);
```

**Code that imports the app's engine module** (`src/telemetry/telemetry.ts`) gets a test engine
from one mock of that module in the test setup file, so no spec builds the real destination (a RUM
sink's `init()` would call the broker). Mirror the module's exports; add it if the app has none:

```ts
// src/test-setup.ts — listed in the test runner's `setupFiles`
vi.mock('./telemetry/telemetry', async () => {
  const { uwtCreateTelemetry, UwtNoopLogApiProvider, UwtNoopTelemetrySink } =
    await import('@absaoss-cps/ui-watchtower');
  const destination = new UwtNoopTelemetrySink();
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

To assert on what is sent, spy on that destination and restore the spy after each test:

```ts
const record = vi.spyOn(destination, 'record');
// …drive the code
expect(record).toHaveBeenCalledWith('com.uwt.scenario',
  expect.objectContaining({ scenarioName: 'my-app-customers-load', status: 'success' }));
// BI events: 'com.uwt.bi' with eventName and metadata
```

With Jest, use `jest.mock` with `require` inside the factory. jsdom has no `BroadcastChannel`; a
fragment's tests stub it or use the recording sink instead.

## 12. Shell and fragments

In a page composed of fragments, each in its own JavaScript realm, the shell sends everything and
the fragments forward to it over a `BroadcastChannel`, so a user is one session, not one per
fragment. Each side can use any framework, or none: they exchange the same messages (the library
holds every pairing to one recorded wire format).

| Realm          | Destination                                     | RUM client and credentials          | Log store                                         |
|----------------|-------------------------------------------------|-------------------------------------|---------------------------------------------------|
| Standalone app | Its own: `UwtRumTelemetrySink`, or another sink | The app's                           | The app's                                         |
| Shell          | Its own, plus a `UwtTelemetryBroadcastHost`     | The shell's: the only one on a page | The shell's, which also stores fragments' records |
| Fragment       | `UwtBroadcastTelemetrySink`                     | None: the shell's records for it    | None: `UwtBroadcastLogApiProvider` forwards       |

```ts
// shell, after its engine: records what fragments forward
const host = new UwtTelemetryBroadcastHost({ sink: destination, logApi, channelName, enabled });

// fragment: one connection for its sink and log provider
const connection = uwtConnectBroadcastChannel({ channelName, enabled });
const telemetry = uwtCreateTelemetry({
  identity,                                   // the fragment's application, the shell's eventNamespace
  destination: new UwtBroadcastTelemetrySink({ identity, connection, enabled }),
  logApi: new UwtBroadcastLogApiProvider({ connection, enabled }),
  enabled
});
```

`channelName` is the shell's per-page-load channel, which the shell publishes and each fragment
reads (micro-frontends.md); the default, `UWT_DEFAULT_BROADCAST_CHANNEL`, is shared by every tab on
the origin. Forwarding works only between same-origin realms. A fragment reports the shell's
session and user. Whoever creates something disposes it: the engine, then the host, the sink, the
log provider and the connection, when their realm goes away. `host.received` counts accepted
messages, for verification.

## 13. Not yet released

These are in ui-watchtower #29 (open), not in core 0.1.1 or adapter 0.5.1. Use one only when the
installed package's typings have it; never wire it from this list alone:

- Fragments that follow the shell's channel by themselves, with no `channelName`.
- The X-Ray header on relative same-origin URLs, the shell's RUM client tracing nested fragments'
  requests, and `traceHeaderExcludeUrls` to keep the header off a path.
- Sending the scenario id to the backend as a request header (in the Angular adapter, an
  `HttpClient` interceptor; ngx-ui-watchtower-api.md §6).
