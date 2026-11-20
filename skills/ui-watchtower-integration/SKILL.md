---
name: ui-watchtower-integration
description: >
  Instruments a frontend app that already uses ui-watchtower — the Angular adapter
  @absaoss-cps/ngx-ui-watchtower, or the framework-free core @absaoss-cps/ui-watchtower in any
  other app (any framework, or none) — with scenarios (user journeys) and BI events driven by the
  team's own questions: asks what they want to learn, scans the code for candidates, proposes a
  merged plan, implements after confirmation, and tests it. Use for "measure checkout", "track
  exports", "add journey/BI telemetry", "instrument this page". NOT for: installing or wiring the
  library (→ ui-watchtower-setup), dashboards, server-side or native mobile apps.
license: Apache-2.0
compatibility: >
  Requires a frontend app where ui-watchtower is already installed and wired — the Angular
  adapter's providers, or the core's engine (see ui-watchtower-setup).
---

# ui-watchtower-integration

Measures what matters in a specific app, with ui-watchtower already in place:

| Concern | Answers | API (Angular: injected service · elsewhere: the engine) |
|---|---|---|
| **Scenarios** | Did this user journey succeed, and how long did it take? | `UwtScenarioTelemetryService.start()` · `telemetry.scenarios.start()` → `UwtScenario` |
| **BI events** | Did this meaningful thing happen? | `UwtBITelemetryService.track()` · `telemetry.bi.track()` |

These are **two separate concerns with two separate APIs**. A scenario measures a journey: it has a
duration and settles with a status. A BI event only counts that something happened. Call the API
for the concern at hand directly where the telemetry is needed — inject the service in Angular,
use the app's engine (`telemetry.scenarios`, `telemetry.bi`) elsewhere — and never merge them
behind an `AppTelemetryService`, a facade, a shared wrapper module, or a single `track…` API
unless the user explicitly asks for one — a merged API hides which concern a call is and which
status it settles with.

It asks the team what they want to learn before proposing, marks each item as theirs or suggested,
and can be re-run as the app grows — each pass only adds.

## Reference files — load on demand

