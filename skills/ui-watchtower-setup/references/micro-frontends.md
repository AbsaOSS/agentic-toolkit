# Micro-frontends: shell hosts, fragments forward

Use when the app embeds fragments that run in their own JavaScript realm (Web Fragments, same-origin
iframes, separately bootstrapped Angular apps), or is such a fragment. Not for a Module Federation
remote loaded through `loadChildren`/`loadComponent`: it runs in the host's injector — give it no
providers of its own.

## Why

Each realm has its own Angular injector, so each would build its own AWS RUM client: one visitor
becomes N sessions with N event budgets, N credential fetches and N SDK downloads. So **exactly one
realm — the shell — owns the RUM client; fragments forward** to it over a same-origin
`BroadcastChannel`. Application code is identical in both; only the providers differ.

**Version.** This setup needs ngx-ui-watchtower **0.5.0 or later** in the shell and every fragment:
from 0.5.0 (ui-watchtower #29), fragments find the shell's channel themselves and the shell traces
their HTTP. Install the latest and check its version. While the shell or any fragment is on 0.4.x
or older (0.4.0 is the latest release until 0.5.0 ships), use the manual pattern under "Before
0.5.0" for the whole page. Otherwise a fragment falls back to the shared default channel, which the shell
doesn't listen on, and its telemetry is silently lost.

## Shell

```ts
import { inject } from '@angular/core';
import {
  UWT_LOG_API_PROVIDER,
  UwtNoopLogApiProvider,
  provideUwtTelemetry,
  provideUwtTelemetryBroadcastHost
} from '@absaoss-cps/ngx-ui-watchtower';
import {
  UWT_RUM_CREDENTIALS_PROVIDER,
  UwtRumTelemetrySink,
  provideUwtTelemetryRumSink
} from '@absaoss-cps/ngx-ui-watchtower/rum';
import {
  provideRouteNavigationTelemetry,
  ROUTE_PAGE_VIEW_RECORDER
} from './telemetry/route-navigation-telemetry.service';

// One random channel per page load. randomUUID needs a secure context, hence the fallback;
// skipped during server rendering (undefined keeps the default channel there).
const channelId =
  typeof window === 'undefined'
    ? undefined
    : `ngx-ui-watchtower-${crypto.randomUUID?.() ?? `${Date.now()}-${Math.random().toString(36).slice(2)}`}`;

providers: [
  provideUwtTelemetry({ application: 'shell', environment, version }),
  provideUwtTelemetryRumSink(),
  { provide: UWT_RUM_CREDENTIALS_PROVIDER, useExisting: AppRumCredentialsProvider },
  // Route tracking and page views under the route template (SKILL.md Step 6)
  provideRouteNavigationTelemetry(),
  {
    provide: ROUTE_PAGE_VIEW_RECORDER,
    useFactory: () => {
      const rum = inject(UwtRumTelemetrySink);
      return (route: string) => rum.recordPageView(route);
    }
  },
  provideUwtTelemetryBroadcastHost(channelId),
  // Required by the host. Fragments' log records are shipped by the shell's log provider;
  // with no log backend, say so explicitly:
  { provide: UWT_LOG_API_PROVIDER, useClass: UwtNoopLogApiProvider }
];
```

- **Provide the host now**, even if no fragment forwards yet — a host with no fragments just sits
  idle, and it must be listening before the first fragment sends.
- **Per-tab channel id is required.** `BroadcastChannel` and the host's leader election are
  origin-wide. On the shared default channel, a second tab's fragments get recorded through the
  first tab's RUM client — wrong page, wrong context. Generate the id once per page load, never per
  fragment or per navigation.
- **Nothing to publish** (*0.5.0+*). The host leaves the channel on the shell's window, and
  fragments nested in the page (Web Fragments, same-origin iframes) find it themselves. Don't add a
  `window.__uwtTelemetryChannel` global, except below 0.5.0 ("Before 0.5.0", below).
- **Fragment HTTP is traced by the shell** (*0.5.0+*). The shell's RUM client also patches each
  nested fragment's `fetch`/XHR: fragment requests get the X-Ray header and RUM HTTP events in the
  shell's session, with nothing to configure. They count toward the shell's session event budget
  (`sessionEventLimit`, default 200). Before 0.5.0, fragment requests aren't traced.
- The contract you hand to fragment teams states the shell's `eventNamespace` (`com.uwt` when it
  sets none) — fragments must use the same one.

## Fragment — the contract to hand to fragment teams

