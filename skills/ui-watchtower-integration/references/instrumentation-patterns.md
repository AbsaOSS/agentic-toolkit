# Instrumentation patterns

How to choose, implement and settle scenarios and BI events.

## Contents

1. [Finding candidates](#1-finding-candidates)
2. [Choosing the settle status](#2-choosing-the-settle-status)
3. [Scenario shapes](#3-scenario-shapes)
4. [RxJS traps](#4-rxjs-traps)
5. [Cleanup on destroy](#5-cleanup-on-destroy)
6. [BI events](#6-bi-events)
7. [Names, metadata and privacy](#7-names-metadata-and-privacy)
8. [Starter catalogue](#8-starter-catalogue)

## 1. Finding candidates

| Look for                                                         | Becomes                                                     |
|------------------------------------------------------------------|-------------------------------------------------------------|
| An `await` / subscription the user waits on before seeing a result | Scenario (route load, gating fetch, submit, upload, export) |
| A meaningful or irreversible click; a setting change              | BI event                                                    |
| A `catch` / `error` handler that ends a journey                  | That scenario's `fail(safeHttpFailure(error))` (§2)         |
| A guard, empty result, feature flag routing elsewhere            | That scenario's `incomplete({ reason })`                    |
| Component teardown, supersession by a newer request              | That scenario's `cancel({ reason })`                        |

Skip: anything that fires continuously (scroll, mousemove, per-keystroke), purely decorative UI,
and work the user never waits for.

## 2. Choosing the settle status

| Status       | Call                   | Means                                                                       | Response                          |
|--------------|------------------------|-----------------------------------------------------------------------------|-----------------------------------|
| `success`    | `complete()`           | The journey reached its goal                                                 | —                                 |
| `failure`    | `fail(outcome)`        | A defect: the journey broke (HTTP: `safeHttpFailure`, below)                 | Investigate; alert on rate        |
| `abandoned`  | `cancel({ reason })`   | No longer relevant: navigated away, superseded, component destroyed         | Engagement signal, **not** a bug  |
| `incomplete` | `incomplete(outcome?)` | An expected path that didn't reach the goal: no results, guard declined     | Product signal                    |
| `timeout`    | automatic              | Never settled within `timeoutMs`                                             | Usually a missed settle path      |

Keeping these apart is what makes the failure rate usable for alerting. Prefer the named methods
over `settle(status, …)` so every failure path is findable by searching for `.fail(`. The first
settle wins: a `catch` calling `fail()` followed by a `finally` calling `complete()` records the
failure.

Use a small, consistent set of `reason` strings — they are grouping keys: `'component-destroyed'`,
`'superseded'`, `'user-cancelled'`, `'no-results'`, `'guard-rejected'`.

Pass a `statusCode` with `fail()` so failures group by category — but **never a raw
`HttpErrorResponse`** (to `fail()` or `logger.error()`): its message quotes the request URL
(`/api/customers/42`), and redaction never scrubs path segments. Keep its class and status:

```ts
/** HttpErrorResponse.message quotes the request URL, path ids included — keep class and status only. */
function safeHttpFailure(error: unknown): UwtScenarioOutcome {
  const status = (error as { status?: unknown } | null)?.status;
  return typeof status === 'number'
    ? {
        error: Object.assign(new Error('HTTP request failed'), { name: 'HttpErrorResponse' }),
        statusCode: status
      }
    : { error }; // not an HTTP error: the library normalizes and redacts it
}
```

## 3. Scenario shapes

**Promise / async**:

```ts
async load(): Promise<void> {
  const scenario = this.scenarios.start({ name: 'load-customers', feature: 'customers' });
  try {
    scenario.step('fetch');
    const rows = await firstValueFrom(this.api.customers());
    scenario.step('render');
    this.rows.set(rows);
    if (rows.length === 0) {
      scenario.incomplete({ reason: 'no-results' });
      return;
    }
    scenario.complete({ metadata: { count: rows.length } });
  } catch (error) {
    scenario.fail(safeHttpFailure(error));
  }
}
```

**Observable** — `traceScenario` settles on completion, error or early unsubscribe. Like any cold
observable, nothing happens until something subscribes: return it to a caller that subscribes (a
template's `async` pipe, a component's `subscribe()`), or await it with `lastValueFrom()`. On error
it calls `fail({ error })` with the raw error and no status, so for HTTP sources settle the failure
first with `catchError` upstream — the first settle wins:

```ts
loadCustomers(): Observable<Customer[]> {
  const scenario = this.scenarios.start({ name: 'load-customers', feature: 'customers' });
  return this.api.customers().pipe(
    catchError((error) => {
      scenario.fail(safeHttpFailure(error));
      return throwError(() => error);
    }),
    traceScenario(scenario, { outcome: (rows) => ({ metadata: { count: rows.length } }) })
  );
}
```

**Backdating** — the journey starts at the click, not when the async handler runs:

```ts
onExportClick(): void { this.clickedAt = Date.now(); /* … */ }
// later
this.scenarios.start({ name: 'export-download', startedAt: this.clickedAt });
```

`startedAt` is epoch ms, clamped to the page lifetime; an unusable value falls back to now.

**Repeated work inside one journey** — aggregate instead of N steps:

```ts
for (const row of rows) {
  scenario.aggregateStart('format-row');
  format(row);
  scenario.aggregateEnd('format-row');
}
```

**Child journeys** — pass `parentScenarioId: parent.id`. Across realms (fragments), pass the id
string, never the `UwtScenario` object.

**Measuring what the user saw** — `complete()` stops the clock when the JavaScript finishes; for a
render-heavy journey, complete after the next frame:
`requestAnimationFrame(() => requestAnimationFrame(() => scenario.complete()))`.

## 4. RxJS traps

**Nothing downstream of `traceScenario` may stop after the first value.** `traceScenario` settles
`success` when the source *completes*; anything after it that unsubscribes on the first value —
`take(1)` or `first()` placed after it, or `firstValueFrom()` on the traced observable — tears it
down before completion arrives, and the scenario records `abandoned`. This holds even for
`HttpClient`, which completes right after its one value: `firstValueFrom` unsubscribes first.

```ts
// Records abandoned:
await firstValueFrom(this.api.customers().pipe(traceScenario(scenario)));
this.events$.pipe(traceScenario(scenario), take(1));

// Records success: limit upstream, await completion.
await lastValueFrom(this.api.customers().pipe(traceScenario(scenario)));
this.events$.pipe(take(1), traceScenario(scenario));
```

**`switchMap` supersession** — give `traceScenario` a `cancelOutcome`; `switchMap` tears the
previous request down before your projector runs, so cancelling it there is too late:

```ts
query$.pipe(
  debounceTime(300),
  switchMap((q) => {
    const scenario = this.scenarios.start({ name: 'search', feature: 'catalogue' });
    scenario.step('query');
    return this.api.search(q).pipe(
      catchError((error) => {
        scenario.fail(safeHttpFailure(error));
        return EMPTY; // keep the search stream alive after a failed request
      }),
      traceScenario(scenario, { cancelOutcome: { reason: 'superseded' } })
    );
  })
);
```

Managing scenarios by hand? Cancel the previous one at the top of the projector, before starting the
next.

## 5. Cleanup on destroy

Every component that starts a scenario settles it on destroy; otherwise it sits in the active
registry until its timeout (and forever with `timeoutMs: 0`).

```ts
ngOnDestroy(): void {
  this.loadScenario?.cancel({ reason: 'component-destroyed' });
}

// several, keyed by entity
ngOnDestroy(): void {
  for (const s of this.uploads.values()) s.cancel({ reason: 'component-destroyed' });
  this.uploads.clear();
}
```

Cancelling an already-settled scenario is a harmless no-op, so this needs no "is it still open"
check.

## 6. BI events

- One event per meaningful action, named `snake_case` in `UwtBIEventNames`.
- Inside a journey, link it: `track('export_clicked', { format }, { scenarioId: scenario.id })`.
- Debounce high-frequency sources (search boxes, sliders) before `track()` — e.g.
  `debounceTime(400)`. Repeated identical clicks within 400 ms are already collapsed by the library.
- A thin app wrapper is fine; type its name parameter `UwtBIEventName`.

## 7. Names, metadata and privacy

- Never interpolate data into a scenario, step or BI name. Put the variable part in metadata, and
  only if it is low-cardinality (a format, a tab name, a count) — never a record id or free text.
- `route` is a template (`/customers/:id`).
- Metadata: flat `string | number | boolean | null`; max 50 keys across the whole scenario.
- No personal data: no emails, names, usernames, account numbers, free-text input. Use opaque ids.
- Code you write that touches `window`, `navigator`, `document` or `localStorage` runs during server
  rendering too — guard it:
  `this.isBrowser ? { language: navigator.language } : {}` with
  `isBrowser = isPlatformBrowser(inject(PLATFORM_ID))`.

## 8. Starter catalogue

Adapt to the app's real vocabulary and to what the user asked for. Route navigation is already
tracked by `ui-watchtower-setup`.

| Scenario          | Steps                          | Settles                                                                                     |
|-------------------|--------------------------------|---------------------------------------------------------------------------------------------|
| `<screen>-load`   | `fetch`, `render`              | `complete`; `incomplete({reason:'no-results'})`; `fail(safeHttpFailure(e))`; cancel on destroy/supersede |
| `<form>-submit`   | `validate`, `submit`           | `complete`; `incomplete({reason:'validation-failed'})`; `fail(safeHttpFailure(e))`         |
| `file-upload`     | `read`, `upload`, `process`    | `complete({metadata:{fileSize}})`; `cancel({reason:'user-cancelled'})`; `fail(safeHttpFailure(e))` |
| `export-download` | `request`, `transfer`          | `complete`; `cancel({reason:'user-cancelled'})`; `fail(safeHttpFailure(e))`                 |

BI: `export_clicked`, `filter_applied`, `search_submitted` (debounced), `theme_changed`,
`sidebar_toggled`, `sign_out_clicked`.
