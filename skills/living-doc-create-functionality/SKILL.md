---
name: living-doc-create-functionality
description: >
  Define an atomic, testable behavior (Functionality) with Acceptance Criteria for unit or
  integration tests: write Functionality-level ACs, choose func_type or test_type, record the
  Features it calls, flag reuse candidates, or review a Functionality.
  Triggers on: "create a functionality", "document an atomic behavior", "document a business
  rule", "functionality AC", "atomic acceptance criteria", "unit-testable behavior",
  "define component behavior", "link functionality to feature", "func_type",
  "which func_type", "component_state vs button_action", "behavior category", "test_type",
  "unit vs integration test", "review this functionality", "reuse candidate",
  "what ACs should I write for".
  NOT for: E2E User Stories (living-doc-create-user-story), system surfaces
  (living-doc-create-feature), BDD scenarios (living-doc-scenario-creator).
  Pairs with living-doc-create-feature and living-doc-scenario-creator; after creating,
  update the parent Feature's functionalities[] array.
license: Apache-2.0
---

# Living Doc — Create Functionality

> **Key concepts:** Feature, Functionality, User Story, AC — see [living-doc-glossary](../shared/references/living-doc-glossary.md) ([remote](https://github.com/AbsaOSS/agentic-toolkit/blob/master/skills/shared/references/living-doc-glossary.md)).
> **BDD schemas:** Functionality feature file template and func_type values — see [living-doc-bdd-schemas](../shared/references/living-doc-bdd-schemas.md) ([remote](https://github.com/AbsaOSS/agentic-toolkit/blob/master/skills/shared/references/living-doc-bdd-schemas.md)).

## Step 1 — Elicit the behavior

Before asking, **scan the conversation context** for a behavior phrase and parent Feature already stated by the user. If the behavior is already clear, do not re-ask for it.

Ask only for what is missing: *What is the atomic behavior to document?*

Express the behavior as a **verb phrase** — one atomic responsibility. The Functionality `name` is that phrase prefixed with the parent Feature's name: `<Feature name> - <verb phrase>`, joined by a plain hyphen (never an en or em dash). This is the canon form — see [living-doc-glossary — Functionality](../shared/references/living-doc-glossary.md#functionality-func) — and it is what appears in the feature-file title line and the issue title. The Feature ID itself still goes only in `parent_feature`.

```
✅  "Checkout Page - Validate cart contains at least one in-stock item"
✅  "Checkout Page - Apply gold member discount on qualifying orders"
✅  "Checkout Page - Deduct voucher discount before tax is calculated"

❌  "Validate cart contains at least one in-stock item"   (no Feature name prefix)
❌  "Checkout Page — Validate cart contents"              (em dash — use a plain hyphen)
❌  "Checkout Page - Handle checkout"                     (too broad — split into multiple Functionalities)
❌  "The payment page"                                    (that is a Feature, not a Functionality)
```

Until the parent Feature is known (Step 2), work with the verb phrase alone; add the prefix once the Feature's name is confirmed from the catalog.

## Step 2 — Identify the parent Feature

Ask: *Which Feature (system surface) owns this behavior?* only if it is not already obvious from the prompt.

A Functionality belongs to exactly one parent Feature, recorded in `parent_feature` — the toolkit JSON name for the canon's `# parent:` header key (see [living-doc-bdd-schemas](../shared/references/living-doc-bdd-schemas.md#3-functionality-in-a-gherkin-feature-file)). If the user clearly names the surface or domain (for example checkout, basket, login, pricing), infer a provisional `parent_feature` by asking for the catalog to look up the numeric ID. If the catalog is not available, note that the Feature must be created formally via `living-doc-create-feature` first (which will assign a numeric ID). Do **not** invent a slug-based Feature ID; all Feature IDs are numeric and catalog-assigned.

### Features this behaviour calls

Ask: *Does this behaviour call another documented Feature — an API endpoint or an annotated event contract?*

Record each one as a `FEAT-<nnn>` id in `feature_dependencies`. The field is authored **here**, on the Functionality that makes the call, and derived upward to the parent Feature — never written on the Feature itself. Which targets are allowed is defined once, in [living-doc-glossary — Functionality](../shared/references/living-doc-glossary.md#functionality-func); read the rules there rather than a copy here.

A system the behaviour calls that is **not** a documented Feature is not a target. It stays a free-form `external_dependencies` name on the parent Feature, which `living-doc-create-feature` owns. If nothing is called, emit `"feature_dependencies": []`.

## Step 3 — Elicit Functionality-level Acceptance Criteria

Functionality ACs describe atomic inputs to outputs. They are:
- **Atomic**: one input condition, one output or side effect per AC
- **Fast-testable**: designed for verification by unit or integration test
- **Unambiguous**: exact error codes, exact output values, exact rule outcomes where relevant

Write **3-7 ACs** for one coherent behavior. If a Functionality needs around **12 ACs**, treat that as a strong sign it is not atomic and split it into 2-3 focused Functionalities.

**Completeness checklist — adapt each prompt to the domain before finalizing:**

| Category | Prompt |
|---|---|
| Empty / null input | "What happens when the input is null, empty, or missing entirely?" |
| Invalid members / states | "What happens when every item is invalid, only some items are valid, an item has an invalid state such as zero quantity or out-of-stock, or the actor is not eligible (for example a non-gold member)?" |
| Boundary values | "What happens below the threshold, exactly on the threshold, and above it?" |
| Rule interactions | "Does this combine with other rules, discounts, promo codes, or validations? If so, what is the stacking or precedence rule?" |
| External dependency | "Does proving this behavior require a real DB / service read or write, or can it be verified as a pure function?" |
| All error codes | "Are all error codes documented explicitly, not just 'error' or 'invalid'?" |

Warn if only happy-path ACs are present.

### Choosing `func_type`

`func_type` is **required** on every Functionality. It is not a label applied after the fact: it
decides which PageObject locator the behaviour anchors to, and it drives the one-FUNC-one-cause
scoping rules — so getting it wrong changes how the behaviour must be split, not just how it reads.

The seven allowed values, what each documents, and its PageObject anchor are tabulated once, in
[living-doc-bdd-schemas — `func_type` values](../shared/references/living-doc-bdd-schemas.md#3-functionality-in-a-gherkin-feature-file);
the scoping rules follow it in the same section. Read the table there — it is not repeated here.

To pick a value, ask **what causes the behaviour**:

| The behaviour is caused by… | Value |
|---|---|
| the page simply loading, or a data-bound component rendering a data state | `component_state` |
| an interaction inside one self-contained component, with no discrete control and no system side effect | `component_action` |
| a specific discrete control being triggered (including form submit) | `button_action` |
| a rule enforced on one field's value | `field_validation` |
| a value derived from inputs and displayed without a submission | `calculation` |
| a runtime condition (role, prior action, data presence, config) gating an element | `visibility` |
| a routing decision with its own precondition or business rule | `navigation_rule` |

Two tie-breaks worth stating explicitly, because they are the usual mistakes:

- A derived value that only appears **after a submit** is an AC on the `button_action` FUNC, not a
  `calculation`.
- A redirect that is always the result of a button press is an AC on that `button_action` FUNC, not
  a separate `navigation_rule`.

### Choosing `test_type`

- Use **`unit`** when the behavior can be verified in isolation as a pure calculation, validation rule, or deterministic transformation.
- Use **`integration`** when correctness depends on a real database, uniqueness check, external service, persistence side effect, or cross-component interaction.
- If the behavior could be refactored into a pure function that accepts all required inputs directly, prefer that design and then use **`unit`**. Example: if duplicate-email validation accepts the current email plus a provided list/set of existing emails, test it as a unit rule; use **`integration`** only when the behavior itself performs the real database lookup.
- Cart/inventory validation is usually **`unit`** when the Functionality evaluates the cart snapshot it has already been given (for example item quantities and in-stock flags on the cart lines). Do not upgrade this to integration unless the behavior itself performs the live stock lookup.

### When reviewing an existing Functionality

Classify findings as **Blocker**, **Important**, or **Nit**.
- **Blocker**: not atomic, vague ACs, or non-testable wording such as "works correctly".
- **Important**: missing error codes, missing boundary conditions, or missing interaction rules.
- **Nit**: wording cleanup that does not change the contract.

For Blocker or Important findings, propose a split into smaller Functionalities where needed and show rewritten AC examples with exact `When` / `Then` outcomes and explicit error codes.

**System-level constraints** (optional, but ask if relevant):
When the Functionality has preconditions or explicit exclusions that apply across all ACs, document them at the FUNC level in the feature file header:
- **`preconditions:`** — System state required before ANY AC in this FUNC can be tested (e.g. "User is logged in", "Feature flag enabled"). All ACs inherit these; individual ACs can extend them if needed.
- **`not_in_scope:`** — Explicit exclusions or boundaries at the FUNC level (e.g. "Does not cover multi-factor authentication", "Does not apply to bulk orders"). All ACs inherit these; individual ACs can extend them if needed.

Ask: *Are there any system-level preconditions (required states before any scenario can run) or explicit exclusions (things this FUNC deliberately does not cover)?* If yes, note them for the feature file header — they will be incorporated when `living-doc-scenario-creator` generates the Gherkin.

## Step 4 — Flag reuse candidates

Before creating, check whether an identical behavior already exists under any Feature. **Compare ACs, not names** — the same verb phrase in a different Feature context often produces a legitimately different contract.

> **Scope note:** This step is a lightweight in-session check during creation. For a full cross-catalog duplicate and coverage audit across all existing Functionalities, use `living-doc-gap-finder` instead.

If the ACs are identical or near-identical across Features or User Stories, prefer **one shared Functionality**. Link every consuming User Story in the `user_stories` array instead of duplicating the ACs.

> "This is a reuse candidate. If the contract is truly identical, keep one Functionality and link both User Stories to it. Duplicating the same AC in multiple places creates maintenance burden and raises the risk of divergence when the behavior changes."

If contextually distinct despite similar names, create a new Functionality and note the related one for future reviewers.

## Step 5 — Output canonical Functionality entity

When the user asks to **create**, **document**, or **draft** a Functionality entity, first show a brief **completeness checklist** line (or 2-4 short questions) covering the relevant missing edge cases, then output **one fenced `json` code block** and no extra prose inside the block. Do not stop at advice about what the entity should contain — emit the actual JSON artifact.

Never answer a create/document request with only instructions such as "Create a Functionality entity..." or "Then output the canonical JSON". The response itself must contain the canonical JSON.

> **ID assignment:** before assigning a `FUNC-nnn` ID, run
> `python scripts/next_id.py --type FUNC --catalog catalog.json`
> to get the next available ID and avoid collisions.

Use this canonical shape:

```json
{
  "type": "Functionality",
  "id": "FUNC-<nnn>",
  "name": "<Feature name> - <verb phrase>",
  "description": "<one sentence in business language>",
  "parent_feature": "FEAT-<nnn>",
  "func_type": "<component_state | component_action | button_action | field_validation | calculation | visibility | navigation_rule>",
  "feature_dependencies": ["FEAT-<nnn>"],
  "user_stories": ["US-<id>"],
  "acceptance_criteria": [
    {"id": "AC:FUNC-<nnn>-01", "description": "When <condition>, <observable outcome>"},
    {"id": "AC:FUNC-<nnn>-02", "description": "When <condition>, validation returns INVALID with code <ERROR_CODE>"},
    {"id": "AC:FUNC-<nnn>-03", "description": "When <condition>, <observable outcome>"}
  ],
  "test_coverage": [
    {"ac": "AC:FUNC-<nnn>-01", "test_type": "unit", "justification": "Pure validation rule"},
    {"ac": "AC:FUNC-<nnn>-02", "test_type": "unit", "justification": "Pure validation rule"},
    {"ac": "AC:FUNC-<nnn>-03", "test_type": "unit", "justification": "Pure validation rule"}
  ],
  "status": "planned"
}
```

Rules:
- If `catalog.json` is available, run `python scripts/next_id.py --type FUNC --catalog catalog.json` and use the returned ID.
- If the prompt states an existing catalog range (for example `FUNC-001` through `FUNC-007`), reflect the allocator call in the answer as `Ran: python scripts/next_id.py --type FUNC --catalog catalog.json -> FUNC-008` and use that returned numeric ID in the JSON.
- If the prompt explicitly says the catalog is missing / `next_id.py` cannot run for a real save operation, use the stable placeholder `FUNC-PENDING` until an allocator can assign the final ID.
- Otherwise, for starter drafts and normal create/document requests where no catalog state is given, use the readable draft form `FUNC-<kebab-name>`.
- `name` is `<Feature name> - <verb phrase>`: the parent Feature's name, a plain hyphen, then the atomic verb phrase.
- Each acceptance criterion is an object with `id` and `description`. The `id` is
  `AC:<Functionality id>-<nn>`, numbered from `01` in order — the same ID the AC carries in the
  feature-file header or issue body (see [living-doc-glossary — Acceptance Criterion](../shared/references/living-doc-glossary.md#acceptance-criterion-ac)).
  Never emit an AC as a bare string: it has no ID, so nothing can link a test or a scenario to it.
  When a placeholder ID (`FUNC-<kebab-name>`, `FUNC-PENDING`) is replaced, renumber the AC IDs and
  the `test_coverage` references with it.
- `description` and `acceptance_criteria` must stay in plain business language with **no implementation details**.
- Every acceptance criterion must state an exact outcome; error cases must include the explicit error code.
- `func_type` is **required** and must be one of the seven allowed values — pick it from what causes
  the behaviour, per [Choosing `func_type`](#choosing-func_type). Never omit it and never invent a
  value: `validate_entity.py` rejects both, and without it the entity cannot be authored into a
  Functionality feature-file header.
- `feature_dependencies` lists the documented Features this behaviour calls, per
  [Features this behaviour calls](#features-this-behaviour-calls) — `[]` when it calls none. Never
  put a free-form system name in it.
- `test_coverage` must cover every AC — one entry per AC `id`, referenced by that exact ID — and record `unit` or `integration` consistently with Step 3.

> **`test_coverage` is toolkit-local.** It is a test-planning structure used by this toolkit's
> skills to reason about how each AC will be verified; it is **never authored into documentation** —
> neither `func-*.feature` headers nor issue bodies carry it, and the living-doc pipeline neither
> reads nor emits it. `test_type` lives only inside it, for the same reason (see
> [Choosing `test_type`](#choosing-test_type)).

Starter example for a normal draft:
```json
{
  "type": "Functionality",
  "id": "FUNC-001",
  "name": "Checkout Page - Apply gold member discount on qualifying orders",
  "description": "Applies the gold-member discount when the order satisfies the minimum qualifying threshold.",
  "parent_feature": "FEAT-001",
  "func_type": "calculation",
  "user_stories": ["US-001"],
  "acceptance_criteria": [
    {"id": "AC:FUNC-001-01", "description": "When the customer is a gold member and the order total is greater than £50, the discount applied is 20% of the subtotal."},
    {"id": "AC:FUNC-001-02", "description": "When the order total is exactly £50, no gold-member discount is applied."},
    {"id": "AC:FUNC-001-03", "description": "When the customer is not a gold member, no gold-member discount is applied."}
  ],
  "test_coverage": [
    {"ac": "AC:FUNC-001-01", "test_type": "unit", "justification": "Pure pricing rule"},
    {"ac": "AC:FUNC-001-02", "test_type": "unit", "justification": "Boundary threshold rule"},
    {"ac": "AC:FUNC-001-03", "test_type": "unit", "justification": "Eligibility rule"}
  ],
  "status": "planned"
}
```

Fallback example when the prompt explicitly says the catalog is missing:
```json
{
  "type": "Functionality",
  "id": "FUNC-PENDING",
  "name": "Checkout Page - Validate discount code expiry",
  "description": "Rejects expired discount codes before they are applied to the order.",
  "parent_feature": "FEAT-001",
  "func_type": "field_validation",
  "user_stories": ["US-001"],
  "acceptance_criteria": [
    {"id": "AC:FUNC-PENDING-01", "description": "When the discount code is expired, validation returns INVALID with code DISCOUNT_EXPIRED."}
  ],
  "test_coverage": [
    {"ac": "AC:FUNC-PENDING-01", "test_type": "unit", "justification": "Pure date comparison rule"}
  ],
  "status": "planned"
}
```

> **Promoting `planned` → `active`:** A Functionality is created with `status: "planned"`. Once the tests backing all its ACs are written and passing, use `living-doc-update` to change the status to `active`. Do not mark a Functionality `active` until its test coverage is in place.

> **Parent Feature sync:** After saving this entity, load `living-doc-update` and append this `FUNC-<id>` to the parent Feature's `"functionalities"` array. An unlinked Functionality will be flagged as `ORPHAN_FUNCTIONALITY` by `living-doc-gap-finder`.

Common create requests that should produce JSON immediately (each names the `func_type` that fits
its behaviour — never carry one value across from the previous example):
- cart validation rule ("Validate cart contains at least one in-stock item") → `func_type: "field_validation"` (a rule enforced on the cart's contents); explicitly ask: *What happens when the cart is empty? when all items are out of stock? when only some items are in stock? when an item has zero quantity?* Then emit JSON with those cases covered, including an explicit zero-quantity error such as `INVALID_QUANTITY`; keep all ACs as `unit` when validating an already-provided cart snapshot
- discount rule ("Apply 20% discount to gold member orders over £50") → `func_type: "calculation"` (a value derived from the order); look up the pricing (or named) Feature's numeric ID in the catalog for `parent_feature`, ask about non-gold members, exactly £50, under £50, and promo-code stacking, then emit the full JSON **including a stacking/precedence AC in the `acceptance_criteria` array**
- voucher calculation rule ("Deduct voucher discount before tax is calculated") → `func_type: "calculation"` (an ordering rule on a derived total); ask which Feature (checkout/pricing) owns this, or ask for the catalog to look up the Feature ID, then emit the full JSON
- checkout stock rule ("Reject order when all items are out of stock") → `func_type: "button_action"` if the rejection is observable only after the order is submitted, `field_validation` if the cart itself blocks first; ask which Feature (checkout) owns this, or ask for the catalog to look up the Feature ID, then emit the full JSON

For the gold-member discount pattern, first write a short `Completeness checklist:` line that explicitly mentions non-gold members, exactly £50, under £50, and promo-code stacking, then end with the full JSON artifact, not a sentence saying to output JSON later.

Gold-member discount starter draft example:
```json
{
  "type": "Functionality",
  "id": "FUNC-003",
  "name": "Checkout Page - Apply gold member discount on qualifying orders",
  "description": "Applies the gold-member discount when an order meets the qualifying threshold.",
  "parent_feature": "FEAT-001",
  "func_type": "calculation",
  "user_stories": ["US-001"],
  "acceptance_criteria": [
    {"id": "AC:FUNC-003-01", "description": "When the customer is a gold member and the order total is greater than £50, a 20% discount is applied to the order subtotal."},
    {"id": "AC:FUNC-003-02", "description": "When the customer is a gold member and the order total is exactly £50, the threshold outcome is applied exactly as specified by the business rule."},
    {"id": "AC:FUNC-003-03", "description": "When the customer is a gold member and the order total is below £50, no gold-member discount is applied."},
    {"id": "AC:FUNC-003-04", "description": "When the customer is not a gold member, no gold-member discount is applied regardless of order total."},
    {"id": "AC:FUNC-003-05", "description": "When a promo code is combined with the gold-member discount, the stacking or precedence rule is applied exactly as specified."}
  ],
  "test_coverage": [
    {"ac": "AC:FUNC-003-01", "test_type": "unit", "justification": "Pure pricing rule"},
    {"ac": "AC:FUNC-003-02", "test_type": "unit", "justification": "Boundary threshold rule"},
    {"ac": "AC:FUNC-003-03", "test_type": "unit", "justification": "Below-threshold rule"},
    {"ac": "AC:FUNC-003-04", "test_type": "unit", "justification": "Eligibility rule"},
    {"ac": "AC:FUNC-003-05", "test_type": "unit", "justification": "Discount interaction rule"}
  ],
  "status": "planned"
}
```

## Script — `validate_entity.py`

After outputting the entity, validate it against the canonical schema before saving to the catalog. Do not save the entity if the script exits with code 1.

```bash
# Validate the output (run from the toolkit root)
python skills/living-doc-update/scripts/validate_entity.py entity.json

# With referential integrity checks against the full catalog
python skills/living-doc-update/scripts/validate_entity.py entity.json --catalog catalog.json

# Enforce the project's AC state vocabulary (reads `ac_states` from the Project Profile)
python skills/living-doc-update/scripts/validate_entity.py entity.json --profile .copilot/bdd/.project-profile.yaml
```

Exits 0 if valid (warnings are non-blocking). Exits 1 if any required field is missing, the ID format is wrong, `parent_feature` does not match `FEAT-*`, `func_type` is outside the seven canonical values, or the status value is invalid. With `--catalog` it also rejects a `feature_dependencies` target that is not an `API` Feature or is the Functionality's own Feature, and warns on one that is missing from the catalog or deprecated.

## Distinguishing Functionality ACs from User Story ACs

| Dimension | User Story AC | Functionality AC |
|---|---|---|
| Perspective | End user observing outcomes | Developer / component behaviour |
| Scope | Full E2E flow | Single function or method |
| Example | "Order is confirmed and email is sent" | "Returns the discounted total when a valid membership tier is applied" |

If an AC written here is outcome-based from a user's perspective, it belongs in the User Story —
redirect to `living-doc-create-user-story`.

## Anti-patterns to flag

| Anti-pattern | Warning |
|---|---|
| Functionality name is a noun (e.g. "Password Validation") | The behavior part of the name must be a verb phrase expressing the atomic behavior — e.g. "Login Page - Validate Password Strength". |
| Functionality name has no Feature prefix (e.g. "Validate Password Strength") | Canon names a Functionality `<Feature name> - <verb phrase>` — prefix the parent Feature's name with a plain hyphen: "Login Page - Validate Password Strength". `validate_entity.py` warns on a name without the separator. |
| Functionality name is broad (e.g. "Handle checkout") | That is not atomic. Split it into smaller behaviors such as validation, pricing, payment authorization, or order submission. |
| Functionality AC describes a full user journey (e.g. "User logs in and sees their dashboard") | That is a User Story AC — redirect to **living-doc-create-user-story**. Functionality ACs describe a single behavior's input to output or side effect. |
| Functionality has only happy-path ACs | Edge cases (null input, boundary values, partial validity, error codes) are missing. Run through the completeness checklist in Step 3 before confirming. |
| AC says "returns error" without specifying the type or code | Specify the exact error code. Without a named code, the AC is not testable. |
| AC uses "should", "may", or "might" | Non-binary wording makes the AC untestable. Use `must` for rules the system enforces, `returns` for calculations, `rejects`/`accepts` for validations. |
| AC wording is vague (e.g. "works correctly", "handles it appropriately") | Rewrite with exact `When` / `Then` behavior and explicit outputs or error codes. |
| Functionality has more than 7 ACs | Review for non-atomic scope. Around 12 ACs is almost certainly too broad and should be split into 2-3 Functionalities. |
| Two Functionalities have identical or near-identical ACs | Duplicate ACs create a maintenance burden. Consolidate into one shared Functionality and link all related `user_stories`. |
| Functionality has no parent Feature | A Functionality without a parent Feature is untraceable — create or identify the parent Feature first. It will be flagged as `ORPHAN_FUNCTIONALITY`, missed in impact analyses, and unreachable via the living-doc hierarchy until linked. |

## Out-of-scope routing

| Request type | Correct skill |
|---|---|
| "Create a User Story" | `living-doc-create-user-story` — this skill documents atomic behaviors, not end-to-end User Stories. Note: a system-actor narrative ("As a system...") with no human beneficiary in `so that` is a strong signal to use this skill instead |
| "Create a Feature entity" | `living-doc-create-feature` — a Feature is a system surface, not an atomic behavior |
| "Write unit tests for this Functionality" | No skill in this toolkit covers unit test authoring — use your project's test framework directly. This skill defines the _what_ (ACs); writing the test code is outside scope. |
| "Generate BDD scenarios for this Functionality" | `living-doc-scenario-creator` |
