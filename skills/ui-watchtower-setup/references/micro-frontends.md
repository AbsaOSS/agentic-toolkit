# Micro-frontends: shell hosts, fragments forward

Use when the app embeds fragments that run in their own JavaScript realm (Web Fragments, same-origin
iframes, separately bootstrapped Angular apps), or is such a fragment.

## Why

Each realm has its own Angular injector, so each would build its own AWS RUM client: one visitor
becomes N sessions with N event budgets, N credential fetches and N SDK downloads. So **exactly one
realm — the shell — owns the RUM client; fragments forward** to it over a same-origin
`BroadcastChannel`. Application code is identical in both; only the providers differ.

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

declare global {
  interface Window {
    __uwtTelemetryChannel?: string;
  }
}

/**
 * A random id for this page load. `crypto.randomUUID` exists only in secure contexts (HTTPS,
 * localhost); `getRandomValues` works everywhere crypto does. Never throws — a failure here would
 * stop the shell from booting.
 */
function newChannelId(): string {
  const c = globalThis.crypto;
  if (typeof c?.randomUUID === 'function') {
    return `ngx-ui-watchtower-${c.randomUUID()}`;
  }
  if (typeof c?.getRandomValues === 'function') {
    const bytes = c.getRandomValues(new Uint8Array(16));
    const hex = Array.from(bytes, (b) => b.toString(16).padStart(2, '0')).join('');
    return `ngx-ui-watchtower-${hex}`;
  }
  return `ngx-ui-watchtower-${Date.now().toString(36)}-${Math.random().toString(36).slice(2)}`;
}

// One channel per page load, at module scope so it exists before any fragment boots. Browser-only:
// this module is also evaluated during server rendering, where the host is a no-op anyway.
const channelId = typeof window === 'undefined' ? undefined : newChannelId();
if (channelId) {
  window.__uwtTelemetryChannel = channelId;
}

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
- Publish it on `window`, not `sessionStorage` (copied into duplicated tabs) or a query parameter
  (fragments share the shell's `location`).

## Fragment — the contract to hand to fragment teams

```ts
import {
  UWT_BROADCAST_CHANNEL,
  provideUwtTelemetry,
  provideUwtTelemetrySink
} from '@absaoss-cps/ngx-ui-watchtower';

declare global {
  interface Window {
    __uwtTelemetryChannel?: string;
  }
}

/**
 * The shell's channel — or, with no shell, a cross-origin `top`, or during server rendering, a
 * private channel nobody hosts, so nothing ships. Never `undefined`: the library would then use its
 * shared default channel, where another same-origin shell may be listening.
 */
function shellChannelName(): string {
  try {
    const shell = typeof window === 'undefined' ? undefined : window.top?.__uwtTelemetryChannel;
    if (shell) {
      return shell;
    }
  } catch {
    // cross-origin `top`
  }
  const suffix = `${Date.now().toString(36)}-${Math.random().toString(36).slice(2)}`;
  return `ngx-ui-watchtower-unhosted-${suffix}`;
}

providers: [
  provideUwtTelemetry({ application: 'cart', environment, version }), // must differ from the shell
  provideUwtTelemetrySink('broadcast'),
  { provide: UWT_BROADCAST_CHANNEL, useFactory: shellChannelName } // lazy — see below
];
```

Use the `useFactory` provider, not `provideUwtTelemetrySink('broadcast', { channelName:
shellChannelName() })`: the option is bound with `useValue` and read when the fragment's providers
array is built, while the factory runs only when the sink is first constructed.

**The shell must publish the id before any fragment boots** — the sink reads it once, so an early
fragment ships nothing for the whole page. The shell code above guarantees this with Web Fragments.

| Must match the shell | `eventNamespace`; the channel name (read from `window.top`)                                             |
|----------------------|---------------------------------------------------------------------------------------------------------|
| **Must differ**      | `application` — every forwarded event is stamped with it, which is how fragments are told apart         |
| **Never provide**    | `provideUwtTelemetryRumSink()`, `UWT_RUM_CREDENTIALS_PROVIDER`, `provideUwtTelemetryBroadcastHost()`, `UWT_LOG_API_PROVIDER` (`'broadcast'` already binds it to the forwarding provider) |
| **Never install**    | `aws-rum-web`                                                                                           |

Inside a fragment:

- `getSessionId()` is `undefined` until the shell answers the identity handshake — don't assert on it
  at bootstrap. Work is still correlated by `scenarioId`.
- Log lines go to the shell's log provider; `logger.query()` is answered by the shell.
- Don't call `setUserId()`: it is forwarded and changes the shell's user (and `undefined` starts a
  new session). The shell owns user identity.
- Paint observation doesn't work (a hidden iframe never paints) — settle with `complete()`.
- A fragment with no shell, or on a wrong channel, runs normally and ships nothing, silently —
  verify the channel (below).
- Correlation across realms is a string: forward `scenario.id` and start a child scenario with
  `parentScenarioId`.

## Verifying

- In a fragment's realm, `window.top.__uwtTelemetryChannel` equals the shell's id, and on a first
  page load the shell's `inject(UwtTelemetryBroadcastHost).received` counter grows.
- Two tabs have two different channel ids.
- With the debug flags on, lines are prefixed per realm: `[shell][scenario] …`, `[cart][bi] …`.
- `BroadcastChannel` is same-origin only: a fragment served from another origin forwards nothing,
  silently.
