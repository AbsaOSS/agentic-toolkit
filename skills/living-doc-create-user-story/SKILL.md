---
name: living-doc-create-user-story
description: >
  Guide the creation of a well-formed User Story (US) with business-level Acceptance Criteria
  that are traceable, testable, and E2E-ready. Activate when creating a new User Story for a
  business capability, eliciting As-a/I-can/so-that narratives, defining US-level Acceptance
  Criteria, or validating User Story completeness before handing off to scenario creation.
  Triggers on: "create a user story", "new user story for", "write acceptance criteria for",
  "document a business requirement", "define US AC", "user story template", "as a user I want",
  "elicit requirements", "AC for user story", "US acceptance criteria".
  Does NOT trigger for: atomic component behaviors (use living-doc-create-functionality),
  documenting system surfaces (use living-doc-create-feature), generating BDD scenarios
  (use living-doc-scenario-creator).
  Pairs with living-doc-create-functionality and living-doc-scenario-creator.
license: Apache-2.0
compatibility: GitHub Copilot
---

# Living Doc — Create User Story

> **Key concepts:** Feature, Functionality, User Story, AC — see `../references/living-doc-glossary.md`.

## Step 1 — Elicit the narrative

Before asking, **scan the conversation context** for an actor, capability, or business outcome already stated by the user. If all three are present, form the narrative directly and ask for confirmation rather than re-asking the questions.

Ask only for what is missing:

1. **Who is the user?** — The actor using the system (a specific role, not "the user")
2. **What do they want to do?** — The capability or action in business terms
3. **Why?** — The business outcome or value delivered

Form the canonical narrative:

```
As a <actor>,
I can <capability>,
so that <business outcome>.
```

**Validation:**
- Actor must be a named role — not "system", "admin", or "the app"
- If the actor given is "the system" or similar, reject it: *"The system is not a valid actor.
  Ask: who triggers this action? Who benefits from it? Name that human role."*
  System-initiated or background flows do not belong in a User Story — they belong in a
  Functionality. Redirect to `living-doc-create-functionality` for system-driven behaviors.
- Capability must be an action the user performs — not a technical implementation
- Outcome must describe business value — not system state

## Step 2 — Establish domain context

Ask: *Which Feature(s) does this User Story touch?*

A Feature is a named system surface (UI screen or API endpoint group). If the Feature
has not yet been created as a living doc entity, note it as `[NEW: <name>]` and suggest creating it
with `living-doc-create-feature` after completing the User Story.

## Step 3 — Elicit Acceptance Criteria

Each AC must be:
- **End-to-end** — written from the user's perspective, not the database's
- **Outcome-focused** — "order is confirmed" not "DB record is inserted"
- **Binary** — clear pass/fail; no "should usually" or "typically"
- **Single placeholder** — at most ONE `{placeholder}` per AC statement. If two aspects vary independently, write a separate AC for each.

Use `{placeholder}` syntax when a value varies, and list the concrete values immediately below:

```
AC:US-<nnn>-<nn> (v<version> – Planned)
   – <end-to-end outcome from the user's perspective, with optional {placeholder}>
   – <Placeholder>: value1, value2, ...
```

See full AC format and examples in `../references/living-doc-glossary.md`.

**Completeness check — always ask:**
1. What happens on the happy path? (at least one AC required)
2. What happens when the input is invalid or missing?
3. What happens when a downstream dependency fails?
4. Are there alternative flows (e.g. user is not logged in, item is out of stock)?

Warn if only happy-path ACs are present:
> "No error or alternative-path ACs were provided. Real systems fail — add at least one
> AC for a failure or edge case before marking this US ready."

**Warn if an AC reads like a Functionality AC** (too atomic/technical):
> "This AC describes a technical behavior rather than an end-to-end user outcome.
> Consider creating a Functionality entity for this behavior with
> living-doc-create-functionality."

## Step 4 — Validate and output

Invariants that must hold before outputting:
- At least one AC exists
- At least one Feature is linked (or flagged as `[NEW]`)
- Status defaults to `planned`
- No open `[TODO]` markers

Output the User Story using the project's Storage Profile format. Canonical fields:

| Field | Required | Value |
|---|---|---|
| entity type | Yes | `UserStory` |
| `id` | Yes | `US-<nnn>` (e.g. `US-001`) |
| `name` | Yes | Short imperative title (e.g. "Customer Login") |
| `status` | Yes | `planned` — default for new entities |
| `as_a` | Yes | Named actor |
| `i_can` | Yes | The capability |
| `so_that` | Yes | Business outcome |
| `features` | Yes | List of `FEAT-<nnn>` IDs |
| `acceptance_criteria` | Yes | List of ACs in the format defined in `../references/living-doc-glossary.md` |

## Anti-patterns to flag

| Anti-pattern | Warning |
|---|---|
| AC says "the system saves to the database" | Technical implementation — restate as user outcome. Provide a rewritten AC: e.g. "When the customer confirms the order, then the order is acknowledged and the customer sees a confirmation message." |
| AC says "unit test passes" | Test is not an AC — describe the behavior, not how it's verified |
| Narrative says "As a system..." | System is not a user — name the human role |
| Same capability described for two different actors | Two actors = two separate User Stories. Different actors have different permissions, audit requirements, and AC sets. Mixing two actor perspectives in one User Story produces ambiguous ACs. Shared Functionalities (e.g. OTP generation, email delivery) can be linked to both User Stories. || User Story "I can" clause contains "and" | Multiple capabilities in one User Story — split at each “and”. Each capability has its own failure paths and may touch different Features; bundling them makes ACs ambiguous and traceability impossible. |
| AC uses `{placeholder}` for a single value | Placeholder syntax is only justified when two or more values vary. If only one value applies, write it inline. Example: instead of `{error type}: inline validation message`, write `an inline validation message is shown`. |
| AC describes a non-observable outcome | e.g. “a background job processes the record” — the user cannot observe this. Restate as the observable signal (e.g. “the confirmation email arrives within 60 seconds”), or redirect the behavior to a Functionality entity if it is purely technical. |
| AC identifier is missing the version or state | AC format requires `AC:<parent-id>-<nn> (v<version> – <State>)`. An AC without version or state cannot be traced across releases or marked as deprecated without rewriting its ID. |
| AC behavior already documented in another User Story | Duplicate ACs create a maintenance burden — any change must be applied in every copy. Extract the shared behavior into a Functionality entity and link both User Stories to it. |