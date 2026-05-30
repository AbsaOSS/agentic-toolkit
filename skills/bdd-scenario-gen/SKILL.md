---
name: bdd-scenario-gen
description: >
  BDD scenario writing quality and agent-level scenario generation for @living-doc-bdd-copilot.
  Covers: writing Gherkin in plain business language, Given/When/Then correctness,
  one-behaviour-per-scenario rule, Scenario Outline, Background, anti-patterns, feature file
  types (US vs Functionality), @AC: traceability annotations (authoritative format), gap
  detection via living-doc-gap-finder, and step definition resolution against PageObjects.
  Triggers on: "write a Gherkin scenario", "BDD scenario", "standalone feature file",
  "Given When Then", "Scenario Outline", "Cucumber scenario", "behave scenario",
  "acceptance test in Gherkin", "should I use Background", "BDD anti-patterns",
  "review my feature file", "BDD scenarios for",
  "convert acceptance criteria to Gherkin", "# AC: comment", "exploratory scenario".
  Does NOT trigger for: implementing step definitions (use gherkin-step), writing unit tests,
  designing a test case table, generating the living-doc feature file header block or skeleton
  scenarios (use living-doc-scenario-creator).
license: Apache-2.0
compatibility: GitHub Copilot
---

# BDD Scenario Generation

