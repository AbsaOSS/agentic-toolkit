---
name: ui-watchtower-integration
description: >
  Instruments an Angular app that already uses @absaoss-cps/ngx-ui-watchtower with scenarios (user
  journeys) and BI events driven by the team's own questions: asks what they want to learn, scans
  the code for candidates, proposes a merged plan, implements after confirmation, and tests it. Use
  for "measure checkout", "track exports", "add journey/BI telemetry". NOT for: installing or wiring
  the library (→ ui-watchtower-setup), dashboards, non-Angular apps.
license: Apache-2.0
compatibility: >
  Requires an Angular application where @absaoss-cps/ngx-ui-watchtower is already installed and
  wired (see ui-watchtower-setup).
---

# ui-watchtower-integration

Measures what matters in a specific app, with
[`@absaoss-cps/ngx-ui-watchtower`](https://www.npmjs.com/package/@absaoss-cps/ngx-ui-watchtower)
already in place:

| Concern | Answers | API |
|---|---|---|
| **Scenarios** | Did this user journey succeed, and how long did it take? | `UwtScenarioTelemetryService.start()` → `UwtScenario` |
| **BI events** | Did this meaningful thing happen? | `UwtBITelemetryService.track()` |

These are **two separate concerns with two separate services**. A scenario measures a journey: it
has a duration and settles with a status. A BI event only counts that something happened. Inject
`UwtScenarioTelemetryService` and/or `UwtBITelemetryService` directly in the component or service
where the telemetry is needed, and never merge them behind an `AppTelemetryService`, a facade or a
single `track…` API unless the user explicitly asks for one — a merged API hides which concern a call
is and which status it settles with.

It asks the team what they want to learn before proposing, marks each item as theirs or suggested,
and can be re-run as the app grows — each pass only adds.

## Reference files — load on demand

| Load | When |
|---|---|
| [ngx-ui-watchtower-api](../shared/references/ngx-ui-watchtower-api.md) ([remote](https://github.com/AbsaOSS/agentic-toolkit/blob/master/skills/shared/references/ngx-ui-watchtower-api.md)) | Before writing code — exact imports, signatures, test harness |
| `references/instrumentation-patterns.md` | Steps 3–6 — finding candidates, settle statuses, RxJS traps, cleanup, BI rules, starter catalogue |

## Workflow

Copy this checklist and track progress:

```
- [ ] Step 1: Check that setup is done (read-only)
- [ ] Step 2: Ask the user what they want to learn
- [ ] Step 3: Scan the code for candidates
- [ ] Step 4: Present a merged proposal
- [ ] Step 5: Wait for confirmation
- [ ] Step 6: Implement what was confirmed
- [ ] Step 7: Tests for every outcome
- [ ] Step 8: Validate
```

### Step 1 · Check that setup is done (read-only)

Look for the package in `package.json`, and `provideUwtTelemetry(...)` plus exactly one destination
in the app's providers. If either is missing, stop and tell the user to run
**`ui-watchtower-setup`** first — instrumenting an unwired app fails at bootstrap with `NG0201`.

If only `telemetry.schema.ts` is missing, don't stop — create it in Step 6.

Read what already exists so this pass only adds: the names in `telemetry.schema.ts`, and their uses
(search each name, every injection of `UwtScenarioTelemetryService` / `UwtBITelemetryService`, and
`traceScenario(`). Note the test runner and package manager. If the app already wraps these services in
its own telemetry service, list that under "Already instrumented", don't extend it or copy the
pattern, and say so in the proposal; write the new code against the two services directly unless the
user tells you to follow the wrapper.

### Step 2 · Ask the user what they want to learn

Before reading the code for candidates, ask — in **one** short message, skipping anything the request
already answers:

1. **Which questions should this telemetry answer?** e.g. "is checkout getting slower", "do people
   use the export", "where do new users drop off".
2. **Which user journeys matter most**, and what counts as success for each?
3. **Which interactions or features** do you want usage numbers for?
4. **Known pain points** — slow screens, incidents, support tickets worth watching?
5. **Anything that must not be tracked** — sensitive screens, fields, user groups?
6. **Scope of this pass** — the whole app, or one area?

Why ask first: the code can show where waits and clicks are, but not which of them anyone will ever
look at. Telemetry nobody needs still spends the 200-event RUM session budget and adds noise.

If the user can't answer or says "just suggest", continue with code-derived candidates only and say
so in the proposal.

### Step 3 · Scan the code for candidates

Always do this scan, even when the user gave a complete list of what to track: their list says what
they care about, only the code says how it can be wired and what else is worth measuring. Load
`references/instrumentation-patterns.md` (section 1), read the routes, the components and services
in scope, and the HTTP calls behind them. Within the scope from Step 2, find:

- **Every wait the user actually sits through** → a scenario (a fetch that gates a screen, a submit,
  an upload, an export).
- **Every meaningful or irreversible click** → a BI event.
- **Every `catch` that ends a journey** → that scenario's `fail(...)` (Step 6, rule 3).

Decide for every candidate whether it is a scenario, a BI event, or both. A wait with no interesting
click is a scenario; a click with no wait is a BI event; a click inside a journey is both — a scenario
for the journey and a BI event linked to it with `{ scenarioId }`.

Then map each user request to concrete code: which component or service, which call starts the
journey, which outcomes it can have. A request you can't find in the code goes under "Requested but
changed or not feasible". Candidates the user didn't mention are not optional extras: they become
`suggested` rows, so the proposal never contains only what was asked for.

### Step 4 · Present a merged proposal

Use this table shape even when nobody is there to answer — it is what the user reviews, and prose
loses the `Source` column. `Source` says where each item came from — `you` (the user asked for it, or it answers
one of their questions) or `suggested` (found in the code). Put the user's items first.

```markdown
## Proposed telemetry for <application>

Scanned: <routes, components and services read, e.g. "checkout/ (3 components, 2 HTTP calls)">
Answers: <the user's questions, one line each, or "none given — suggestions only">
Already instrumented (unchanged): <existing scenario and BI names, or "nothing yet">

### Scenarios (UwtScenarioTelemetryService)
| Source | Name | Where (file) | Steps | success when | other outcomes |
|---|---|---|---|---|---|
| you | customer-search | customers/customer-search.ts | query | results shown | incomplete: no-results; fail: HTTP error; cancel: superseded/left |

### BI events (UwtBITelemetryService)
| Source | Name | Where (file) | Metadata (flat, no PII) |
|---|---|---|---|
| suggested | export_clicked | customers/customers.ts | format |

### Requested but changed or not feasible
- "<request>" — <why, e.g. raw search text is PII and unbounded> → <alternative, e.g. debounced
  `search_submitted` with `queryLength` and `resultCount`>

### Deliberately not instrumented
- <thing> — <why>
```

When a request conflicts with the library's rules, keep the user's intent and change the shape —
never silently drop it and never implement it as asked. The usual conflicts: an id or free text in a
name or metadata, per-keystroke events, personal data, a metric the frontend can't measure (server
latency, percentiles — those are computed in AWS from `delta`).

### Step 5 · Wait for confirmation

Stop. The user may add, drop or reshape items; apply their changes and show the final list if it
changed materially. Implement nothing before this.

### Step 6 · Implement what was confirmed

Follow `references/instrumentation-patterns.md`.

**Use the two services directly.** In each component or service that needs telemetry, `inject()` the
service for the concern at hand — `UwtScenarioTelemetryService`, `UwtBITelemetryService`, or both —
and call it there. Do not create an `AppTelemetryService`, facade, base class or one `track…` API over
both, and do not move the calls into a shared service. Single-purpose helpers are fine (for example
`safeHttpFailure`); a shared abstraction only if the user explicitly asks.

1. Add every confirmed name to `telemetry.schema.ts` (scenarios and steps kebab-case, BI events
   snake_case, one JSDoc line each). Never interpolate ids into names.
2. Each journey: start → steps → settle with the **right** status — `complete`, `incomplete` (an
   expected dead end, e.g. no results), `fail` (a defect, with a `statusCode`), `cancel` (the user
   left or a newer request superseded it). Timeout is automatic. Collapsing `abandoned` or
   `incomplete` into `failure` makes the failure rate useless for alerts. On `complete`, add the one
   number that says how much happened (rows returned, file size) when the screen has one: it tells a
   fast empty list from a fast full one.
3. **Never pass a raw `HttpErrorResponse` to `fail()` or `logger.error()`** — its message quotes the
   URL, ids included. Use the patterns' `safeHttpFailure(error)`; with `traceScenario`, settle it in a
   `catchError` placed before the operator.
4. Settle open scenarios when their component is destroyed; under `switchMap`, give
   `traceScenario` a `cancelOutcome`. Nothing downstream of `traceScenario` may stop after the
   first value — no `take(1)`/`first()` after it, no `firstValueFrom()` on it (it records
   `abandoned`): limit upstream and await with `lastValueFrom()`.
5. BI events inside a journey pass `{ scenarioId: scenario.id }`. Debounce high-frequency sources
   (search boxes, sliders) before starting a scenario or sending a BI event — one per settled
   input, never one per keystroke.
6. Metadata: flat primitives, low cardinality, no personal data.
7. Only if the app has a log backend (`UwtLoggerNames` declared): at a journey-ending error, also
   `logger.error(message, { error: safeHttpFailure(e).error, correlationId: scenario.id })` so log
   lines join the scenario.

### Step 7 · Tests for every outcome

Use a recording sink (API reference, "Testing") and assert what reaches the sink — event type,
`scenarioName`, `status`, `reason`, metadata — for each outcome the proposal claims (success,
incomplete, failure with status, abandoned on leave). Specs that render instrumented components need
the telemetry providers or they fail with `NG0201`. Check one test bites: remove its settle call,
confirm it fails, restore.

### Step 8 · Validate

Run, through the app's package manager: the **build**, the **unit tests**, and a **real type-check**
(`tsc -p tsconfig.app.json --noEmit` and the spec tsconfig — Vitest never type-checks). Then a live
check with `localStorage.setItem('debugScenario', 'true')` and `debugBI`: one line per settled
scenario with the right status, leaving mid-journey gives `abandoned`, and a repeated identical
click gives one BI event.

Report what was instrumented (by source), what was proposed but not confirmed, and anything changed
from the user's original request and why.

## Gotchas

- **Telemetry never throws into the app** — don't wrap calls in try/catch.
- **Scenario and BI stay separate** — use `UwtScenarioTelemetryService` and `UwtBITelemetryService`
  directly where needed; no merged service, facade or unified `track…` API unless the user asks.

## Out of scope

- Installing or wiring the library, credentials, destinations, route-navigation tracking →
  `ui-watchtower-setup`.
- CloudWatch dashboards, extended metrics, alarms.
- A backend correlation-header interceptor (offer as a follow-up).
- Non-Angular applications.
