---
name: living-doc-scenario-creator
description: >
  From User Stories and Acceptance Criteria, generate BDD Gherkin scenario skeletons in
  .feature files and identify step implementations needed using available PageObjects.
  Activate when generating Gherkin scenarios from a User Story, covering US AC with BDD
  scenarios, mapping Given-When-Then to PageObject actions, identifying missing step
  definitions, or auditing scenario-to-AC coverage.
  Triggers on: "create BDD scenarios for user story", "generate scenarios for US",
  "cover AC with scenarios", "generate feature file from user story", "BDD from requirements",
  "scenario coverage for US", "map AC to scenarios", "gherkin from user story", "scenarios for US-",
  "generate .feature file".
  Does NOT trigger for: standalone Gherkin without a User Story (use gherkin-scenario),
  implementing step definitions (use gherkin-step), writing unit tests (use test-unit-write),
  doc gaps or undocumented behaviors (use living-doc-gap-finder).
  Pairs with living-doc-create-user-story, gherkin-scenario, and living-doc-pageobject-scan.
---

# Living Doc — Scenario Creator

> **Glossary:** User Story, AC, PageObject, step definitions — see [living-doc-glossary](../references/living-doc-glossary.md) ([remote](https://github.com/AbsaOSS/agentic-toolkit/blob/master/skills/references/living-doc-glossary.md)).

## Glossary alignment

**AC ID format:** `AC:<parent-id>-<nn>` — e.g. `AC:US-001-01`, `AC:US-001-02`

**AC traceability** (required for living-doc feature files — placed above every `Scenario:` in `features/us/` and `features/functionalities/`):

```gherkin
# AC:US-1-01 (v1.0.0 - Active) — customer places an order with a saved payment method
@AC:US-1-01
Scenario: Customer successfully places an order
```

When a scenario covers only **one aspect** of a multi-aspect AC, encode it as a `/aspect:value`
param on the tag and mirror it in the comment:

```gherkin
# AC:US-1-01 (v1.0.0 - Active) — displays {required field} on login screen | aspect: username input
@AC:US-1-01/aspect:username-input
Scenario: Login form shows the username input field
```

The `/param:value` format is extensible — additional params can be added after `/aspect:value`.
The `# AC:` comment provides human context (version, state, description, aspect). The `@AC:` Cucumber tag provides machine traceability for scripts and coverage reports.

Only ACs with state `Active` or `Implemented` drive scenario generation.
ACs with state `Planned` or `Deprecated` are excluded from generation; note them in the coverage report.

---

## Inputs required

| Input | Source | Required |
|---|---|---|
| User Story (with ACs) | User Story entity file (or inline JSON) | Yes |
| Available PageObjects | `tests/pages/` directory | Recommended |
| Existing step definitions | `tests/steps/` directory | Recommended |

If PageObjects or step files are not available, generate scenarios with stub step implementations
(see Step 3 for the two-case protocol: PageObject method found vs. not found).

---

## Workflow

### Step 1 — Read the User Story

Load the User Story. Confirm:
- ID follows `US-<nnn>` format
- Which ACs are eligible for generation (`Active` or `Implemented`)
- ACs are atomic — each has one input condition and one observable outcome

Treat requests such as “write feature tests for US-007” as requests to generate BDD scenarios plus a coverage table for that User Story.

If no ACs are `Active` or `Implemented`, do **not** generate empty or stub scenarios. Instead,
output a coverage report that lists every AC with its state-specific skip reason (`Planned`:
`skipped — not yet active`, `Deprecated`: `skipped — deprecated AC`) and advise the user to
re-run the scenario creator when an AC becomes `Active` or `Implemented`.

### Step 2 — Map each AC to a scenario

For each active AC, select the scenario pattern by AC type:
- `happy_path`: `Scenario:` or `Scenario Outline:` (if data-driven)
- `error`: `Scenario: <US title> — <error condition>`. If the AC text already gives a crisp business-facing failure title (for example, `Order rejected when payment card is declined`), prefer that exact title instead of mechanically prefixing the User Story title.
- `alternative`: `Scenario: <US title> — <alternative path>`

Generate a scenario for **every** active AC.

Map Given-When-Then from the AC to existing step definitions — reuse exact step text where found. Keep all step text in domain/business language only; never mention HTTP, APIs, selectors, DOM details, databases, or other implementation mechanics.

```gherkin
# AC:US-1-01 (v1.0.0 - Active) — customer places an order with a saved payment method
@AC:US-1-01
Scenario: Customer successfully places an order
  Given the customer has items in their cart and a saved payment method
  When the customer confirms the order
  Then the order is confirmed
  And a confirmation email is sent to the customer
  And the cart is emptied
```

### Step 3 — Implement missing step stubs

For each step not found in existing step files, generate a named stub function in the
appropriate step file. Apply the following two-case protocol:

**Case A — A PageObject method can implement the step:**

Generate the full stub using the available method:

```
MISSING STEP: "Given the customer has items in their cart and a saved payment method"
  PageObject candidate: CheckoutPage (FEAT-003)
  Suggested step file: tests/steps/checkout_steps.py
  Generated stub:
      @given('the customer has items in their cart and a saved payment method')
      def step_customer_has_cart_with_payment(context):
          context.checkout_page = CheckoutPage(context.browser)
          context.checkout_page.add_item_to_cart("SKU-100", quantity=1)
          context.checkout_page.set_saved_payment_method()
```

**Case B — No matching PageObject method exists for the step:**

Generate a stub with a `NotImplementedError` failure guard and flag the gap to
`living-doc-pageobject-scan` (Maintain mode) so it can extend the PageObject:

```
MISSING STEP + MISSING PAGEOBJECT METHOD:
  "When the customer applies a promo code"
  No matching method found in CheckoutPage (FEAT-003)
  Generated stub (with failure guard):
      @when('the customer applies a promo code')
      def step_apply_promo_code(context):
          raise NotImplementedError(
              "Step not implemented: 'the customer applies a promo code'. "
              "CheckoutPage (FEAT-003) is missing an 'apply_promo_code' method. "
              "Run living-doc-pageobject-scan (Maintain mode) on FEAT-003 to add it."
          )
  Action: invoke living-doc-pageobject-scan (Maintain mode) for the missing element
```

### Step 4 — Validate AC coverage

Every `Active` or `Implemented` AC must map to at least one scenario.
The coverage report must list **every** AC on the User Story, including skipped ones.
Use these skip reasons verbatim so the output is predictable and auditable:
- `Planned`: `skipped — not yet active`
- `Deprecated`: `skipped — deprecated AC`

Run `scripts/coverage_report.py <living_doc_dir> <features_dir>` for a full coverage report.

```
AC COVERAGE REPORT — US-001
  AC:US-001-01 (Active): ✅ covered by "Customer successfully places an order"
  AC:US-001-02 (Active): ✅ covered by "Order rejected when payment card is declined"
  AC:US-001-03 (Active): ❌ NOT COVERED — added to gap list
  AC:US-001-04 (Planned): ⏭  skipped — not yet active
  AC:US-001-05 (Deprecated): ⏭  skipped — deprecated AC
```

Use `scripts/coverage_report.py` to generate this report across all entities.

### Step 5 — Output artifacts

**`.feature` file** — one per User Story, named `us-<nnn>-<kebab-title>.feature` in lowercase. The file starts with a header block (matching the project's US feature file convention) and uses `@AC:` traceability tags above each scenario. When showing the generated output, include the filename as a comment:

```gherkin
# us-001-place-an-online-order.feature

# Source: https://github.com/<org>/<repo>/issues/<n>

# Business Value:
#   - <concise value statement>

# Acceptance Criteria:
#
#   AC:US-001-01 (v1.0.0 - Active)
#     - Customer places an order with a saved payment method.
#
#   AC:US-001-02 (v1.0.0 - Active)
#     - Order is rejected when the payment card is declined.

@US_ID:US-001
Feature: Place an online order
  As a registered customer
  I can place an order for in-stock items
  So that the items are delivered to my address

  # AC:US-001-01 (v1.0.0 - Active) — customer places an order with a saved payment method
  @AC:US-001-01
  Scenario: Customer successfully places an order
    ...

  # AC:US-001-02 (v1.0.0 - Active) — order is rejected when the payment card is declined
  @AC:US-001-02
  Scenario: Order rejected when payment card is declined
    ...
```

**Missing step report** — generated stub implementations grouped by step file; Case B stubs include `NotImplementedError` failure guards and flag missing PageObject methods for extension (see Step 3).

**Coverage table** — ACs with coverage status (use `scripts/coverage_report.py`). Append it immediately after the `.feature` code block in the response.

---

## Step reuse rules

1. **Narrow to page scope first** — identify which PageObject the scenario's steps interact with. Only look in step definition files that already import or reference that PageObject; those are the most likely reuse candidates.
2. **Match by purpose, not just text** — read the step implementation body to confirm it performs the same business action. Two steps may have identical text but operate on different elements (e.g. a `fill` on `username-input` vs `search-input`). Only reuse if the purpose matches.
3. If a purpose-matching step exists, reuse it as-is; note the file it lives in.
4. Only if no match exists: write a new stub using the `gherkin-step` skill. If an existing step is close but not identical, suggest a parameter to generalise it rather than duplicating.
5. Never create duplicate step definitions — search before creating.

## File placement

| Step domain | Example step file |
|---|---|
| Authentication | `tests/steps/auth_steps.py` |
| Checkout / order | `tests/steps/checkout_steps.py` |
| Common / shared | `tests/steps/common_steps.py` |
| Domain-specific | `tests/steps/<domain>_steps.py` |

> **Note:** Paths above are illustrative examples. Actual file locations depend on the project's repository structure.

---

## Functionality scenarios

When the source is a Functionality (`FUNC-<nnn>`) rather than a User Story, apply the same workflow but with these differences:

| Aspect | User Story (E2E) | Functionality (system test) |
|---|---|---|
| AC ID format | `AC:US-<nnn>-<nn>` | `AC:FUNC-<nnn>-<nn>` |
| File location | `features/us/us-<nnn>-<kebab>.feature` | `features/functionalities/<feat-kebab>/func-<nnn>-<kebab>.feature` |
| File header | `# Source:` (optional), `# Business Value:`, `# Acceptance Criteria:` block + `@US_ID:US-<n>` tag | `# Source:` (optional), `# Rationale:` (optional), `# Acceptance Criteria:` block + `@FUNC_ID:FUNC-<nnn>` tag |
| Feature block | `Feature: <US title>` with As-a/I-can/so-that | `Feature: <Feature name> — <Functionality name>` (no narrative) |
| Scope | End-to-end, from user's perspective | One atomic behavior, input to output contract |
| Language | Business domain language | Business domain language — same rule; no code calls, no selector references |

**Functionality feature file example:**

```gherkin
# func-001-validate-password-strength.feature

# Source: https://github.com/<org>/<repo>/issues/<n>      ← optional

# Rationale:
#   - <why this atomic behavior exists>                    ← optional

# Acceptance Criteria:
#
#   AC:FUNC-001-01 (v1.0.0 - Active)
#     - Returns valid=true when the password satisfies all complexity rules.
#
#   AC:FUNC-001-02 (v1.0.0 - Active)
#     - Raises INVALID_PASSWORD when the password is shorter than 8 characters.

@FUNC_ID:FUNC-001
Feature: Login Page — Validate Password Strength

  # AC:FUNC-001-01 (v1.0.0 - Active) — returns valid=true when password satisfies all complexity rules
  @AC:FUNC-001-01
  Scenario: Password meets all complexity rules
    Given a password with at least 8 characters, one uppercase, one lowercase, and one number
    When password strength is validated
    Then the result is valid

  # AC:FUNC-001-02 (v1.0.0 - Active) — raises INVALID_PASSWORD when password is shorter than 8 characters
  @AC:FUNC-001-02
  Scenario: Password too short
    Given a password with 7 or fewer characters
    When password strength is validated
    Then the result is invalid with code INVALID_PASSWORD
```

Functionality scenarios are **not** unit tests written in Gherkin. Steps must still describe observable business-facing input/output — never internal method calls, DB queries, or selector names.

---

## Out-of-scope redirects

| Request | Correct skill |
|---|---|
| Standalone Gherkin without a User Story | `gherkin-scenario` |
| Writing step definition code | `gherkin-step` |