> **Glossary:** User Story, AC, Feature, PageObject — see [living-doc-glossary](../references/living-doc-glossary.md) ([remote](https://github.com/AbsaOSS/agentic-toolkit/blob/master/skills/references/living-doc-glossary.md)).
> **BDD schemas:** US and Functionality feature file templates — see [living-doc-bdd-schemas](../references/living-doc-bdd-schemas.md) ([remote](https://github.com/AbsaOSS/agentic-toolkit/blob/master/skills/references/living-doc-bdd-schemas.md)).

Use for: writing or reviewing Gherkin scenarios, generating feature files from ACs, detecting uncovered ACs, resolving step stubs against PageObjects.

---

## Gap Detection (agent mode)

An AC is considered uncovered if no scenario in any `.feature` file carries the `@AC:<id>` traceability tag.

1. Use the `living-doc-gap-finder` skill (bottom-up mode) to identify User Stories with `ACTIVE` ACs that have no linked Gherkin scenario.
2. For each gap: generate scenario skeletons — one scenario per `ACTIVE` AC with the mandatory `@AC:` traceability tag. Skip `PLANNED` and `DEPRECATED` ACs.

---

## Feature File Types

Two categories of `.feature` files exist — they have different locations, headers, and scopes:

| Type | Location | Feature block | Scope |
|---|---|---|---|
| User Story (E2E) | `features/us/us-<nnn>-<kebab>.feature` | `Feature: <US title>` with As-a/I-can/so-that narrative + `@US_ID:US-<n>` tag | End-to-end, user perspective |
| Functionality (system test) | `features/functionalities/<feat-kebab>/func-<nnn>-<kebab>.feature` | `Feature: <Feature name> — <Functionality name>` + `@FUNC_ID:FUNC-<nnn>` tag | One atomic behavior, input to output |

For non-living-doc scenarios (exploratory probes, regression suites not tied to a US AC), `@AC:` annotations are not required. Use `@AC:STANDALONE` as an optional placeholder when explicitly signalling that a scenario is intentionally unlinked — `gherkin-living-doc-sync` will note it but not flag it as a traceability gap.

---

## Feature File Conventions

- File naming: `us-<nnn>-<kebab-title>.feature` under `features/us/`, e.g. `features/us/us-007-place-an-online-order.feature`.
- The `Feature:` header must restate the User Story narrative in `As a / I can / so that` form.
- Scenario step text must stay in business/domain language only — never mention selectors, HTTP calls, DOM details, or database operations.

---

## Write in the Ubiquitous Language

Scenarios must use the language of the business domain. Anyone on the product team must be able to read and verify them without knowing the implementation.

```gherkin
# ✅ — business language
Given a customer with a gold membership
When they place an order for 2 units of "SKU-100"
Then the order is confirmed and the total is £160.00

# ❌ — implementation details
Given the database contains a row in users with tier="gold"
When a POST request is sent to /api/orders with body { "sku": "SKU-100", "qty": 2 }
Then the response status is 201
```

---

## Given / When / Then

| Keyword | Purpose | Rule |
|---|---|---|
| **Given** | System state before the action | Preconditions only — no actions |
| **When** | The action the actor takes | Exactly one meaningful action per scenario |
| **Then** | Observable outcome | Assertions only — no actions |
| **And / But** | Continuation | Never as the first step in a block |

```gherkin
# ✅
Given the customer's cart contains 3 items
When the customer applies the promo code "SAVE10"
Then the cart total is reduced by 10%

# ❌ — multiple When actions (split into separate scenarios)
When the customer applies the promo code "SAVE10"
And the customer proceeds to checkout
And the customer enters payment details
```

---

## One Behaviour per Scenario

Each scenario must verify exactly one observable behaviour. If the scenario name contains "and", it likely tests two behaviours — split it.

---

## Scenario Outline for Data-Driven Variations

```gherkin
# ✅
Scenario Outline: Discount is applied correctly for each membership tier
  Given a customer with a <tier> membership
  When they purchase an item costing £100.00
  Then the total is £<total>

  Examples:
    | tier   | total |
    | gold   | 80.00 |
    | silver | 90.00 |
    | bronze | 95.00 |
```

When illustrating discount calculations, show the resulting order total in the `Then` step or `Examples:` table rather than the raw discount percentage. If the prompt does not give an amount, default to £100.00 for comparison tables and £200.00 for single-scenario threshold cases so the discounted outcome is concrete.

---

## Background

Use `Background` when **every** scenario in the file shares the same precondition. Keep Background to 3 steps or fewer. If only 2–3 scenarios share a precondition, duplicate the `Given` step — prefer clarity over abstraction. Keep `Background` to `Given` preconditions only, not `When` or `Then` steps.

When answering whether `Background` is appropriate, confirm all three checks: shared-by-every-scenario, 3-steps-or-fewer, and no-subset-sharing.

---

## Anti-Patterns

| Anti-pattern | Problem | Fix |
|---|---|---|
| UI selectors in steps (`I click the "Submit" button`) | Breaks when UI changes | Use domain actions (`the customer submits the order`) |
| Imperative style (`I enter "alice@example.com" in Email field`) | Fragile and verbose | Declarative (`the customer logs in as Alice`) |
| Multiple `When` per scenario | Usually signals multiple behaviours | Prefer splitting; if all steps represent one logical action, collapse into one declarative step |
| Assertions in Given/When | Violates keyword semantics | Move all assertions to `Then` |
| Scenario depends on a previous scenario's state | Hidden ordering dependency | Each scenario must be fully self-contained |

When reviewing an existing scenario, explicitly check for a missing `@AC:` tag immediately above each `Scenario:` or `Scenario Outline:` and call that out as a traceability defect.

---

## Traceability Annotations

Living-doc feature files (`features/us/` and `features/functionalities/`) require two complementary annotations above each `Scenario:` or `Scenario Outline:`:

1. **`# AC:` comment** — human-readable context: AC ID, version, state, description, and optionally the specific aspect this scenario covers.
2. **`@AC:` tag** — machine-readable Cucumber tag consumed by scripts and coverage reports.

```gherkin
# AC:US-1-01 (v1.0.0 - ACTIVE) — customer places an order with a saved payment method
@AC:US-1-01
Scenario: Customer successfully places an order
  ...
```

When a scenario covers only **one aspect** of a multi-aspect AC, encode the aspect as a `/param:value` segment on the tag and mirror it in the comment:

```gherkin
# AC:US-1-01 (v1.0.0 - ACTIVE) — displays {required field} on login screen | aspect: username input
@AC:US-1-01/aspect:username-input
Scenario: Login form shows the username input field
  ...
```

The `/param:value` format is extensible. Multiple ACs — one comment + tag pair per AC:

```gherkin
# AC:US-1-01 (v1.0.0 - ACTIVE) — invalid credentials show an error message
# AC:US-1-02 (v1.0.0 - ACTIVE) — account lockout after 3 failed attempts
@AC:US-1-01
@AC:US-1-02
@Regression
Scenario: User is locked out after repeated failed logins
  ...
```

The AC tag prefix matches the parent entity: `@AC:US-<n>-<nn>` for User Story scenarios, `@AC:FUNC-<nnn>-<nn>` for Functionality scenarios.

---

## Step Definition Resolution (agent mode)

For each generated scenario step:

a. **Narrow the search scope to the page first** — identify which PageObject the scenario's steps will interact with. Look in step definition files that already import or reference that PageObject; these are the most likely candidates for reuse.

b. **Match by purpose, not just pattern** — read the step's implementation body to confirm it performs the same business action. Only reuse if purpose matches.

c. If a purpose-matching step exists, reuse it as-is; note which library file it lives in.

d. If no reusable step exists but the needed PageObject method already exists, generate a full step stub via `gherkin-step` that delegates directly to that PageObject method.

e. If neither the step nor the PageObject method exists, generate a stub that raises `NotImplementedError` and flag that the PageObject must be extended with the missing interaction.

After resolution, update `manifest.json` to record any new PageObject paths created.

---

## Output Format

Output all generated Gherkin in a single fenced `gherkin` code block starting with `Feature:`. Use only `Scenario:`, `Scenario Outline:`, `Background:`, `Given`, `When`, `Then`, `And`, `But`, and `Examples:` inside the block.

---

## Out-of-Scope Routing

| Request | Use instead |
|---|---|
| Implementing step definitions | **gherkin-step** |
| Writing unit tests | Use your project's unit test framework directly |
| Designing a test case table | Use your project's test design practice |
| Generate a living-doc US entity with AC coverage report | **living-doc-scenario-creator** |

If asked for step definition code, do not write it here — redirect to **gherkin-step**. If asked for a US entity skeleton with an AC coverage report, redirect to **living-doc-scenario-creator**.

**Ambiguous request — "create scenarios for US-007":** If the user does not specify whether they want the feature file structure or full scenario bodies, ask:
> "Do you want the living-doc feature file header and skeleton scenario titles (use `living-doc-scenario-creator`), or full Given/When/Then scenario bodies (continue here in `bdd-scenario-gen`)?"
Both skills handle different parts of the same feature file — they are meant to be used in sequence.
