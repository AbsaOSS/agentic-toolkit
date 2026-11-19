# Micro-frontends: shell hosts, fragments forward

Use when the app embeds fragments that run in their own JavaScript realm (Web Fragments,
same-origin iframes, separately bootstrapped apps), or is such a fragment. Not for code that runs
in the host's realm — a Module Federation remote, a lazy-loaded bundle: it uses the host's
telemetry and creates none of its own (in Angular, it runs in the host's injector; elsewhere, the
host hands it its engine).

## Why

Each realm would otherwise create its own engine and AWS RUM client: one visitor becomes N
sessions with N event budgets, N credential fetches and N SDK downloads. So **exactly one realm —
the shell — owns the RUM client; fragments forward** to it over a same-origin `BroadcastChannel`.
Each realm can be Angular (the adapter) or anything else (the core): they exchange the same
messages. Application code is the same as in a standalone app; only the wiring differs.

## The channel: one per page load

`BroadcastChannel` and the host's leader election are origin-wide. On the shared default channel,
a second tab's fragments get recorded through the first tab's RUM client — wrong page, wrong
context. So the shell creates one channel name **per page load** (never per fragment or per
navigation), publishes it on its window, and each fragment reads it once, at startup.

```ts
// shell: src/telemetry/telemetry-channel.ts
declare global {
  interface Window { __uwtTelemetryChannel?: string }
}

/**
 * One random channel per page load, published for the fragments. randomUUID needs a secure
 * context, hence the fallback; undefined during server rendering, where no channel opens.
 */
export const channelId =
  typeof window === 'undefined'
    ? undefined
    : `ui-watchtower-${crypto.randomUUID?.() ?? `${Date.now()}-${Math.random().toString(36).slice(2)}`}`;
if (channelId) {
  window.__uwtTelemetryChannel = channelId;
}
```

```ts
// fragment: src/telemetry/telemetry-channel.ts
declare global {
  interface Window { __uwtTelemetryChannel?: string }
}

/**
 * The nearest window that published a channel, else a private one nobody hosts — never
 * undefined, which would select the shared default channel.
 */
export function shellChannelName(): string {
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
  return `ui-watchtower-unhosted-${Date.now().toString(36)}-${Math.random().toString(36).slice(2)}`;
}
```

- **The shell publishes before any fragment boots.** A fragment reads the name once; one that
  boots first ships nothing for the whole page. A shell that renders its fragments after it
  starts (Web Fragments does) guarantees this.
- A realm outside the shell's page (a popup window) can't walk to it: give it the shell's id
  another way.
- **A fragment that can also run on its own** (opened at its own URL, with no shell): on the private
  fallback it opens a channel, asks for the shell's identity and times scenarios, all for nobody.
  Check once at startup whether a shell published a channel
  (`!shellChannelName().startsWith('ui-watchtower-unhosted-')`) and make that part of the switch:
  `enabled = <the app's switch> && shellFound`. That check is the app's code: test it as plain code
  (a published channel → found, none → not found), not the telemetry while it is off.
- Server rendering on the core path: Node has a `BroadcastChannel` too, so give the host, the
  connection and the broadcast classes `enabled: enabled && typeof window !== 'undefined'`. (The
  Angular adapter checks the platform itself.)
