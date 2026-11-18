# ngx-ui-watchtower API reference (Angular adapter)

`@absaoss-cps/ngx-ui-watchtower` (latest release, 0.5.0; if the installed typings differ, they win)
is the Angular adapter over the core `@absaoss-cps/ui-watchtower`: providers, injectable services
and Observables around the same engine. Installing it installs the core — never add the core to an
Angular app yourself. **Behaviour** (identity and defaults, scenarios, BI events, logging, the RUM
broker contract, what reaches the wire, debug flags, shells and fragments) is the core's:
`ui-watchtower-api.md` §3–§12. This file covers only the Angular wiring. Items marked *0.4.0+*
don't exist in older releases (§8). Import only from the two entry points below — no deep imports.

## Contents

1. [Imports by entry point](#1-imports-by-entry-point)
2. [Providers](#2-providers)
3. [Turning telemetry off](#3-turning-telemetry-off)
4. [Services, and the core they wrap](#4-services-and-the-core-they-wrap)
5. [Custom destination](#5-custom-destination)
6. [Not yet released](#6-not-yet-released)
7. [Testing](#7-testing)
8. [Older releases](#8-older-releases)

## 1. Imports by entry point

```ts
// '@absaoss-cps/ngx-ui-watchtower' — everything except RUM
import {
  // setup
  provideUwtTelemetry, withScenarios, withBIEvents, withLogging, withRedaction,
  withTelemetryEnabled, UWT_TELEMETRY_ENABLED, // turn all telemetry off (§3)
  provideUwtTelemetrySink,          // 'broadcast' | 'noop'
  provideUwtTelemetryDestination,   // a custom sink (§5)
  provideUwtTelemetryBroadcastHost, // shells only
  UwtTelemetryBroadcastHost,        // shells: `received` counter for verification
  UWT_BROADCAST_CHANNEL, UWT_DEFAULT_BROADCAST_CHANNEL,
  UwtBroadcastLogApiProvider,       // bound by 'broadcast'; never bind it yourself
  // scenarios
  UwtScenarioTelemetryService, UwtScenario, traceScenario,
  // BI
  UwtBITelemetryService,
  // logging
  UwtLoggerService, UWT_LOG_API_PROVIDER, UwtNoopLogApiProvider, UWT_LOG_LEVEL_ORDER,
  // sinks
  UwtTelemetrySink, UwtNoopTelemetrySink, uwtClassifyTelemetryEvent,
  uwtMarkSessionStart,              // custom destinations that own sessions (§5), 0.4.0+
  // debug
  uwtIsDebugEnabled,
  // redaction helpers (for custom sinks)
  uwtRedactMetadata, uwtNormalizeError, uwtScrubString, uwtRedactConfigFor
} from '@absaoss-cps/ngx-ui-watchtower';
import type {
  UwtTelemetryIdentity, UwtTelemetryMetadata, UwtTelemetryError, UwtScenarioOptions,
  UwtScenarioOutcome, UwtScenarioRecord, UwtScenarioStatus, UwtTraceScenarioOptions,
  UwtBIEventName, UwtLogApiProvider, UwtLogQuery, UwtLogRecord, UwtLogDetail,
  // registries augmented by telemetry.schema.ts
  UwtScenarioNames, UwtScenarioSteps, UwtBIEventNames, UwtLoggerNames
} from '@absaoss-cps/ngx-ui-watchtower';

// '@absaoss-cps/ngx-ui-watchtower/rum' — the whole entry point
import {
  provideUwtTelemetryRumSink, UwtRumTelemetrySink, UWT_RUM_CREDENTIALS_PROVIDER
} from '@absaoss-cps/ngx-ui-watchtower/rum';
import type {
  UwtRumCredentialsProvider, UwtRumBootstrap, UwtRumCredentials, UwtRumAppMonitorConfig
} from '@absaoss-cps/ngx-ui-watchtower/rum';
```

Names are declared on `'@absaoss-cps/ngx-ui-watchtower'` (`declare module …`); the adapter
re-exports the core's registries, so that reaches them. Use `import type` for the credential types,
so a credentials provider carries no runtime dependency on `/rum`.

## 2. Providers

All return `EnvironmentProviders`; they work in `ApplicationConfig.providers` and NgModule
`providers` alike.

| Call                                                   | Registers                                                                                                         |
|--------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------|
| `provideUwtTelemetry(identity, ...features)`           | Identity + default config for every concern; `withScenarios()`, `withBIEvents()`, `withLogging()` and `withRedaction()` override one concern each (later wins), with the core's options (core §3). **No destination.** |
| `provideUwtTelemetryRumSink()` (`/rum`)                | The AWS CloudWatch RUM destination (core §7). Needs `UWT_RUM_CREDENTIALS_PROVIDER`. Starts the client from a non-awaited initializer, so a slow broker never delays first paint |
| `provideUwtTelemetrySink('noop')`                      | Explicit "ship nowhere" destination                                                                                |
| `provideUwtTelemetrySink('broadcast', { channelName? })` | Forwards to a shell's broadcast host (core §12). Also binds `UWT_LOG_API_PROVIDER` to `UwtBroadcastLogApiProvider`. Set the shell's per-page-load channel, with `channelName` or a `UWT_BROADCAST_CHANNEL` provider (micro-frontends.md) |
| `provideUwtTelemetryDestination(SinkClass, { init? })` | Any custom sink (§5); `init(sink)` runs once from an initializer, fail-open                                       |
| `provideUwtTelemetryBroadcastHost(channelName?)`       | Shell-side receiver for fragments; constructed eagerly. Injects `UWT_LOG_API_PROVIDER` — a host without a log provider fails at bootstrap |

Exactly one destination per realm: two different ones throw at bootstrap; the same one listed twice
is fine. Who injects `UWT_LOG_API_PROVIDER`: only `UwtLoggerService` and the broadcast host. The
adapter reads `PLATFORM_ID` itself, so server rendering needs nothing extra: no page listeners,
no RUM client, no channel on the server.

## 3. Turning telemetry off

`withTelemetryEnabled(value | () => boolean)`, a feature of `provideUwtTelemetry` (token
`UWT_TELEMETRY_ENABLED`, default `true`). The factory runs in an injection context; the value is
read once at startup. The providers stay the same — a destination and, where required, a log
provider are still needed, so wiring fails the same way everywhere. Off behaves as the core's
`enabled: false` (core §2): inert scenarios that never settle, `settled$` never emits, no tracking,
inert loggers, no RUM start, no channel, no host election, destination `init` skipped.

`provideUwtTelemetrySink('noop')` is not the same: it only stops shipping.

## 4. Services, and the core they wrap

Root services, one per concern, each built on the core's class for it. Inject them where the
telemetry is needed — never behind an app-level facade.

| Inject                        | Core equivalent (core §)         | Members                                                                 |
|-------------------------------|----------------------------------|-------------------------------------------------------------------------|
| `UwtScenarioTelemetryService` | `telemetry.scenarios` (§4)       | `start(options)`, `find`, `findByName`, `getActive`; `settled$`: an Observable of settled records, listening only while subscribed |
| `UwtBITelemetryService`       | `telemetry.bi` (§5)              | `track(name, metadata?, detail?)`                                        |
| `UwtLoggerService`            | `telemetry.logging` (§6)         | `getLogger(name)`, `query(filter?)`                                      |
| `UwtTelemetrySink`            | the destination (§7, §8)          | `setUserId(id)` for sign-in and sign-out                                  |

```ts
private readonly scenarios = inject(UwtScenarioTelemetryService);
private readonly bi = inject(UwtBITelemetryService);
private readonly logger = inject(UwtLoggerService).getLogger('my-app-checkout');

const scenario = this.scenarios.start({ name: 'my-app-customers-load' });
this.http.get('/api/customers')
  .pipe(traceScenario(scenario), takeUntilDestroyed(this.destroyRef))
  .subscribe();
```

`traceScenario` from this package is the core's `/rxjs` operator (core §4), reporting in development
mode. Failures and dropped data are printed in development mode only, configuration problems
always, prefixed `[ngx-ui-watchtower]`.

## 5. Custom destination

```ts
@Injectable()
export class MyBackendSink extends UwtTelemetrySink {
  // the six methods of core §8
}

providers: [provideUwtTelemetryDestination(MyBackendSink, { init: (s) => s.start() })]
```

`UwtTelemetrySink` is the destination's token as well as its base class: inject it to reach the
running destination (e.g. `setUserId`).

## 6. Not yet released

In ui-watchtower #29 (open), not in 0.5.0. Use one only when the installed typings export it; never
wire it from this list alone:

- `uwtScenarioHeaderInterceptor()`, `uwtScenarioContext(scenario)`, `UWT_DEFAULT_SCENARIO_HEADER`,
  `UwtScenarioHeaderOptions`: an `HttpClient` interceptor that sends `X-Uwt-Scenario-Id` on requests
  marked with `{ context: uwtScenarioContext(scenario) }` (same-origin only, only while telemetry is
  on), for a backend that logs it as `scenarioId`.
- `provideUwtTelemetryRumSink({ traceHeaderExcludeUrls })` (`UwtRumSinkOptions`): keeps the trace
  header off a path.
- `provideUwtTelemetrySink('broadcast')` following the shell's channel by itself; the X-Ray header
  on relative same-origin URLs (in 0.5.0, only absolute ones get it, so most `HttpClient` calls
  don't); and the shell's RUM client tracing nested fragments' requests.

## 7. Testing

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

To assert on what is sent, decorate core §11's `RecordingSink` with `@Injectable()` and provide it
with `provideUwtTelemetryDestination(RecordingSink)` in place of `'noop'`. A missing provider fails
with `NG0201` when the service is injected.

## 8. Older releases

Setup installs the newest release that fits the app's Angular (`npm view … peerDependencies`).
Below 0.4.0:

- `traceScenario` recorded a teardown after a value as `abandoned`: limit upstream and await with
  `lastValueFrom()`.
- A failed RUM start turned RUM off for the page (no retry), and RUM settings of the wrong type made
  the SDK throw.
- Every `setUserId(undefined)` started a new session; scenario records had no `sessionElapsed`; BI
  events had no `sessionId`/`userId`; `uwtMarkSessionStart` didn't exist; `track()` had an
  `eventType` option (removed in 0.4.0).
