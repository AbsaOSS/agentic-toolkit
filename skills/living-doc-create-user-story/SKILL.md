---
name: living-doc-create-user-story
description: >
  Guide the creation of a well-formed User Story (US) with business-level Acceptance Criteria
  that are traceable, testable, and E2E-ready. Activate when creating a new User Story for a
  business capability, eliciting As-a/I-can/so-that narratives, defining US-level Acceptance
  Criteria, or validating User Story completeness before handing off to scenario creation.
  Triggers on: "create a user story", "new user story for", "write acceptance criteria for",
  "document a business requirement", "define US AC", "user story template", "as a user I want",
  "elicit requirements", "AC for user story", "US acceptance criteria",
  "review this user story", "is my narrative well-formed".
  Does NOT trigger for: atomic component behaviors (use living-doc-create-functionality),
  documenting system surfaces (use living-doc-create-feature).
  Pairs with living-doc-create-functionality.
license: Apache-2.0
compatibility: GitHub Copilot
---

# Living Doc — Create User Story

> **Key concepts:** Feature, Functionality, User Story, AC — see [living-doc-glossary](../references/living-doc-glossary.md) ([remote](https://github.com/AbsaOSS/agentic-toolkit/blob/master/skills/references/living-doc-glossary.md)).

## Step 1 — Elicit the narrative

Before asking, **scan the conversation context** for an actor, capability, or business outcome already stated by the user. If the user clearly provides all three parts and asks for the final artifact now, form the narrative directly and proceed to output. Otherwise, walk through all three questions in order. When a detail is already implied, restate it as a proposed answer and ask the user to confirm or refine it rather than silently skipping the question.

Ask these three questions explicitly:

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

Use `{placeholder}` syntax when a value varies, and list the concrete values immediately below. During elicitation, capture ACs using structured condition / action / outcome language; in the final JSON, convert each accepted AC into a plain-language description.

When reviewing an existing User Story, classify **only happy-path ACs present** as an **Important** gap. Name the missing cases in domain language and propose 2-3 extra Given / When / Then ACs. For password-reset stories, explicitly check for: unregistered email or phone, expired token or code, already-used token or code, wrong code, and retry limits.

If the request is really for a single atomic rule or technical behavior rather than an end-to-end user outcome, say so explicitly: this is a **Functionality-level behavior**, not a User Story. Stop and redirect to `living-doc-create-functionality`.

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

> **ID assignment:** before assigning a `US-nnn` ID, run
> `python scripts/next_id.py --type US --catalog catalog.json`
> to get the next available ID and avoid collisions.

Invariants that must hold before outputting:
- At least one AC exists
- At least one Feature is linked (or flagged as `[NEW]`)
- Status defaults to `planned`
- No open `[TODO]` markers

When creating a new User Story, output **one fenced `json` code block** using this canonical shape:

```json
{
  "type": "UserStory",
  "id": "US-001",
  "title": "Reset password via SMS",
  "status": "planned",
  "as_a": "registered customer",
  "i_want": "reset my password via SMS",
  "so_that": "I can regain access even when I cannot use email",
  "features": ["FEAT-login"],
  "acceptance_criteria": [
    {
      "id": "US-001-AC-1",
      "description": "A registered customer with a phone number on file can request a password reset code by SMS and sees confirmation that the code was sent."
    },
    {
      "id": "US-001-AC-2",
      "description": "A customer who enters an unregistered phone number is told that the reset request cannot be completed."
    },
    {
      "id": "US-001-AC-3",
      "description": "A customer who submits an expired or already-used reset code is told to request a new code."
    }
  ]
}
```

Rules:
- Use `title` rather than `name`
- Use `as_a`, `i_want`, and `so_that`
- Every AC object must have `id` in `US-<nnn>-AC-<n>` format and a plain-language `description`
- Write AC descriptions in plain language — no structured language keywords in JSON values

## Anti-patterns to flag

| Anti-pattern | Warning |
|---|---|
| AC says "the system saves to the database" | Technical implementation — restate as user outcome. Provide a rewritten AC: e.g. "When the customer confirms the order, then the order is acknowledged and the customer sees a confirmation message." |
| AC says "unit test passes" | Test is not an AC — describe the behavior, not how it's verified |
| Narrative says "As a system..." | System is not a user — name the human role |
| Same capability described for two different actors | Two actors = two separate User Stories. Different actors have different permissions, audit requirements, and AC sets. Mixing two actor perspectives in one User Story produces ambiguous ACs. Shared Functionalities (e.g. OTP generation, email delivery) can be linked to both User Stories. |
| User Story "I want" clause contains "and" | Multiple capabilities in one User Story — split at each “and”. Each capability has its own failure paths and may touch different Features; bundling them makes ACs ambiguous and traceability impossible. |
| AC uses `{placeholder}` for a single value | Placeholder syntax is only justified when two or more values vary. If only one value applies, write it inline. Example: instead of `{error type}: inline validation message`, write `an inline validation message is shown`. |
| AC describes a non-observable outcome | e.g. “a background job processes the record” — the user cannot observe this. Restate as the observable signal (e.g. “the confirmation email arrives within 60 seconds”), or redirect the behavior to a Functionality entity if it is purely technical. |
| AC identifier does not follow `US-<nnn>-AC-<n>` | Every acceptance criterion in the JSON output needs a stable `US-<nnn>-AC-<n>` id so it can be referenced unambiguously. |
| AC behavior already documented in another User Story | Duplicate ACs create a maintenance burden — any change must be applied in every copy. Extract the shared behavior into a Functionality entity and link both User Stories to it. |