- Current releases (core 0.1.1, adapter 0.5.1) need this. A later release may find the shell's
  channel by itself (ui-watchtower #29, unreleased); an explicit channel keeps working then.

## Shell

The shell is a RUM realm (SKILL.md Step 3) plus a **broadcast host** on `channelId`, and a log
provider: fragments' log records are stored by the shell's (with no log backend, the no-op one).

Angular:

```ts
import {
  UWT_LOG_API_PROVIDER,
  UwtNoopLogApiProvider,
  provideUwtTelemetry,
  provideUwtTelemetryBroadcastHost
} from '@absaoss-cps/ngx-ui-watchtower';
import {
  UWT_RUM_CREDENTIALS_PROVIDER,
  provideUwtTelemetryRumSink
} from '@absaoss-cps/ngx-ui-watchtower/rum';
import { channelId } from './telemetry/telemetry-channel';

providers: [
  provideUwtTelemetry({ application: 'shell', environment, version }),
  provideUwtTelemetryRumSink(),
  { provide: UWT_RUM_CREDENTIALS_PROVIDER, useClass: AppRumCredentialsProvider },
  // + route tracking and ROUTE_PAGE_VIEW_RECORDER, only if the user chose it (angular.md, Step 6)
  provideUwtTelemetryBroadcastHost(channelId),
  { provide: UWT_LOG_API_PROVIDER, useClass: UwtNoopLogApiProvider }
];
```

Core — in the engine module (`core.md`, Step 3), after the engine:

```ts
import { UwtTelemetryBroadcastHost } from '@absaoss-cps/ui-watchtower';
import { channelId } from './telemetry-channel';

const logApi = new UwtNoopLogApiProvider(); // or the app's own; give the engine the same one
// …destination and engine as in core.md, with this logApi
/** Records what fragments forward; `received` counts it, for verification. */
export const broadcastHost = new UwtTelemetryBroadcastHost({
  sink: destination,
  logApi,
  channelName: channelId,
  enabled
});
```

- **Create the host now**, even if no fragment forwards yet — a host with no fragments sits idle,
  and it must be listening before the first fragment sends.
- Fragments' own HTTP requests aren't traced by the shell's RUM client in current releases
  (ui-watchtower #29, unreleased).
- The contract you hand to fragment teams (below) states the shell's `eventNamespace` (`com.uwt`
  when it sets none) and the channel global, `window.__uwtTelemetryChannel`.

## Fragment — the contract to hand to fragment teams

Copy the fragment's `shellChannelName()` above. Angular:

```ts
import {
  UWT_BROADCAST_CHANNEL,
  provideUwtTelemetry,
  provideUwtTelemetrySink
} from '@absaoss-cps/ngx-ui-watchtower';
import { shellChannelName } from './telemetry/telemetry-channel';

providers: [
  provideUwtTelemetry({
    application: 'cart', // must differ from the shell
    environment,
    version,
    eventNamespace: 'com.uwt' // the shell's — must match
  }),
  provideUwtTelemetrySink('broadcast'), // also binds the forwarding log provider
  { provide: UWT_BROADCAST_CHANNEL, useFactory: shellChannelName }
];
```

Core — the engine module:

```ts
import {
  uwtConnectBroadcastChannel,
  uwtCreateTelemetry,
  UwtBroadcastLogApiProvider,
  UwtBroadcastTelemetrySink
} from '@absaoss-cps/ui-watchtower';
import { shellChannelName } from './telemetry-channel';

// `environment` and `version` come from the same sources as in core.md, "Identity values".
const identity = { application: 'cart', environment, version, eventNamespace: 'com.uwt' };
const enabled = true; // the same switch as the shell's

/** One connection, shared by the sink and the log provider. */
const connection = uwtConnectBroadcastChannel({ channelName: shellChannelName(), enabled });
const destination = new UwtBroadcastTelemetrySink({ identity, connection, enabled });
const logApi = new UwtBroadcastLogApiProvider({ connection, enabled });
export const telemetry = uwtCreateTelemetry({ identity, destination, logApi, enabled });

/** Only if the shell unmounts this fragment while the page stays: from its unmount hook (Web Fragments: see below). */
export function disposeTelemetry(): void {
  telemetry.dispose();
  destination.dispose();
  logApi.dispose();
  connection.close();
}
```

| Must match the shell | `eventNamespace` (ask for the shell's value if the shell isn't in this repo; default `com.uwt`); the off switch (`enabled` / `withTelemetryEnabled`) — it is per realm, so a fragment left on beside a shell that is off still opens a channel nobody hosts |
|----------------------|---------------------------------------------------------------------------------------------------------|
| **Must differ**      | `application` — every forwarded event is stamped with it, which is how fragments are told apart         |
| **Never create**     | a RUM sink, a credentials provider, a broadcast host, a log provider of its own (in Angular, `UWT_LOG_API_PROVIDER`: `'broadcast'` binds it) |
| **Never install**    | `aws-rum-web`                                                                                           |

Inside a fragment:

- Its session id is `undefined` until the shell answers the identity handshake — don't assert on
  it at startup. Work is still correlated by `scenarioId`.
- The shell's host stamps its own current `sessionId` and `userId` on every scenario, step, BI and
  log record a fragment forwards, and re-measures `sessionElapsed` if the session changed (not in
  adapter releases below 0.4.0). So fragment records carry the shell's session and user. While the
  shell's RUM client hasn't started, there is no session to stamp.
- Log lines go to the shell's log provider; a log query is answered by the shell.
- Don't call `setUserId()`: it is forwarded and changes the shell's user. The shell owns user
  identity.
- Don't settle a scenario on a paint (`requestAnimationFrame`): a fragment's hidden realm never
  paints — call `complete()` once the work is done.
- **Web Fragments gives a fragment no unmount hook** (web-fragments 0.8.2,
  [web-fragments#302](https://github.com/web-fragments/web-fragments/issues/302)). It moves the
  fragment's `pagehide` listener to the shell's window, where it fires only when the whole page
  goes away, and Chromium can refuse `unload`. So when the shell removes the fragment, nothing in
  the fragment runs: the engine is never disposed (in Angular, nothing destroys the app, so
  `ngOnDestroy` never runs) and scenarios still in flight are lost. The shell can patch its
  web-fragments to dispatch an event in the fragment just before removal, on the fragment's shadow
  root (where web-fragments delivers the fragment's `window` listeners); the fragment then
  disposes from that event: `disposeTelemetry()` above, or `appRef.destroy()` in Angular. In
  Angular, that destroy sends the scenarios in flight from adapter 0.5.1. Older releases close the
  channel before they settle (ui-watchtower #36), so there they are lost even with the patch:
  suggest the upgrade. Say in the report which case applies: with such a patch, that disposal
  depends on it; without one, that removing the fragment loses the scenarios in flight and, in
  Angular, never destroys the app (`ngOnDestroy` does not run).

## Verifying

- Once a fragment sends something (an event or a log record, e.g. the temporary setup check), the
  shell host's `received` counter grows (Angular: `inject(UwtTelemetryBroadcastHost).received`;
  core: `broadcastHost.received`), also when the shell runs inside another app's iframe. It
  doesn't count a fragment's identity request at startup: a fragment that sends nothing leaves it
  at 0.
- Two tabs have two different `window.__uwtTelemetryChannel` values.
- With the debug flags on, lines are prefixed per realm: `[shell][scenario] …`, `[cart][bi] …`.
- `BroadcastChannel` is same-origin only: a fragment served from another origin forwards nothing,
  silently.