| Load | When |
|---|---|
| [ui-watchtower-api](../shared/references/ui-watchtower-api.md) ([remote](https://github.com/AbsaOSS/agentic-toolkit/blob/master/skills/shared/references/ui-watchtower-api.md)) | Before writing code — the scenario, BI and logging API, what reaches the wire, test harness |
| [ngx-ui-watchtower-api](../shared/references/ngx-ui-watchtower-api.md) ([remote](https://github.com/AbsaOSS/agentic-toolkit/blob/master/skills/shared/references/ngx-ui-watchtower-api.md)) | Angular apps — imports, services, TestBed |
| `references/instrumentation-patterns.md` | Steps 3–7 — finding candidates, settle statuses, promise and RxJS shapes, cleanup per framework, BI rules, starter catalogue |

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

Find which package the app uses, then check it is wired:

- **Angular** (`@absaoss-cps/ngx-ui-watchtower` in `package.json`): `provideUwtTelemetry(...)` plus
  exactly one destination in the app's providers — without them, instrumented code fails at
  bootstrap with `NG0201`.
- **Anything else** (`@absaoss-cps/ui-watchtower`): one engine, created by `uwtCreateTelemetry(...)`
  with a destination at startup — usually an engine module such as `src/telemetry/telemetry.ts`
  that exports `telemetry`. App code reaches it by importing that module; if the app already
  passes it around another way, use that.

If the package or its wiring is missing, stop and tell the user to run **`ui-watchtower-setup`**
first. If only `telemetry.schema.ts` is missing, don't stop — create it in Step 6.

Read what already exists so this pass only adds: the names in `telemetry.schema.ts` (and the prefix
they share), and their uses — search each name, every injection of `UwtScenarioTelemetryService` /
`UwtBITelemetryService` or use of `telemetry.scenarios` / `telemetry.bi`, and `traceScenario(`.
If setup added route-navigation tracking (a `<prefix>-route-navigate` scenario), navigations are
already measured: add no second navigation scenario. Note the test runner and the package
manager. Existing specs stay untouched, setup
included (unless they now need a test engine, Step 7) — new tests go in their own `describe` with
their own setup. If the app already wraps these APIs in its own telemetry service or module,
list that under "Already instrumented", don't extend it or copy the pattern, and say
so in the proposal; write the new code against the two APIs directly unless the user tells you to
follow the wrapper.

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
`references/instrumentation-patterns.md`, read the routes, the components, services and modules
in scope, and the HTTP calls behind them. Within the scope from Step 2, find candidates
with the table in §1 and classify each one as a scenario, a BI event, or both.

Then map each user request to concrete code: which component or function, which call starts the
journey, which outcomes it can have. A request you can't find in the code goes under "Requested but
changed or not feasible". Candidates the user didn't mention are not optional extras: they become
`suggested` rows, so the proposal never contains only what was asked for.

### Step 4 · Present a merged proposal

Use this table shape even when nobody is there to answer — it is what the user reviews, and prose
loses the `Source` column. `Source` says where each item came from — `you` (the user asked for it, or it answers
one of their questions) or `suggested` (found in the code). Put the user's items first. Head each
table with the API the app uses: the service in Angular, `telemetry.scenarios` / `telemetry.bi`
elsewhere.

```markdown
## Proposed telemetry for <application>

Scanned: <routes, components and services read, e.g. "checkout/ (3 components, 2 HTTP calls)">
Answers: <the user's questions, one line each, or "none given — suggestions only">
Already instrumented (unchanged): <existing scenario and BI names, or "nothing yet">
Name prefix: <the prefix the existing names use; if none, one suggested from the application name — confirm it>

### Scenarios (UwtScenarioTelemetryService | telemetry.scenarios)
| Source | Name | Where (file) | Steps | success when | other outcomes |
|---|---|---|---|---|---|
| you | my-app-customer-search | customers/customer-search.ts | query | results shown | incomplete: no-results; fail: HTTP error; cancel: superseded/left |

### BI events (UwtBITelemetryService | telemetry.bi)
| Source | Name | Where (file) | Metadata (flat, no PII) |
|---|---|---|---|
| suggested | my-app-export-clicked | customers/customers.ts | format |

### Requested but changed or not feasible
- "<request>" — <why, e.g. raw search text is PII and unbounded> → <alternative, e.g. debounced
  `my-app-search-submitted` with `queryLength` and `resultCount`>

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

**Use the two APIs directly.** Where a component, service or module needs telemetry, call
the API for the concern at hand right there: in Angular, `inject()` `UwtScenarioTelemetryService`,
`UwtBITelemetryService`, or both; elsewhere, import the app's engine and call `telemetry.scenarios`
or `telemetry.bi`. Do not create an `AppTelemetryService`, facade, base class, shared wrapper, or
one `track…` API over both, and do not move the calls into a shared module.
Single-purpose helpers are fine (for example `safeHttpFailure`); a shared abstraction only if the
user explicitly asks.

1. Add every confirmed name to `telemetry.schema.ts`, adding a registry's interface if it isn't
   there yet (API reference §1 lists them) — kebab-case, scenario, BI and logger names
   with the prefix (`references/instrumentation-patterns.md` §7), one JSDoc line each. Never interpolate ids
   into names.
2. Settle every journey with the right status (§2) and shape it with §3; never pass a raw HTTP
   error object (§2, `safeHttpFailure`).
3. In RxJS code, avoid the traps in §4. Settle open scenarios when their owner goes away or a
   newer load replaces them (§5).
4. BI events follow §6; names, metadata and privacy follow §7.
5. Only if the app has a log backend (`UwtLoggerNames` declared): at a journey-ending error, also
   `logger.error(message, { error: safeHttpFailure(e).error, correlationId: scenario.id })` so log
   lines join the scenario.

### Step 7 · Tests for every outcome

Assert what reaches the destination — event type, `scenarioName`, `status`, `reason`, metadata —
for each outcome the proposal claims (success, incomplete, failure with status, abandoned on
leave). Don't claim `timeout` as an outcome — it's the library's safety net for a missed settle, not
something the code settles.

- **Angular:** a recording sink in TestBed (`ngx-ui-watchtower-api.md`, "Testing"). Specs that
  render instrumented components need the telemetry providers or they fail with `NG0201`.
- **Elsewhere:** the mock of the engine module in the test setup file (API reference §11; add it
  if the app has none). Spy on its destination and assert on the calls: `vi.spyOn(destination,
  'record')`, then `'com.uwt.scenario'` with `scenarioName`, `status`, `reason`, or `'com.uwt.bi'`
  with `eventName` and `metadata`; restore spies after each test.

Check one test bites: remove its settle call, confirm it fails, restore.

### Step 8 · Validate

Run, through the app's package manager: the **build**, the **unit tests**, and a **real type-check**
(the app's own type-check script, e.g. `tsc -b` or `vue-tsc --noEmit`, else `tsc --noEmit -p` on
the app's and the specs' tsconfig; in Angular, `tsc -p tsconfig.app.json --noEmit` and the spec
tsconfig — Vitest never type-checks). Then a live check with
`localStorage.setItem('debugScenario', 'true')` and `debugBI`: one line per settled scenario with
the right status, leaving mid-journey gives `abandoned`, and a repeated identical click gives one
BI event.

Report what was instrumented (by source), what was proposed but not confirmed, and anything changed
from the user's original request and why. The final report repeats the `Scanned:` line and the
proposal tables, so the user sees the proposal without opening the transcript.

## Gotchas

- **Telemetry never throws into the app** — don't wrap calls in try/catch.
- **Strict TypeScript:** many app tsconfigs set `noPropertyAccessFromIndexSignature`. Then a
  recorded payload's keys must be read with brackets (`payload['error']`), not dots (`payload.error`),
  or the specs fail to compile (TS4111). Run the spec type-check; passing tests don't prove it.
- **App behaviour never depends on telemetry results.** Where the off switch
  (`withTelemetryEnabled` in Angular, `enabled: false` on the core) turns telemetry off, scenarios
  never settle, `settled$` / `onSettled` never fire, `find` / `getActive` find nothing and `query()`
  resolves `[]`. If the live check shows no debug lines, check that switch first.

## Out of scope

- Installing or wiring the library, credentials, destinations, route-navigation tracking →
  `ui-watchtower-setup`.
- CloudWatch dashboards, extended metrics, alarms.
- Sending the scenario id to the backend (ui-watchtower #29, unreleased).
- Server-side and native mobile apps.
