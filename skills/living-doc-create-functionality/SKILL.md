---
name: living-doc-create-functionality
description: >
  Define an atomic, testable behavior (Functionality) with Functionality-level Acceptance Criteria
  designed to be validated by fast unit or integration tests. Activate when documenting an atomic
  behavior, component function, or business rule; writing Functionality-level AC; creating the
  granular test anchor for a Feature; or identifying reuse candidates across User Stories.
  Triggers on: "create a functionality", "document an atomic behavior", "functionality AC",
  "unit-testable behavior", "define component behavior", "atomic acceptance criteria",
  "document a business rule", "create a functionality entity", "functionality acceptance criteria".
  Does NOT trigger for: end-to-end User Stories (use living-doc-create-user-story), system
  surface documentation (use living-doc-create-feature), BDD scenario generation
  (use living-doc-scenario-creator).
  Pairs with living-doc-create-feature and living-doc-scenario-creator.
license: Apache-2.0
compatibility: GitHub Copilot
---

# Living Doc — Create Functionality

> **Key concepts:** Feature, Functionality, User Story, AC — see [living-doc-glossary](../references/living-doc-glossary.md) ([remote](https://github.com/AbsaOSS/agentic-toolkit/blob/master/skills/references/living-doc-glossary.md)).

## Step 1 — Elicit the behavior

Before asking, **scan the conversation context** for a behavior phrase and parent Feature already stated by the user. If both are present, form the Functionality name directly and ask for confirmation rather than re-asking the questions.

Ask only for what is missing: *What is the atomic behavior to document?*

Express as a **verb phrase** — a single, focused responsibility. The Functionality name follows
the pattern: `<parent Feature name> – <behavior phrase>` (e.g. "Login Page – Validate Password Strength").

```
✅  "Calculate discount for a cart item given the customer's membership tier"
✅  "Validate that an order quantity is within the allowed range"
✅  "Raise a CartEmptyError when checkout is attempted on an empty cart"

❌  "Handle the checkout process"   (too broad — split into multiple Functionalities)
❌  "The payment page"              (that is a Feature, not a Functionality)
```

## Step 2 — Identify the parent Feature

Ask: *Which Feature (system surface) owns this behavior?*

A Functionality must belong to at least one Feature. If the Feature does not yet exist, suggest
creating it with `living-doc-create-feature` first.



## Step 3 — Elicit Functionality-level Acceptance Criteria

Functionality ACs describe atomic inputs → outputs. They are:
- **Atomic**: one input condition, one output or side effect per AC
- **Fast-testable**: designed for verification by unit or integration test. E2E tests *can* exercise the same behavior, but they are slow and expensive — they belong in a separate system-test tier, not the fast or regression suite.
- **Unambiguous**: exact error codes, exact output values where relevant

Use the canonical AC format (see [living-doc-glossary](../references/living-doc-glossary.md) ([remote](https://github.com/AbsaOSS/agentic-toolkit/blob/master/skills/references/living-doc-glossary.md))):

```
AC:FUNC-<nnn>-<nn> (v<version> – Planned)
   – <atomic description: one input condition → one observable output>
   – <Placeholder>: value1, value2, ...   ← only when two or more values vary
   – Rationale: <business context or constraint>  ← optional
```

**Completeness checklist — prompt for each:**

| Category | Prompt |
|---|---|
| Empty / null input | "What happens when the input is null or empty?" |
| Boundary values | "What happens at the minimum and maximum allowed values?" |
| Invalid type / format | "What error is raised for invalid format, and what is the error code?" |
| Concurrent access | "Is there a race condition? Should this behavior be idempotent?" |
| All error codes | "Are all error codes documented (not just the generic 'error occurred')?" |

Warn if only happy-path ACs are present — same as for User Stories.

## Step 4 — Flag reuse candidates

Before creating, check whether an identical behavior already exists under any Feature. **Compare ACs, not names** — the same verb phrase in a different Feature context often produces a legitimately different contract (e.g. "Validate Amount" on a Payment Feature vs. a Transfer Feature may enforce different limits and error codes and must remain separate).

If the ACs are identical or near-identical across two Features:

> "This behavior has the same contract as [FUNC-nnn] under [parent Feature]. Consider whether
> both are genuinely the same behavior in different contexts, or whether one can be reused.
> If the contracts are truly identical, consolidating avoids a maintenance burden — a contract
> change must otherwise be applied in every copy, increasing the risk of divergence."

If contextually distinct despite similar names, create a new Functionality and note the related one for future reviewers.

## Step 5 — Output canonical Functionality entity

> **ID assignment:** before assigning a `FUNC-nnn` ID, run
> `python scripts/next_id.py --type FUNC --catalog catalog.json`
> to get the next available ID and avoid collisions.
> For AC IDs, use `--type AC --parent FUNC-<nnn>` to get the next sequential AC number.

Output using the project's Storage Profile format (defined per project — see `../../docs/guides/living-doc-copilot.md`). Canonical fields (see [living-doc-glossary](../references/living-doc-glossary.md) ([remote](https://github.com/AbsaOSS/agentic-toolkit/blob/master/skills/references/living-doc-glossary.md)) for AC format details):

| Field | Required | Value |
|---|---|---|
| entity type | Yes | `Functionality` |
| `id` | Yes | `FUNC-<nnn>` (e.g. `FUNC-001`) |
| `name` | Yes | `<parent Feature name> – <behavior phrase>` (e.g. "Login Page – Validate Password Strength") |
| `parent_feature` | Yes | `FEAT-<nnn>` ID of the owning Feature |
| `status` | Yes | `planned` \| `active` \| `deprecated` |
| `acceptance_criteria` | Yes | List of ACs in the format defined in [living-doc-glossary](../references/living-doc-glossary.md) ([remote](https://github.com/AbsaOSS/agentic-toolkit/blob/master/skills/references/living-doc-glossary.md)) |

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
| Functionality name is a noun (e.g. "Password Validation") | Names must be verb phrases expressing the atomic behavior — e.g. "Validate Password Strength". A noun names a concept; a verb phrase names what the code does. |
| Functionality AC describes a full user journey (e.g. "User logs in and sees their dashboard") | That is a User Story AC — redirect to **living-doc-create-user-story**. Functionality ACs describe a single function's input → output or side effect. |
| Functionality has only happy-path ACs | Edge cases (null input, boundary values, error codes) are missing. Run through the completeness checklist in Step 3 before confirming. Untested error paths are the most common source of production incidents. |
| AC says "returns error" without specifying the type or code | Specify the error code using the canonical AC format: `– Raises {error code} when …` with `– Error code: CODE_VALUE`. Without a named code, the AC cannot be verified against a specific error contract. |
| AC uses `{placeholder}` for a single fixed value | Write the value inline. `{placeholder}` is only justified when two or more values vary across AC variants. |
| Two Functionalities have identical or near-identical ACs | Duplicate ACs create a maintenance burden. Consolidate into one shared Functionality owned by the appropriate parent Feature. |
| Functionality has no parent Feature | A Functionality without a parent Feature is untraceable — it cannot appear in impact analysis. Create or identify the parent Feature first. |

## Out-of-scope redirects

| Request type | Correct skill |
|---|---|
| "Create a User Story" | `living-doc-create-user-story` — this skill documents atomic behaviors, not end-to-end User Stories |
| "Create a Feature entity" | `living-doc-create-feature` — a Feature is a system surface, not an atomic behavior |
| "Generate BDD scenarios" | `living-doc-scenario-creator` — scenario generation requires a User Story with ACs |
