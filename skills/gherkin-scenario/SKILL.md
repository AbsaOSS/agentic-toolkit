---
name: gherkin-scenario
description: >
  Writing BDD Gherkin scenarios in plain business language. Activate when writing or reviewing
  feature files, Given/When/Then steps, Scenario Outlines, Background blocks, or acceptance
  criteria expressed as Gherkin. Covers business-language principles, one-behaviour-per-scenario
  rule, anti-patterns (implementation leakage, multiple When actions, UI-speak in domain
  scenarios), and data-driven scenario design.
  Triggers on: "write a Gherkin scenario", "BDD scenario", "feature file", "Given When Then",
  "Scenario Outline", "Cucumber scenario", "behave scenario", "acceptance test in Gherkin",
  "should I use Background", "BDD anti-patterns", "review my feature file", "BDD scenarios for",
  "convert acceptance criteria to Gherkin".
  Does NOT trigger for: implementing step definitions (use gherkin-step), writing unit tests
  (use test-unit-write), designing a test case table (use test-case-design).
  Pairs with gherkin-step for step definition implementation.
---

# Gherkin Scenario Standards

> **Glossary:** User Story, AC, Feature — see [living-doc-glossary](../references/living-doc-glossary.md) ([remote](https://github.com/AbsaOSS/agentic-toolkit/blob/master/skills/references/living-doc-glossary.md)).

## Traceability requirement

Living-doc feature files (`features/us/` and `features/functionalities/`) require two
complementary annotations above each `Scenario:` or `Scenario Outline:`:

1. **`# AC:` comment** — human-readable context: AC ID, version, state, description, and
   optionally the specific aspect this scenario covers.
2. **`@AC:` tag** — machine-readable Cucumber tag consumed by scripts and coverage reports.

```gherkin
# AC:US-1-01 (v1.0.0 - Active) — customer places an order with a saved payment method
@AC:US-1-01
Scenario: Customer successfully places an order
  ...
```

When a scenario covers only **one aspect** of a multi-aspect AC, encode the aspect as a
`/param:value` segment on the tag and mirror it in the comment:

```gherkin
# AC:US-1-01 (v1.0.0 - Active) — displays {required field} on login screen | aspect: username input
@AC:US-1-01/aspect:username-input
Scenario: Login form shows the username input field
  ...
```

The `/param:value` format is extensible — future params (e.g. `/coverage:partial`) can be
appended. Multiple ACs — one comment + tag pair per AC:

```gherkin
# AC:US-1-01 (v1.0.0 - Active) — invalid credentials show an error message
# AC:US-1-02 (v1.0.0 - Active) — account lockout after 3 failed attempts
@AC:US-1-01
@AC:US-1-02
@Regression
Scenario: User is locked out after repeated failed logins
  ...
```

The AC tag prefix matches the parent entity: `@AC:US-<n>-<nn>` for User Story scenarios,
`@AC:FUNC-<nnn>-<nn>` for Functionality scenarios.

**Scope:** These annotations are only required in living-doc feature files. Other feature files
(smoke tests, regression suites, exploratory probes) do not require `@AC:` tags and may use
`@AC:STANDALONE` as an optional placeholder to signal intent. `gherkin-living-doc-sync` reports
`STANDALONE`-tagged scenarios but does not flag them as traceability gaps.

---

## Feature file types

Two categories of `.feature` files exist — they have different locations, headers, and scopes:

| Type | Location | File header | Feature block | Scope |
|---|---|---|---|---|
| User Story (E2E) | `features/us/us-<nnn>-<kebab>.feature` | `# Source:`, `# Business Value:`, `# Acceptance Criteria:` block + `@US_ID:US-<n>` feature tag | `Feature: <US title>` with As-a/I-can/so-that narrative | End-to-end, user perspective |
| Functionality (system test) | `features/functionalities/<feat-kebab>/func-<nnn>-<kebab>.feature` | Similar to US — format TBD; `@FUNC_ID:FUNC-<nnn>` feature tag | `Feature: <Feature name> — <Functionality name>` | One atomic behavior, input to output |

Both types use the `@AC:` + `# AC:` traceability annotations described above. Both must be written in business domain language — no implementation details, selectors, or code references.

For non-living-doc scenarios (exploratory probes, tutorial walkthroughs, regression suites not tied to a User Story AC), `@AC:` annotations are not required. Use `@AC:STANDALONE` as an optional placeholder when explicitly signalling that a scenario is intentionally unlinked — `gherkin-living-doc-sync` will note it but not flag it as a traceability gap.

---

## Write in the ubiquitous language

Scenarios must use the language of the business domain. Anyone on the product team must be
able to read and verify them without knowing the implementation.

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

## Follow Given / When / Then correctly

| Keyword | Purpose | Rule |
|---------|---------|------|
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

## One behaviour per scenario

Each scenario must verify exactly one observable behaviour. If the scenario name contains "and",
it likely tests two behaviours — split it.

---

## Use Scenario Outline for data-driven variations

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

When illustrating discount calculations, show the resulting order total in the `Then` step or
`Examples:` table rather than the raw discount percentage. If the prompt does not give an amount,
default to a £100.00 order for comparison tables and to £200.00 for single-scenario threshold cases
such as "orders over £100" so the discounted outcome is concrete.

---

## Use Background for shared preconditions

Use `Background` when **every** scenario in the file shares the same precondition.
Keep Background to 3 steps or fewer. If only 2–3 scenarios share a precondition,
duplicate the `Given` step — prefer clarity over abstraction.
When answering whether `Background` is appropriate, explicitly mention all three checks:
shared-by-every-scenario, 3-steps-or-fewer, and duplicate the `Given` steps instead when only a
subset of scenarios needs them. Keep `Background` to shared `Given` preconditions, not `When` or
`Then` steps.

---

## Avoid common anti-patterns

| Anti-pattern | Problem | Fix |
|---|---|---|
| UI selectors in steps (`I click the "Submit" button`) | Breaks when UI changes | Use domain actions (`the customer submits the order`) |
| Imperative style (`I enter "alice@example.com" in Email field`) | Fragile and verbose | Declarative (`the customer logs in as Alice`) |
| Multiple `When` per scenario | Usually signals multiple behaviours — try to avoid | Prefer splitting into separate scenarios; if all steps represent a single logical action, collapse into one declarative step |
| Assertions in Given/When | Violates keyword semantics | Move all assertions to `Then` |
| Scenario depends on a previous scenario's state | Hidden ordering dependency | Each scenario must be fully self-contained |

When reviewing an existing scenario, explicitly check for a missing `@AC:` tag immediately
above each `Scenario:` or `Scenario Outline:` and call that out as a traceability defect.

---

## Output format for generated scenarios

Output all generated Gherkin in a single fenced `gherkin` code block starting with `Feature:`.
Use only `Scenario:`, `Scenario Outline:`, `Background:`, `Given`, `When`, `Then`, `And`, `But`,
and `Examples:` inside the block.

---

## Out-of-scope routing

| Request | Use instead |
|---|---|
| Implementing step definitions | **gherkin-step** |
| Writing unit tests | **test-unit-write** |
| Designing a test case table | **test-case-design** |

If asked for step definition code, do not write it here. Redirect to **gherkin-step** and explain
that this skill writes or reviews Gherkin scenario text, while **gherkin-step** implements the step
binding code.
