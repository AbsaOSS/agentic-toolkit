---
name: living-doc-create-functionality
description: >
  Define an atomic, testable behavior (Functionality) with Functionality-level Acceptance Criteria
  designed to be validated by fast unit or integration tests. Activate when documenting an atomic
  behavior, component function, or business rule; writing Functionality-level AC; creating the
  granular test anchor for a Feature; choosing test_type (unit vs integration); identifying reuse
  candidates across User Stories; linking a Functionality to its parent Feature; or reviewing a
  Functionality for completeness.
  Triggers on: "create a functionality", "document an atomic behavior", "functionality AC",
  "unit-testable behavior", "define component behavior", "atomic acceptance criteria",
  "document a business rule", "create a functionality entity", "functionality acceptance criteria",
  "test_type", "unit vs integration test", "choose test type", "link functionality to feature".
  Does NOT trigger for: end-to-end User Stories (use living-doc-create-user-story), system
  surface documentation (use living-doc-create-feature), generating BDD scenarios for a
  Functionality (use bdd-scenario-gen).
license: Apache-2.0
compatibility: GitHub Copilot
---

# Living Doc — Create Functionality

> **Key concepts:** Feature, Functionality, User Story, AC — see [living-doc-glossary](../references/living-doc-glossary.md) ([remote](https://github.com/AbsaOSS/agentic-toolkit/blob/master/skills/references/living-doc-glossary.md)).
> **BDD schemas:** Functionality feature file template and func_type values — see [living-doc-bdd-schemas](../references/living-doc-bdd-schemas.md) ([remote](https://github.com/AbsaOSS/agentic-toolkit/blob/master/skills/references/living-doc-bdd-schemas.md)).

## Step 1 — Elicit the behavior

Before asking, **scan the conversation context** for a behavior phrase and parent Feature already stated by the user. If the behavior is already clear, do not re-ask for it.

Ask only for what is missing: *What is the atomic behavior to document?*

Express the Functionality `name` as a **verb phrase only** — one atomic responsibility, with no Feature prefix. Keep the owning Feature separate in `feature_id`.

```
✅  "Validate cart contains at least one in-stock item"
✅  "Apply gold member discount on qualifying orders"
✅  "Deduct voucher discount before tax is calculated"

❌  "Handle checkout"              (too broad — split into multiple Functionalities)
❌  "The payment page"             (that is a Feature, not a Functionality)
```

## Step 2 — Identify the parent Feature

Ask: *Which Feature (system surface) owns this behavior?* only if it is not already obvious from the prompt.

A Functionality must belong to at least one Feature. If the user clearly names the surface or domain (for example checkout, basket, login, pricing), infer a provisional `feature_id` such as `FEAT-checkout` and proceed. If the Feature truly does not yet exist, suggest creating it with `living-doc-create-feature` first.

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

### Choosing `test_type`

- Use **`unit`** when the behavior can be verified in isolation as a pure calculation, validation rule, or deterministic transformation.
- Use **`integration`** when correctness depends on a real database, uniqueness check, external service, persistence side effect, or cross-component interaction.
- If the behavior could be refactored into a pure function that accepts all required inputs directly, prefer that design and then use **`unit`**.

### When reviewing an existing Functionality

Classify findings as **Blocker**, **Important**, or **Nit**.
- **Blocker**: not atomic, vague ACs, or non-testable wording such as "works correctly".
- **Important**: missing error codes, missing boundary conditions, or missing interaction rules.
- **Nit**: wording cleanup that does not change the contract.

For Blocker or Important findings, propose a split into smaller Functionalities where needed and show rewritten AC examples with exact `When` / `Then` outcomes and explicit error codes.

## Step 4 — Flag reuse candidates

Before creating, check whether an identical behavior already exists under any Feature. **Compare ACs, not names** — the same verb phrase in a different Feature context often produces a legitimately different contract.

If the ACs are identical or near-identical across Features or User Stories, prefer **one shared Functionality**. Link every consuming User Story in the `user_stories` array instead of duplicating the ACs.

> "This is a reuse candidate. If the contract is truly identical, keep one Functionality and link both User Stories to it. Duplicating the same AC in multiple places creates maintenance burden and raises the risk of divergence when the behavior changes."

If contextually distinct despite similar names, create a new Functionality and note the related one for future reviewers.

## Step 5 — Output canonical Functionality entity

When creating a Functionality, output **one fenced `json` code block** and no extra prose inside the block.

> **ID assignment:** before assigning a `FUNC-nnn` ID, run
> `python scripts/next_id.py --type FUNC --catalog catalog.json`
> to get the next available ID and avoid collisions.

Use this canonical shape:

```json
{
  "type": "Functionality",
  "id": "FUNC-<kebab-name>",
  "name": "<verb phrase>",
  "description": "<one sentence in business language>",
  "feature_id": "FEAT-<kebab-or-known-id>",
  "user_stories": ["US-<id>"],
  "acceptance_criteria": [
    "When <condition>, <observable outcome>",
    "When <condition>, validation returns INVALID with code <ERROR_CODE>",
    "When <condition>, <observable outcome>"
  ],
  "test_coverage": [
    {"ac": "AC-1", "test_type": "unit", "justification": "Pure validation rule"},
    {"ac": "AC-2", "test_type": "unit", "justification": "Pure validation rule"}
  ],
  "status": "planned"
}
```

Rules:
- `id` uses the stable draft convention `FUNC-<kebab-name>` when no catalog allocator is available in-session.
- `name` stays a verb phrase only.
- `description` and `acceptance_criteria` must stay in plain business language with **no implementation details**.
- Every acceptance criterion must state an exact outcome; error cases must include the explicit error code.
- `test_coverage` must cover every AC and record `unit` or `integration` consistently with Step 3.

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
| Functionality name is a noun (e.g. "Password Validation") | Names must be verb phrases expressing the atomic behavior — e.g. "Validate Password Strength". |
| Functionality name is broad (e.g. "Handle checkout") | That is not atomic. Split it into smaller behaviors such as validation, pricing, payment authorization, or order submission. |
| Functionality AC describes a full user journey (e.g. "User logs in and sees their dashboard") | That is a User Story AC — redirect to **living-doc-create-user-story**. Functionality ACs describe a single behavior's input to output or side effect. |
| Functionality has only happy-path ACs | Edge cases (null input, boundary values, partial validity, error codes) are missing. Run through the completeness checklist in Step 3 before confirming. |
| AC says "returns error" without specifying the type or code | Specify the exact error code. Without a named code, the AC is not testable. |
| AC wording is vague (e.g. "works correctly", "handles it appropriately") | Rewrite with exact `When` / `Then` behavior and explicit outputs or error codes. |
| Functionality has more than 7 ACs | Review for non-atomic scope. Around 12 ACs is almost certainly too broad and should be split into 2-3 Functionalities. |
| Two Functionalities have identical or near-identical ACs | Duplicate ACs create a maintenance burden. Consolidate into one shared Functionality and link all related `user_stories`. |
| Functionality has no parent Feature | A Functionality without a parent Feature is untraceable — create or identify the parent Feature first. |

## Out-of-scope redirects

| Request type | Correct skill |
|---|---|
| "Create a User Story" | `living-doc-create-user-story` — this skill documents atomic behaviors, not end-to-end User Stories |
| "Create a Feature entity" | `living-doc-create-feature` — a Feature is a system surface, not an atomic behavior |
| "Write unit tests for this Functionality" | No skill in this toolkit covers unit test authoring — use your project's test framework directly. This skill defines the _what_ (ACs); writing the test code is outside scope. |
| "Generate BDD scenarios for this Functionality" | `bdd-scenario-gen` (step bodies) via `living-doc-scenario-creator` (feature file skeleton) |
