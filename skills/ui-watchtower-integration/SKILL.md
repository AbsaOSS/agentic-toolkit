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

The people who own the app know which questions the data must answer; the code shows where those
journeys live. This skill starts from the first and uses the second — it asks before it proposes,
and marks which items came from the user and which it suggested. It can be re-run as the app grows:
each pass adds to what is already instrumented.

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

If only `telemetry.schema.ts` (the file augmenting the name registries) is missing, don't stop:
create it in Step 6 — a `declare module '@absaoss-cps/ngx-ui-watchtower'` block with the confirmed
names, side-effect-imported where the providers are configured.

Also read what already exists — the schema's declared names and every `scenarios.start(` /
`track(` call — so this pass only adds or changes, never duplicates. Note the test runner and the
package manager.

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

Load `references/instrumentation-patterns.md` (section 1). Within the scope from Step 2, find:

- **Every wait the user actually sits through** → a scenario (a fetch that gates a screen, a submit,
  an upload, an export).
- **Every meaningful or irreversible click** → a BI event.
- **Every `catch` that ends a journey** → that scenario's `fail({ error })`.

Map each user answer to concrete code: which component or service, which call starts the journey,
which outcomes it can have.

### Step 4 · Present a merged proposal

Use this shape. `Source` says where each item came from — `you` (the user asked for it, or it answers
one of their questions) or `suggested` (found in the code). Put the user's items first.

```markdown
## Proposed telemetry for <application>

Answers: <the user's questions, one line each, or "none given — suggestions only">
Already instrumented (unchanged): <existing scenario and BI names, or "nothing yet">

### Scenarios
| Source | Name | Where (file) | Steps | success when | other outcomes |
|---|---|---|---|---|---|
| you | customer-search | customers/customer-search.ts | query | results shown | incomplete: no-results; fail: HTTP error; cancel: superseded/left |

### BI events
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

Follow `references/instrumentation-patterns.md`:

1. Add every confirmed name to `telemetry.schema.ts` (scenarios and steps kebab-case, BI events
   snake_case, one JSDoc line each). Never interpolate ids into names.
2. Each journey: start → steps → settle with the **right** status — `complete`, `incomplete` (an
   expected dead end, e.g. no results), `fail` (a defect; pass `error` and `statusCode`), `cancel`
   (the user left or a newer request superseded it). Timeout is automatic.
3. Settle open scenarios when their component is destroyed; under `switchMap`, give
   `traceScenario` a `cancelOutcome`; never put `take(1)`/`first()` upstream of `traceScenario`.
4. BI events inside a journey pass `{ scenarioId: scenario.id }`. Debounce high-frequency sources
   (search boxes, sliders) before starting a scenario or sending a BI event — one per settled
   input, never one per keystroke.
5. Metadata: flat primitives, low cardinality, no personal data.
6. Only if the app has a log backend (`UwtLoggerNames` declared): at a journey-ending error, also
   `logger.error(message, { error, correlationId: scenario.id })` so log lines join the scenario.

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
scenario with the right status, leaving mid-journey gives `abandoned`, a double-click gives one BI
event.

Report what was instrumented (by source), what was proposed but not confirmed, and anything changed
from the user's original request and why.

## Gotchas

- **The right settle status is the whole point.** Leaving is `abandoned`, not `failure`; an empty
  result is `incomplete`, not `success`. Collapsing them makes the failure rate useless for alerts.
- **Names and `route` are metric dimensions** — no ids, no resolved URLs.
- **Metadata is flat primitives**, at most 50 keys per scenario; objects and `undefined` are dropped.
- **The RUM session budget is 200 events**, page views and errors included — one event per settled
  scenario, keep `emitLifecycleEvents` off, debounce chatty BI events.
- **Telemetry never throws into the app** — don't wrap calls in try/catch.
- **Percentiles and dashboards are AWS-side.** The frontend emits raw `delta` and low-cardinality
  dimensions; it never computes metrics.

## Out of scope

- Installing or wiring the library, credentials, destinations, route-navigation tracking →
  `ui-watchtower-setup`.
- CloudWatch dashboards, extended metrics, alarms.
- A backend correlation-header interceptor (offer as a follow-up).
- Non-Angular applications.
