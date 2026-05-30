---
name: living-doc-scenario-creator
description: >
  Generate the living-doc feature file header block (@US_ID:/@FUNC_ID: tag, Feature narrative,
  # Acceptance Criteria: block) and scenario skeletons (one @AC:-tagged Scenario: title with
  ... placeholder per ACTIVE AC). Produces an AC coverage report. Step bodies (Given/When/Then)
  are authored by bdd-scenario-gen.
  Use when bootstrapping a feature file for a US or Functionality, auditing AC coverage, or
  tagging partial coverage with aspect notation.
  Triggers on: "feature file header for user story", "living-doc feature file",
  "bootstrap feature file for US", "US feature file structure", "cover AC with scenarios",
  "scenario coverage for US", "map AC to scenarios", "AC coverage for US",
  "partial AC coverage", "scenario creator", "generate feature file for US",
  "bootstrap living-doc scenarios".
  Does NOT trigger for: writing scenario step bodies (use bdd-scenario-gen), standalone
  Gherkin (use bdd-scenario-gen), step definitions (use gherkin-step),
  doc gaps (use living-doc-gap-finder).
  Pairs with living-doc-create-user-story, bdd-scenario-gen, and living-doc-pageobject-scan.
license: Apache-2.0
compatibility: GitHub Copilot
---

# Living Doc — Scenario Creator

> **Glossary:** User Story, AC, PageObject, step definitions — see [living-doc-glossary](../references/living-doc-glossary.md) ([remote](https://github.com/AbsaOSS/agentic-toolkit/blob/master/skills/references/living-doc-glossary.md)).
> **BDD schemas:** US and Functionality feature file templates — see [living-doc-bdd-schemas](../references/living-doc-bdd-schemas.md) ([remote](https://github.com/AbsaOSS/agentic-toolkit/blob/master/skills/references/living-doc-bdd-schemas.md)).

## AC state vocabulary

**AC states used in this skill:** `PLANNED` · `IN_REVIEW` · `ACTIVE` · `DEPRECATED`

Only `ACTIVE` ACs drive scenario generation. `PLANNED` and `DEPRECATED` ACs are skipped.

**AC traceability format** — for the authoritative `# AC:` and `@AC:` annotation format, load `bdd-scenario-gen`.

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
- Which ACs are eligible for generation (`ACTIVE`)
- ACs are atomic — each has one input condition and one observable outcome

Treat requests such as "write feature tests for US-007" as requests to generate BDD scenarios plus a coverage table for that User Story.

If no ACs are `ACTIVE`, do **not** generate empty or stub scenarios. Instead,
output a coverage report that lists every AC with its state-specific skip reason (`PLANNED`:
`skipped — not yet active`, `DEPRECATED`: `skipped — deprecated AC`) and advise the user to
re-run the scenario creator when an AC becomes `ACTIVE`.

### Step 2 — Generate scenario skeletons

For each `ACTIVE` AC, generate the `# AC:` comment, `@AC:` tag, and `Scenario:` title with `...` as the step placeholder. Step bodies (Given/When/Then) are authored by `bdd-scenario-gen`.

Select the title by AC type:
- `happy_path`: `Scenario: <positive outcome>`
- `error`: `Scenario: <US title> — <error condition>` (prefer the crisp business-facing failure title from the AC if available)
- `alternative`: `Scenario: <US title> — <alternative path>`

```gherkin
# AC:US-1-01 (v1.0.0 - Active) — customer places an order with a saved payment method
@AC:US-1-01
Scenario: Customer successfully places an order
  ...

# AC:US-1-02 (v1.0.0 - Active) — order is rejected when the payment card is declined
@AC:US-1-02
Scenario: Order rejected when payment card is declined
  ...
```

### Step 3 — Hand off step bodies to bdd-scenario-gen

The skeletons from Step 2 use `...` placeholders. To produce full Given/When/Then implementations, pass the generated feature file to `bdd-scenario-gen`. For step definition code, load `gherkin-step`.

Do not author step bodies in this skill.

### Step 4 — Validate AC coverage

Every `ACTIVE` AC must map to at least one scenario.
The coverage report must list **every** AC on the User Story, including skipped ones.
Use these skip reasons verbatim so the output is predictable and auditable:
- `PLANNED`: `skipped — not yet active`
- `DEPRECATED`: `skipped — deprecated AC`

Run `scripts/coverage_report.py <living_doc_dir> <features_dir>` for a full coverage report.

```
AC COVERAGE REPORT — US-001
  AC:US-001-01 (ACTIVE): ✅ covered by "Customer successfully places an order"
  AC:US-001-02 (ACTIVE): ✅ covered by "Order rejected when payment card is declined"
  AC:US-001-03 (ACTIVE): ❌ NOT COVERED — added to gap list
  AC:US-001-04 (PLANNED): ⏭  skipped — not yet active
  AC:US-001-05 (DEPRECATED): ⏭  skipped — deprecated AC
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

**Coverage table** — ACs with coverage status (use `scripts/coverage_report.py`). Append it immediately after the `.feature` code block in the response.

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
| Standalone Gherkin without a User Story | `bdd-scenario-gen` |
| Writing step definition code | `gherkin-step` |

**Ambiguous request — "create scenarios for US-007":** If the user does not specify whether they want skeleton structure or full step bodies, ask:
> "Do you want the living-doc feature file header and skeleton scenario titles (continue here in `living-doc-scenario-creator`), or full Given/When/Then scenario bodies (use `bdd-scenario-gen`)?"
This skill produces the reusable structural skeleton (header block + AC-tagged scenario titles); `bdd-scenario-gen` fills in the step bodies.
