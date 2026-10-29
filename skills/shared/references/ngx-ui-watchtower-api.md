# ngx-ui-watchtower API reference

The public surface of `@absaoss-cps/ngx-ui-watchtower` (latest release, 0.4.0; if the installed
typings differ, they win — items marked *0.4.0+* don't exist before it). Import only from the two
entry points below — no deep imports.

## Contents

1. [Imports by entry point](#1-imports-by-entry-point)
2. [Providers](#2-providers)
3. [Identity and configuration defaults](#3-identity-and-configuration-defaults)
4. [Scenarios](#4-scenarios)
5. [BI events](#5-bi-events)
6. [Logging](#6-logging)
7. [RUM sink and credentials](#7-rum-sink-and-credentials)
8. [Custom destination](#8-custom-destination)
9. [What reaches the wire](#9-what-reaches-the-wire)
10. [Debug flags](#10-debug-flags)
11. [Testing](#11-testing)

## 1. Imports by entry point

```ts
// '@absaoss-cps/ngx-ui-watchtower' — everything except RUM
import {
  // setup
  provideUwtTelemetry, withScenarios, withBIEvents, withLogging, withRedaction,
  withTelemetryEnabled, UWT_TELEMETRY_ENABLED, // turn all telemetry off
  provideUwtTelemetrySink,          // 'broadcast' | 'noop'
  provideUwtTelemetryDestination,   // a custom sink
  provideUwtTelemetryBroadcastHost, // shells only
  UwtTelemetryBroadcastHost,        // shells: `received` counter for verification
  UWT_BROADCAST_CHANNEL, UWT_DEFAULT_BROADCAST_CHANNEL,
  UwtBroadcastLogApiProvider,       // bound by 'broadcast'; never bind it yourself
  // scenarios
  UwtScenarioTelemetryService, UwtScenario, traceScenario,
  uwtScenarioHeaderInterceptor, uwtScenarioContext, UWT_DEFAULT_SCENARIO_HEADER, // §4 backend header, 0.4.0+
  // BI
  UwtBITelemetryService,
  // logging
  UwtLoggerService, UWT_LOG_API_PROVIDER, UwtNoopLogApiProvider, UWT_LOG_LEVEL_ORDER,
  // sinks
  UwtTelemetrySink, UwtNoopTelemetrySink, uwtClassifyTelemetryEvent,
  uwtMarkSessionStart,              // custom destinations that own sessions (§8), 0.4.0+
  // debug
  uwtIsDebugEnabled,
  // redaction helpers (for custom sinks)
  uwtRedactMetadata, uwtNormalizeError, uwtScrubString, uwtRedactConfigFor
} from '@absaoss-cps/ngx-ui-watchtower';
import type {
  UwtTelemetryIdentity, UwtTelemetryMetadata, UwtTelemetryError, UwtScenarioOptions,
  UwtScenarioOutcome, UwtScenarioRecord, UwtScenarioStatus, UwtTraceScenarioOptions,
  UwtBIEventName, UwtLogApiProvider, UwtLogQuery, UwtLogRecord, UwtLogDetail,
  UwtScenarioHeaderOptions,
  // registries augmented by telemetry.schema.ts
  UwtScenarioNames, UwtScenarioSteps, UwtBIEventNames, UwtLoggerNames
} from '@absaoss-cps/ngx-ui-watchtower';

// '@absaoss-cps/ngx-ui-watchtower/rum' — the whole entry point, eight names
import {
  provideUwtTelemetryRumSink, UwtRumTelemetrySink, UWT_RUM_CREDENTIALS_PROVIDER
} from '@absaoss-cps/ngx-ui-watchtower/rum';
import type {
  UwtRumCredentialsProvider, UwtRumBootstrap, UwtRumCredentials, UwtRumAppMonitorConfig,
  UwtRumSinkOptions // 0.4.0+
} from '@absaoss-cps/ngx-ui-watchtower/rum';
```

Use `import type` for the credential types so a credentials provider carries no runtime dependency
on the `/rum` entry.

## 2. Providers

All return `EnvironmentProviders`; they work in `ApplicationConfig.providers` and NgModule
`providers` alike.

| Call                                                   | Registers                                                                                                         |
|--------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------|
| `provideUwtTelemetry(identity, ...features)`           | Identity + default config for every concern; features override one concern each (later wins). **No destination.** |
| `provideUwtTelemetryRumSink(options?)` (`/rum`)        | The AWS CloudWatch RUM destination. Needs `UWT_RUM_CREDENTIALS_PROVIDER`. Starts the client from a non-awaited initializer, so a slow broker never delays first paint. `options`: `UwtRumSinkOptions` (`xRayExcludeUrls`, §7) |
| `provideUwtTelemetrySink('noop')`                      | Explicit "ship nowhere" destination                                                                                |
| `provideUwtTelemetrySink('broadcast', { channelName? })` | Forwards to a shell's broadcast host. Also binds `UWT_LOG_API_PROVIDER` to `UwtBroadcastLogApiProvider`. Created at startup. Nested in the shell's page, it follows the shell's channel by itself; set `channelName` only outside the page (a popup) |
| `provideUwtTelemetryDestination(SinkClass, { init? })` | Any custom sink; `init(sink)` runs once from an initializer, fail-open                                            |
| `provideUwtTelemetryBroadcastHost(channelName?)`       | Shell-side receiver for fragments; constructed eagerly. Publishes its channel for the fragments nested in its page. Injects `UWT_LOG_API_PROVIDER` — a host without a log provider fails at bootstrap |

Exactly one destination per realm: two different ones throw at bootstrap; the same one listed twice
is fine. Who injects `UWT_LOG_API_PROVIDER`: only `UwtLoggerService` and the broadcast host.

**Turning telemetry off** — `withTelemetryEnabled(value | () => boolean)`, a feature of
`provideUwtTelemetry` (token `UWT_TELEMETRY_ENABLED`, default `true`). The factory runs in an
injection context; the value is read once at startup (no runtime toggling, e.g. for consent). The
providers stay the same — a destination and, where required, a log provider are still needed, so
wiring fails the same way everywhere. When off:

- `start()` returns an inert `UwtScenario` (own `id`, the given `name`, chainable) that records
  nothing and **never settles**; `find` / `findByName` / `getActive` find nothing, `settled$` never
  emits, `traceScenario` passes values and errors through.
- `track()` does nothing; `getLogger()` returns an inert logger; `query()` resolves `[]` without
  calling the log provider.
- RUM sink never starts (no credentials fetch, no SDK download), the broadcast sink opens no
  channel, the broadcast host neither listens nor joins leader election, destination `init` is
  skipped. The bundle doesn't shrink.

`provideUwtTelemetrySink('noop')` is not the same: it only stops shipping.

## 3. Identity and configuration defaults

```ts
interface UwtTelemetryIdentity {
  application: string;      // unique per app and per fragment; becomes a session attribute
  environment: string;      // 'dev' | 'qa' | 'prod' …
  version: string;
  eventNamespace?: string;  // default 'com.uwt' → com.uwt.scenario, com.uwt.scenario.step, com.uwt.bi
}
```

| Feature           | Options and defaults                                                                                                                     |
|-------------------|------------------------------------------------------------------------------------------------------------------------------------------|
| `withScenarios()` | `defaultTimeoutMs: 30_000` (0 disables), `emitLifecycleEvents: false`, `maxSteps: 50`, `userTimings: false`, `markCleanupFallbackMs: 300_000`, `redact: true` |
| `withBIEvents()`  | `dedupWindowMs: 400`, `dedupMaxKeys: 100`, `redact: true`                                                                                |
| `withLogging()`   | `minLevel: 'log'` (`'log' \| 'warn' \| 'error'`), `levels?` per logger name, `mirrorErrorsToRum: false`, `redact: true`                   |
| `withRedaction()` | `extraKeyPatterns: []`, `maxStringLength: 1024`, `maxKeys: 50`, `maxStackLength: 2048`, `includeStack: true`, `stripUrlQuery: true`, `scanValuePatterns: []` (`'email' \| 'creditCard' \| 'ssn' \| 'ipv4' \| 'phone'`), `extraValuePatterns: []`, `extraValueTransforms: []` |

Always on, even with `redact: false`: the credential key denylist (`password`, `secret`, `token`,
`auth`, `credential`, `cookie`, `api-key`, `bearer`, `jwt`, `signature`, `session-key`, `ssn` —
substring, case-insensitive), the size caps, error normalization to `{ name, message, stack? }`, and
`extraValueTransforms`. URL query strings and fragments are stripped; **path segments are not** —
so an `HttpErrorResponse` passed as `error` sends its message, which quotes the request URL path
(ids included). Send its class and status instead (`safeHttpFailure` in the integration patterns).

## 4. Scenarios

```ts
const scenario = inject(UwtScenarioTelemetryService).start({
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
| `settle(status, outcome?, error?)`            | For adapters mapping an external status; prefer the named methods                             |
| `id`, `name`, `status`, `isSettled`, `delta`  | `id` is the correlation id                                                                     |
| `toRecord()`                                  | Deep-cloned snapshot; `status` undefined while running                                         |

`UwtScenarioOutcome = { message?, reason?, metadata?, statusCode?, error? }`. `reason` is a short,
low-cardinality grouping key (`'superseded'`, `'no-results'`). Settling is absorbing: the first
settle wins, later calls are ignored. Timeout settles as `timeout` automatically.

`traceScenario(scenario, options?)` — RxJS operator: `complete()` on source completion,
`fail({ error })` on error, `cancel(cancelOutcome)` on unsubscribe before either. So anything
downstream that stops after the first value — `take(1)`/`first()` after it, `firstValueFrom()` on
it — records `abandoned`; limit upstream and await with `lastValueFrom()`.

```ts
interface UwtTraceScenarioOptions<T> {
  outcome?: (value: T) => UwtScenarioOutcome | void;   // from the last emitted value
  cancelOutcome?: UwtScenarioOutcome | (() => UwtScenarioOutcome | void);
}
```

**Sending the scenario to the backend** (*0.4.0+*). Opt-in, per request:

```ts
provideHttpClient(withInterceptors([uwtScenarioHeaderInterceptor()])); // { headerName? } renames it

this.http.get('/api/customers', { context: uwtScenarioContext(scenario) })
  .pipe(traceScenario(scenario)).subscribe();
```

Marked requests get `X-Uwt-Scenario-Id: <scenario.id>` (`UWT_DEFAULT_SCENARIO_HEADER`) — only
same-origin ones, only while telemetry is on, never unmarked ones. It only adds the header: errors
pass through and settling stays with the caller. List it after any interceptor that rewrites URLs
(e.g. one prefixing an API host). `uwtScenarioContext` returns a new `HttpContext`; add other tokens
with `.set()`. The backend logs the header as `scenarioId` and adds it to its X-Ray trace as the
`scenarioId` annotation (letters, digits, underscores only). Don't mark a request to an endpoint
that redirects to another origin (§7).

Service extras: `find(id)`, `findByName(name)`, `getActive()`, and `settled$` (an observable of
deep-cloned settled records). On `pagehide` every in-flight scenario settles as `abandoned`
(`abandonedBy: 'page-hidden'`); on `visibilitychange` to hidden the sink flushes and scenarios keep
running. More than 50 active scenarios logs a dev-mode leak warning.

## 5. BI events

```ts
inject(UwtBITelemetryService).track(
  'my-app-export-clicked',                       // declared in UwtBIEventNames
  { format: 'csv' },                             // flat metadata
  { scenarioId: scenario.id, feature: 'reports' } // optional: join to a journey
);
```

What the sink receives is always `record('{ns}.bi', event)` — `com.uwt.bi` by default — with

```ts
event = { eventName, eventTime /* ISO string */, metadata?, scenarioId?, feature?, application, sessionId?, userId? }
```

The name is in **`eventName`** (not `name`). A test with a recording sink asserts on
`payload.eventName` and `payload.metadata`.

Identical events (name + scenarioId + feature + metadata) within 400 ms collapse into
one — no click throttling needed. Type any parameter that carries an event name as `UwtBIEventName`,
not `string`, or it stops compiling once the registry is augmented.

## 6. Logging

Only with a log backend bound to `UWT_LOG_API_PROVIDER`.

```ts
private readonly logger = inject(UwtLoggerService).getLogger('my-app-checkout'); // declared in UwtLoggerNames

this.logger.log('Submitting order');
this.logger.warn('Retrying payment', { metadata: { attempt: 2 } });
this.logger.error('Payment failed', { error, correlationId: scenario.id, context: 'CheckoutService' });
// never a raw HttpErrorResponse as `error` — its message quotes the request URL (§3)

inject(UwtLoggerService).query({ correlationId: scenario.id }); // → your provider's query()
```

`UwtLogDetail = { context?, metadata?, error?, correlationId? }`. Loggers are named — there is no
unnamed `log()` on the service. `correlationId = scenario.id` is what joins log lines to a journey.

```ts
interface UwtLogApiProvider {
  send(record: UwtLogRecord): void;          // must not throw; batching/retries/auth are yours
  query(filter: UwtLogQuery): Promise<UwtLogRecord[]>;
  flush?(): void;                            // called when the page is hidden or closed
}
interface UwtLogQuery { correlationId?; logger?; minLevel?; from?; to?; limit? }
```

`UwtNoopLogApiProvider` is the explicit "no log backend": discards records, `query()` returns `[]`.

## 7. RUM sink and credentials

```ts
interface UwtRumCredentialsProvider {
  /** Called at startup and again ~5 min before each credential expiry. `null` disables RUM. */
  load(): Promise<UwtRumBootstrap | null>;
}
interface UwtRumBootstrap { config: UwtRumAppMonitorConfig; credentials?: UwtRumCredentials }
interface UwtRumCredentials { accessKeyId; secretAccessKey; sessionToken; expiration } // all strings
```

`UwtRumAppMonitorConfig` requires `applicationId`, `region`, `applicationVersion`; it mirrors the
`aws-rum-web` config otherwise (`sessionSampleRate`, `sessionEventLimit` (default 200),
`telemetries`, `allowCookies`, `disableAutoPageView`, `pageIdFormat`, `pagesToInclude/Exclude`,
`enableXRay`, `endpoint`, …). Deliberately absent: `identityPoolId`/`guestRoleArn` (Cognito — use
your broker), `endpointUrl`, `sessionId`, `userId`. Leave `telemetries` out of broker JSON where
you can: a list replaces the library's default, whose `http` entry adds the X-Ray header to
same-origin requests, relative URLs (`/api/...`) included, through a `RegExp` — and in a shell, to
nested fragments' requests too. If the broker sends one, take names only
(`['errors', 'http']`): settings that need a `RegExp` or a function (`pagesToExclude`, or
`urlsToExclude`, `ignore` inside `telemetries`, and `addXRayTraceIdHeader` unless it's a boolean)
can't travel as JSON. If one arrives as a string, the sink doesn't start RUM for the page and warns
in the console (each setting and its expected type, never the value), rather than let the SDK throw
or record what the filters should exclude. Set them in code.

A same-origin endpoint that redirects to another origin (a download that 302s to S3, an SSO
login) passes the X-Ray header on, and the request fails unless that origin allows
`x-amzn-trace-id` in CORS. Fix it at the target, or keep the header off that path in code:
`provideUwtTelemetryRumSink({ xRayExcludeUrls: [/\/files\//] })` (*0.4.0+*; matched against the resolved
URL; covers fragments too; only with the default `telemetries`).

User identity: `sink.setUserId(id)` takes a UUID — RUM's API accepts nothing else (MSAL's
`localAccountId`, not `homeAccountId`; an OIDC `sub` often isn't one). `undefined` or `''` signs out:
a new session with a new anonymous id, but only when someone was signed in (*0.4.0+*; before, every
call started one), so it can follow an auth state stream directly. Call it as early as possible —
events carry `signedIn` only after the first call (§9).

Return values of `load()`:

| Return                      | Effect                                                                                       |
|-----------------------------|----------------------------------------------------------------------------------------------|
| `null`                      | RUM off for the rest of the page; mid-session it tears the running client down                |
| throws / rejects            | Retried. At startup (*0.4.0+*; before, RUM went off for the page) with a random wait that grows from up to 1 s to up to 60 s, for 5 minutes, events buffered (at most 100); on a refresh every 30 s, keeping the current credentials |
| `{ config, credentials }`   | Normal path                                                                                  |
| `{ config }` only           | Only for an app monitor allowing unauthenticated access                                       |

`UwtRumTelemetrySink.recordPageView(pageId)` exists for apps that set `disableAutoPageView: true`
and record page ids (route templates) themselves — never alongside automatic page views.

## 8. Custom destination

```ts
@Injectable()
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

providers: [provideUwtTelemetryDestination(MyBackendSink, { init: (s) => s.start() })]
```

Payloads arrive already redacted; the library guards every call into the sink. A destination that
owns its sessions calls `uwtMarkSessionStart(sessionId)` when it starts one, so scenario records carry
`sessionElapsed`; without it they simply omit the field.

## 9. What reaches the wire

| Event type (`{ns}` = `com.uwt`) | When                                                    | Payload                                   |
|---------------------------------|---------------------------------------------------------|-------------------------------------------|
| `{ns}.scenario`                 | Once per scenario, at settlement                         | `UwtScenarioRecord`                       |
| `{ns}.scenario.step`            | Per closed step — only with `emitLifecycleEvents: true` | step + scenario identity                  |
| `{ns}.bi`                       | Per `track()` call (after dedup)                         | `UwtBIEvent`                              |

Every RUM event's metadata also carries `application`, `environment`, `appVersion` and, once the app
has called `setUserId`, `signedIn: true | false` (*0.4.0+*). Anonymous ids are random UUIDs too, so
`signedIn` is what tells them from real users: count distinct anonymous users as distinct user ids
where `signedIn` is `false`.

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

`delta` is the duration; `elapsed` is a timeline position (ms since page load), and `sessionElapsed`
(*0.4.0+*) one in the RUM session (ms since the session started — it survives reloads; absent until
the session's start is known, and always absent with `suppressSessionStartEvent`, cookies off,
`localStorage` blocked, a session that began on a page in `pagesToExclude`, or a clock set back past
the session's start). Steps carry no copy:
a step sits at `sessionElapsed - (elapsed - step.elapsed)`.
`scenario-start` / `scenario-end` are written by the library and don't count toward `stepCount`. `sessionId` / `userId`
appear once the RUM client has started and a user is signed in.

## 10. Debug flags

`localStorage` keys `debugScenario`, `debugBI`, `debugLogger` (`'true'` or `'1'`; `debugLogger` also
accepts a comma-separated list of logger names). Read on every emit — no reload. `debugScenario`
also mirrors scenarios to `performance.mark/measure` (DevTools → Performance → Timings). One console
line per event actually sent: `[<application>][scenario|bi|log] …`, second argument = the exact
object handed to the sink or log provider. `uwtIsDebugEnabled(flag, name?)` reads the same flags.

## 11. Testing

Minimal providers:

```ts
providers: [
  provideUwtTelemetry(
    { application: 'my-app-test', environment: 'test', version: '0.0.0' },
    withScenarios({ defaultTimeoutMs: 0 })
  ),
  provideUwtTelemetrySink('noop'),
  { provide: UWT_LOG_API_PROVIDER, useClass: UwtNoopLogApiProvider } // only if UwtLoggerService is used
]
```

Recording sink, to assert on what is sent (all six methods):

```ts
const events: { eventType: string; payload: Record<string, unknown> }[] = []; // reset in beforeEach: events.length = 0

@Injectable()
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

providers: [
  provideUwtTelemetry({ application: 'my-app-test', environment: 'test', version: '0.0.0' }),
  provideUwtTelemetryDestination(RecordingSink)
]

// expect(events).toEqual([
//   expect.objectContaining({ eventType: 'com.uwt.scenario',
//     payload: expect.objectContaining({ scenarioName: 'my-app-customers-load', status: 'success' }) })
// ]);
```
