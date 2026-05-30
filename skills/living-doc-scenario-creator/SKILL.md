---
name: living-doc-scenario-creator
description: >
  Generate Gherkin scenarios and living-doc feature files from User Story and Functionality ACs.
  Covers full feature file output (@AC:-tagged scenarios, GWT bodies), Scenario Outline,
  Background, AC coverage report, anti-pattern detection, and step definition resolution.
  Two modes: entity (from US/FUNC) and standalone.
  Triggers on: "write a Gherkin scenario", "BDD scenario", "standalone feature file",
  "Given When Then", "Scenario Outline", "BDD anti-patterns", "review my feature file",
  "BDD scenarios for", "convert acceptance criteria to Gherkin", "exploratory scenario",
  "feature file header for user story", "living-doc feature file", "bootstrap feature file for US",
  "cover AC with scenarios", "scenario coverage for US", "map AC to scenarios", "scenario creator".
  Does NOT trigger for: implementing step definitions (use gherkin-step); writing unit tests.
  Pairs with living-doc-create-user-story, living-doc-pageobject-scan, and gherkin-step.
license: Apache-2.0
compatibility: GitHub Copilot
---

# Living Doc — Scenario Creator

> **Glossary:** User Story, AC, Feature, PageObject — see [living-doc-glossary](../references/living-doc-glossary.md) ([remote](https://github.com/AbsaOSS/agentic-toolkit/blob/master/skills/references/living-doc-glossary.md)).
> **BDD schemas:** US and Functionality feature file templates — see [living-doc-bdd-schemas](../references/living-doc-bdd-schemas.md) ([remote](https://github.com/AbsaOSS/agentic-toolkit/blob/master/skills/references/living-doc-bdd-schemas.md)).

**AC states:** `PLANNED` · `IN_REVIEW` · `ACTIVE` · `DEPRECATED`. Only `ACTIVE` ACs drive scenario generation.

---

## Two modes

| Mode | When to use |
|---|---|
| **Entity mode** | A User Story or Functionality entity exists — generate full feature file with header, `@AC:` tags, and step bodies. |
| **Standalone mode** | No US/FUNC entity — write Gherkin directly from business descriptions. Use `@AC:STANDALONE` as tag; `gherkin-living-doc-sync` will note it but not flag a traceability gap. |

---

## Entity mode workflow

### Step 1 — Read the entity

Load the User Story or Functionality. Confirm:
- ID follows `US-<nnn>` or `FUNC-<nnn>` format.
- Which ACs are `ACTIVE` (eligible for generation).
- ACs are atomic — one input condition, one observable outcome.

If no ACs are `ACTIVE`, do not generate empty scenarios. Output a coverage report with state-specific skip reasons (`PLANNED`: `skipped — not yet active`, `DEPRECATED`: `skipped — deprecated AC`) and advise the user to re-run when an AC becomes `ACTIVE`.

### Step 2 — Gap detection and merge policy

An AC is uncovered if no `.feature` file carries `@AC:<id>`. Use `living-doc-gap-finder` (bottom-up mode) to identify `ACTIVE` ACs with no linked scenario before writing new files.

**If a scenario already exists for an AC**, apply this policy:

| Existing scenario state | Action |
|---|---|
| Matches AC intent; GWT correct | **Skip** — record `already covered` in the coverage report |
| Step text stale or AC description changed | **Update** — rewrite GWT in-place; keep `@AC:` tag and title stable |
| Tagged `@deprecated` or `@review-needed` | **Propose replacement** — draft new scenario; confirm with user before overwriting |
| Multiple scenarios for the same AC | **Flag** — list them; ask user: valid aspect split or consolidate? |

### Step 3 — Generate feature file

For each `ACTIVE` AC, output `# AC:` comment, `@AC:` tag, `Scenario:` title, and full Given/When/Then step bodies.

**Scenario title by AC type:**
- `happy_path` → `Scenario: <positive outcome>`
- `error` → `Scenario: <US title> — <error condition>`
- `alternative` → `Scenario: <US title> — <alternative path>`

**Traceability format** (authoritative — `gherkin-living-doc-sync` validates against this definition):

```gherkin
# AC:US-1-01 (v1.0.0 - ACTIVE) — customer places an order with a saved payment method
@AC:US-1-01
Scenario: Customer successfully places an order
  Given the customer has items in their cart
  When they confirm the order with their saved payment method
  Then the order confirmation is displayed
```

Aspect variant (when one scenario covers only one aspect of a multi-aspect AC):

```gherkin
# AC:US-1-01 (v1.0.0 - ACTIVE) — displays {required field} on login screen | aspect: username input
@AC:US-1-01/aspect:username-input
Scenario: Login form shows the username input field
```

Multiple ACs per scenario — one comment + tag pair per AC:

```gherkin
# AC:US-1-01 (v1.0.0 - ACTIVE) — invalid credentials show an error message
# AC:US-1-02 (v1.0.0 - ACTIVE) — account lockout after 3 failed attempts
@AC:US-1-01
@AC:US-1-02
@Regression
Scenario: User is locked out after repeated failed logins
```

AC tag prefix matches the parent entity: `@AC:US-<n>-<nn>` for User Story, `@AC:FUNC-<nnn>-<nn>` for Functionality.

**Feature file types:**

| Type | Location | Feature block |
|---|---|---|
| User Story (E2E) | `features/us/us-<nnn>-<kebab>.feature` | `Feature: <US title>` with As-a/I-can/so-that + `@US_ID:US-<n>` |
| Functionality | `features/functionalities/<feat-kebab>/func-<nnn>-<kebab>.feature` | `Feature: <Feature name> — <Functionality name>` + `@FUNC_ID:FUNC-<nnn>` |

**US feature file example:**

```gherkin
# us-001-place-an-online-order.feature

# Business Value:
#   - Customers can complete an order without calling support.

# Acceptance Criteria:
#   AC:US-001-01 (v1.0.0 - Active) — customer places an order with a saved payment method.
#   AC:US-001-02 (v1.0.0 - Active) — order is rejected when the payment card is declined.

@US_ID:US-001
Feature: Place an online order
  As a registered customer
  I can place an order for in-stock items
  So that the items are delivered to my address

  # AC:US-001-01 (v1.0.0 - Active) — customer places an order with a saved payment method
  @AC:US-001-01
  Scenario: Customer successfully places an order
    Given the customer has items in their cart
    When they confirm the order with their saved payment method
    Then the order confirmation is displayed

  # AC:US-001-02 (v1.0.0 - Active) — order is rejected when the payment card is declined
  @AC:US-001-02
  Scenario: Order rejected when payment card is declined
    Given the customer has items in their cart
    When they attempt to pay with a declined card
    Then an error message is shown and the order is not placed
```

**Functionality feature file example:**

```gherkin
@FUNC_ID:FUNC-001
Feature: Login Page — Validate Password Strength

  # AC:FUNC-001-01 (v1.0.0 - Active) — returns valid=true when password satisfies all rules
  @AC:FUNC-001-01
  Scenario: Password meets all complexity rules
    Given a password with at least 8 characters, one uppercase, one lowercase, and one number
    When password strength is validated
    Then the result is valid
```

### Step 4 — AC coverage report

Run `scripts/coverage_report.py <living_doc_dir> <features_dir>` for a full report. Append after the `.feature` code block:

```
AC COVERAGE REPORT — US-001
  AC:US-001-01 (ACTIVE): ✅ covered
  AC:US-001-02 (ACTIVE): ✅ covered
  AC:US-001-03 (ACTIVE): ❌ NOT COVERED
  AC:US-001-04 (PLANNED): ⏭  skipped — not yet active
```

### Step 5 — Step definition resolution

For each generated scenario step:

1. Narrow scope to the relevant PageObject first — check step files that import it for reuse candidates.
2. Match by purpose, not just pattern — confirm the implementation performs the same business action.
3. If purpose-matching step exists, reuse it; note the source file.
4. If no reuse candidate but the PageObject method exists, generate a thin step stub via `gherkin-step`.
5. If neither exists, generate a stub that raises `NotImplementedError` and flag the PageObject extension needed.

---

## Gherkin quality rules

### Write in the ubiquitous language

Scenarios must use business domain language. Anyone on the product team must be able to read and verify them without implementation knowledge.

```gherkin
# ✅
Given a customer with a gold membership
When they place an order for 2 units of "SKU-100"
Then the order is confirmed and the total is £160.00

# ❌ — implementation details
Given the database contains a row in users with tier="gold"
When a POST request is sent to /api/orders
Then the response status is 201
```

### GWT keyword rules

| Keyword | Purpose | Rule |
|---|---|---|
| **Given** | System state before the action | Preconditions only — no actions, no assertions |
| **When** | The action the actor takes | Exactly one meaningful action per scenario |
| **Then** | Observable outcome | Assertions only — no actions |
| **And / But** | Continuation | Never as the first step in a block |

One behaviour per scenario. If the scenario name contains "and", it likely tests two behaviours — split it.

### Scenario Outline

Use for data-driven variations. Show concrete outcome values in `Examples:`, not raw percentages:

```gherkin
Scenario Outline: Discount applied correctly for each membership tier
  Given a customer with a <tier> membership
  When they purchase an item costing £100.00
  Then the total is £<total>

  Examples:
    | tier   | total |
    | gold   | 80.00 |
    | silver | 90.00 |
```

### Background

Use only when every scenario in the file shares the precondition. Keep to 3 steps or fewer. If only 2–3 scenarios share a precondition, duplicate the `Given` step — prefer clarity over abstraction. `Background` must use only `Given` steps.

### Anti-patterns

| Anti-pattern | Fix |
|---|---|
| UI selectors in steps (`I click the "Submit" button`) | Domain action (`the customer submits the order`) |
| Imperative style (`I enter "alice@example.com" in Email field`) | Declarative (`the customer logs in as Alice`) |
| Multiple `When` per scenario | Split into separate scenarios |
| Assertions in Given/When | Move all assertions to `Then` |
| Scenario depends on prior scenario state | Make every scenario fully self-contained |

When reviewing an existing scenario, check for a missing `@AC:` tag above each `Scenario:` — call that out as a traceability defect.

---

## Standalone mode

When no User Story or Functionality entity exists, generate scenarios directly from business descriptions:

- Apply all GWT rules and ubiquitous language rules above.
- Use `@AC:STANDALONE` as an optional tag to signal intentionally unlinked scenarios.
- Omit the header block (`# Business Value:`, `# Acceptance Criteria:`, `@US_ID:`) — start directly with `Feature:`.
- File location is at the user's discretion; `gherkin-living-doc-sync` will note `@AC:STANDALONE` but not flag a traceability gap.

---

## Output format

Output all generated Gherkin in a single fenced `gherkin` code block starting with `Feature:`. Use only `Scenario:`, `Scenario Outline:`, `Background:`, `Given`, `When`, `Then`, `And`, `But`, `Examples:` inside the block.

---

## Out-of-scope routing

| Request | Correct skill |
|---|---|
| Implementing step definition code | `gherkin-step` |
| Writing unit tests | Use your project's test framework directly |
| Syncing `@AC:` tags and traceability in existing feature files | `gherkin-living-doc-sync` |


