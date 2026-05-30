---
name: bdd-scenario-gen
description: >
  Generate Gherkin scenario skeletons from User Story Acceptance Criteria and resolve
  step definitions for the @living-doc-bdd-copilot agent. Activate after exploration
  completes (manifest up to date) or when a specific US needs BDD coverage.
  Covers gap detection logic, scenario skeleton generation, step reuse/stub rules,
  feature file naming and header conventions, and @AC: traceability tagging.
  Triggers on: "generate scenarios", "cover AC with scenarios", "generate feature file",
  "gherkin from user story", "scenario coverage", "map AC to scenarios",
  "AC coverage for US", "scenarios for US-", "bdd scenario gen".
---

# BDD Scenario Generation

Use after exploration completes (manifest is up to date), or targeting a specific User Story.

---

## Gap Detection

An AC is considered uncovered if no scenario in any `.feature` file carries the `@AC:<id>` traceability tag.

1. Use the `living-doc-gap-finder` skill (bottom-up mode) to identify User Stories with `ACTIVE` ACs that have no linked Gherkin scenario.
2. For each gap: generate Gherkin scenario skeletons — one scenario per `Active` or `Implemented` AC, with the mandatory `@AC:` traceability tag. Skip `Planned` and `Deprecated` ACs.

---

## Feature File Conventions

- Write `.feature` files under `features/us/` using `us-<nnn>-<kebab-title>.feature` naming, e.g. `features/us/us-007-place-an-online-order.feature`.
- The `Feature:` header must restate the User Story narrative in `As a / I can / so that` form.
- Scenario step text must stay in business/domain language only — never mention selectors, HTTP calls, DOM details, or database operations.

---

## Traceability Annotations

Every `Scenario:` or `Scenario Outline:` in a living-doc feature file must carry two complementary annotations:

1. A `# AC:` comment — human-readable context (ID, version, state, description, optional aspect).
2. An `@AC:` Cucumber tag — machine-readable link: `@AC:<id>[/param:value...]`.

```gherkin
# AC:US-1-01 (v1.0.0 - Active) — customer places an order with a saved payment method
@AC:US-1-01
Scenario: Customer successfully places an order
```

When the scenario covers only **one aspect** of a multi-aspect AC, encode it as a `/param:value` segment:

```gherkin
# AC:US-1-01 (v1.0.0 - Active) — displays {required field} on login screen | aspect: username input
@AC:US-1-01/aspect:username-input
Scenario: Login form shows the username input field
```

Multiple ACs — one comment + tag pair per AC:

```gherkin
# AC:US-1-01 (v1.0.0 - Active) — invalid credentials show an error message
# AC:US-1-02 (v1.0.0 - Active) — account lockout after 3 failed attempts
@AC:US-1-01
@AC:US-1-02
@Regression
Scenario: User is locked out after repeated failed logins
```

Feature files outside `features/us/` and `features/functionalities/` (smoke tests, regression suites, exploratory probes) do not require these annotations.

---

## Step Definition Resolution

For each generated scenario:

a. **Narrow the search scope to the page first** — identify which PageObject the scenario's steps will interact with. Look in step definition files that already import or reference that PageObject; these are the most likely candidates for reuse.

b. **Match by purpose, not just pattern** — read the step's implementation body to confirm it performs the same business action (e.g. a `fill` on `username-input` vs a `fill` on `search-input` look identical in text but serve different purposes). Only reuse if purpose matches.

c. If a purpose-matching step exists, reuse it as-is; note which library file it lives in.

d. If no reusable step exists but the needed PageObject method already exists, generate a full step stub via `gherkin-step` that delegates directly to that PageObject method.

e. If neither the step nor the PageObject method exists, generate a stub that raises `NotImplementedError` (or the language-equivalent pending marker) and explicitly flag that the PageObject must be extended with the missing interaction.

After resolution, update `manifest.json` to record any new PageObject paths created.