```ts
import { provideUwtTelemetry, provideUwtTelemetrySink } from '@absaoss-cps/ngx-ui-watchtower';

providers: [
  provideUwtTelemetry({
    application: 'cart', // must differ from the shell
    environment,
    version,
    eventNamespace: 'com.uwt' // the shell's — must match
  }),
  provideUwtTelemetrySink('broadcast') // no channel: it follows the shell's (0.5.0+)
];
```

Below 0.5.0, add the `UWT_BROADCAST_CHANNEL` factory from "Before 0.5.0" below.

The fragment's sink and log provider look the shell's channel up by walking `window.parent`, once,
at startup. So **the shell's host must exist before any fragment boots**: a fragment that boots first
falls back to the shared default channel and ships nothing the shell hears. A shell that renders its
fragments after it bootstraps (Web Fragments does) guarantees this. Set `UWT_BROADCAST_CHANNEL` or
`channelName` only in a realm outside the shell's page (a popup window), and then to the shell's id.

If the shell sends the scenario header (API reference §4, *0.5.0+*), the fragment adds
`uwtScenarioHeaderInterceptor()` to its own `provideHttpClient` too: interceptors don't cross realms.

| Must match the shell | `eventNamespace` (ask for the shell's value if the shell isn't in this repo; default `com.uwt`); `withTelemetryEnabled(...)` — the switch is per realm, so a fragment left on beside a shell that is off still opens a channel nobody hosts. The channel name follows the shell by itself |
|----------------------|---------------------------------------------------------------------------------------------------------|
| **Must differ**      | `application` — every forwarded event is stamped with it, which is how fragments are told apart         |
| **Never provide**    | `provideUwtTelemetryRumSink()`, `UWT_RUM_CREDENTIALS_PROVIDER`, `provideUwtTelemetryBroadcastHost()`, `UWT_LOG_API_PROVIDER` (`'broadcast'` already binds it to the forwarding provider) |
| **Never install**    | `aws-rum-web`                                                                                           |

Inside a fragment:

- `getSessionId()` is `undefined` until the shell answers the identity handshake — don't assert on it
  at bootstrap. Work is still correlated by `scenarioId`.
- The shell's host stamps its own current `sessionId` and `userId` on every scenario, step, BI and
  log record a fragment forwards, and re-measures `sessionElapsed` if the session changed
  (*0.4.0+*). So fragment records carry the shell's session and user even when the fragment's own
  copy lags. While the shell's RUM client hasn't started, there is no session to stamp.
- Log lines go to the shell's log provider; `logger.query()` is answered by the shell.
- Don't call `setUserId()`: it is forwarded and changes the shell's user. The shell owns user
  identity.
- Paint observation doesn't work (a hidden iframe never paints) — settle with `complete()`.

## Before 0.5.0: manual channel pattern

On 0.4.x and older the shell publishes the channel itself and each fragment reads it. Use this
whenever the shell or any fragment is below 0.5.0, including a new setup while 0.4.x is the latest
release:

```ts
// shell, next to channelId above
declare global { interface Window { __uwtTelemetryChannel?: string } }
if (channelId) window.__uwtTelemetryChannel = channelId;

// fragment: the nearest window that published one, else a private channel nobody hosts
// (never undefined, which would select the shared default channel)
function shellChannelName(): string {
  let w: Window | undefined = typeof window === 'undefined' ? undefined : window;
  while (w) {
    try {
      const shell = w.__uwtTelemetryChannel;
      if (shell) return shell;
    } catch {
      // a cross-origin ancestor: its parent is still readable
    }
    w = w === w.parent ? undefined : w.parent;
  }
  return `ngx-ui-watchtower-unhosted-${Date.now().toString(36)}-${Math.random().toString(36).slice(2)}`;
}
providers: [/* … */ { provide: UWT_BROADCAST_CHANNEL, useFactory: shellChannelName }];
```

**The shell must publish the id before any fragment boots**: the fragment's sink reads it once, so
an early fragment ships nothing for the whole page. A shell that renders its fragments after it
bootstraps (Web Fragments does) guarantees this.

That keeps working on 0.5.0 (an explicit channel wins), but shells and fragments deploy separately,
so remove it in this order: upgrade every fragment to 0.5.0 and drop its factory first, then remove
the shell's global. A fragment still below 0.5.0 reads only that global.

## Verifying

- On a first page load the shell's `inject(UwtTelemetryBroadcastHost).received` counter grows, also
  when the shell runs inside another app's iframe.
- On 0.5.0+, a fragment's API request carries `X-Amzn-Trace-Id` in DevTools → Network.
- Two tabs have two different channel ids.
- With the debug flags on, lines are prefixed per realm: `[shell][scenario] …`, `[cart][bi] …`.
- `BroadcastChannel` is same-origin only: a fragment served from another origin forwards nothing,
  silently.
