# UI Watchtower Integration Skill

The `ui-watchtower-integration` skill measures what matters in a specific Angular app with
[`@absaoss-cps/ngx-ui-watchtower`](https://www.npmjs.com/package/@absaoss-cps/ngx-ui-watchtower):
**scenarios** (did a user journey succeed, and how long did it take) and **BI events** (did a
meaningful thing happen).

It starts from what you want to learn, not only from what it finds in the code: it asks first,
proposes a plan that marks which items you asked for and which it suggests, and implements only what
you confirm. Run it again whenever the app grows — each pass adds to what is already instrumented.

The library must already be installed and wired — use [UI Watchtower Setup](./ui-watchtower-setup.md)
first.

---

## What it does

| Step | Action |
|---|---|
| Check | Confirms the library is installed with a destination, otherwise stops and points to the setup skill; reads what is already instrumented so a re-run only adds |
| Ask | One short set of questions: what the telemetry should answer, which journeys matter and what success means, which interactions to count, known pain points, what must not be tracked, scope of this pass |
| Scan | Finds candidate journeys, clicks and journey-ending errors in the code, within that scope |
| Propose | A merged plan with a **Source** column (`you` / `suggested`) and a section for requests it had to change (e.g. no raw search text, no ids in names) with the alternative |
| Implement | Only what you confirmed — names in the schema, the right settle status for each outcome, cleanup on destroy |
| Test & validate | A test per outcome through a recording sink; build, unit tests, a real type-check, a live check with the debug flags |

---

## How to trigger it

```
instrument the checkout flow as a scenario
we want to know if customer search is slow — add telemetry
which journeys should we measure in this app?
track how often people use the export
add BI events for the main buttons
```

---

## What you'll be asked

1. Which questions should this telemetry answer?
2. Which user journeys matter most, and what counts as success?
3. Which interactions or features do you want usage numbers for?
4. Known pain points, incidents or support tickets to watch?
5. Anything that must not be tracked?
6. Scope of this pass — the whole app or one area?

Questions your request already answers are skipped. "Just suggest something" works too: the proposal
then says it is based on the code only.

---

## Out of scope

- Installing or wiring the library → [UI Watchtower Setup](./ui-watchtower-setup.md)
- CloudWatch dashboards, RUM extended metrics and alarms
- A backend correlation-header interceptor (offered as a follow-up)
- Non-Angular applications

---

## Installation

```bash
npx skills add https://github.com/AbsaOSS/agentic-toolkit -g --skill ui-watchtower-integration
```

See [Getting Started](../getting-started.md) for the full install guide.
