---
name: living-doc-create-user-story
description: >
  Guide the creation of a well-formed User Story (US) with business-level Acceptance Criteria
  that are traceable, testable, and E2E-ready. Use when creating a new User Story, eliciting
  As-a/I-can/so-that narratives, defining US-level ACs, validating US narrative structure,
  or reviewing US completeness before scenario creation.
  Triggers on: "create a user story", "new user story for", "write acceptance criteria for",
  "document a business requirement", "define US AC", "user story template", "as a user I want",
  "elicit requirements", "AC for user story", "US acceptance criteria",
  "review this user story", "is my narrative well-formed", "I-want clause".
  Does NOT trigger for: atomic behaviors (use living-doc-create-functionality); system surfaces
  (use living-doc-create-feature); generating BDD scenarios (use living-doc-scenario-creator).
  Pairs with living-doc-create-feature, living-doc-create-functionality, and
  living-doc-scenario-creator (generate scenarios after the US is active).
license: Apache-2.0
compatibility: GitHub Copilot
---

# Living Doc — Create User Story

> **Key concepts:** Feature, Functionality, User Story, AC — see [living-doc-glossary](../shared/references/living-doc-glossary.md) ([remote](https://github.com/AbsaOSS/agentic-toolkit/blob/master/skills/shared/references/living-doc-glossary.md)).

## Step 1 — Elicit the narrative

Before asking, **scan the conversation context** for an actor, capability, or business outcome already stated by the user. If the user clearly provides all three parts and asks for the final artifact now, form the narrative directly and proceed to output. Otherwise, walk through all three questions in order. When a detail is already implied, restate it as a proposed answer and ask the user to confirm or refine it rather than silently skipping the question.

When the user asks to **create**, **document**, or **draft** a User Story, do not stop at elicitation questions alone. Ask the missing questions first as three distinct numbered questions (**Who? What? Why?**), then explicitly ask **Which Feature(s) does this story touch?**, then emit a starter User Story JSON draft in the same reply. For bare prompts like *"Create a new User Story for password reset"* or *"I want to create a new User Story for the password reset capability"*, do **not** wait for confirmation before drafting — assume a sensible starter narrative and output the JSON immediately after the questions.

If the user names a common capability but leaves some details implicit, infer a sensible starter draft instead of blocking. Common patterns:
- password reset → actor usually `registered customer`; likely Feature `FEAT-login`; ask the three narrative questions plus the Feature question, then still output starter JSON immediately with at least one happy-path AC and 2 error-path ACs
- password reset via SMS → add `[NEW: SMS Authentication]` or the known SMS/login Feature if not yet created
- customer service agent views customer order history → actor `customer service agent`; likely Feature `FEAT-order-management`; include customer-not-found and permission error ACs
- two different actors in one narrative → split into two separate User Stories and call out that shared Functionalities can be linked to both

For create flows, explicitly note that if the user provides only happy-path ACs, you will warn them and add at least one failure or alternative-path AC before treating the story as ready.
During elicitation, you may phrase candidate ACs in Given / When / Then form; once accepted, flatten them into the JSON `description` strings.
Never end a create flow with only \"once confirmed, I will output the JSON later\" — the same reply must already contain the starter JSON artifact.

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
- If the actor given is "the system" or similar, warn: *"Using a system actor is not prohibited,
  but it is strongly discouraged. Prefer naming the human role that triggers or benefits from
  the behavior. If the flow is system-initiated with no direct human interaction, it is a better
  fit for a Functionality entity."*
  If the user insists on a system actor, ensure the `so that` clause names a human beneficiary.
  For purely system-driven behaviors with no human outcome, redirect to `living-doc-create-functionality`.
- Capability must be an action the user performs — not a technical implementation
- Outcome must describe business value — not system state

## Step 2 — Establish domain context

Ask: *Which Feature(s) does this User Story touch?*

A Feature is a named system surface (UI screen or API endpoint group). If the Feature
has not yet been created as a living doc entity, note it as `[NEW: <name>]` and suggest creating it
with `living-doc-create-feature` after completing the User Story.

Also ask: *Are there existing Functionalities this User Story relies on?* If yes, link them in the `functionalities` array. This prevents `ORPHAN_FUNCTIONALITY` gaps and makes the entity graph traversable from US down to test coverage.

## Step 3 — Elicit Acceptance Criteria

Each AC must be:
- **End-to-end** — written from the user's perspective, not the database's
- **Outcome-focused** — "order is confirmed" not "DB record is inserted"
- **Binary** — clear pass/fail; no "should usually" or "typically"
- **Single placeholder** — at most ONE `{placeholder}` per AC statement. If two aspects vary independently, write a separate AC for each.
- If the error types are distinct, write a **separate AC per error type** instead of bundling them behind one placeholder.
- **Present simple tense** — "the user sees" not "the user will see" or "should be shown"; ACs are timeless contracts, not predictions
- Future-tense forms like `will be able to` and `should be shown` are predictions, not timeless contracts; rewrite them into present-tense capability or outcome statements and call out this principle explicitly during review
- **Active voice** — "the customer receives a confirmation email" not "a confirmation email is sent to the customer"; makes subject and action unambiguous
- **Correct modal verbs** — use `can` for user-initiated capability; drop the modal for outcome statements ("a confirmation is displayed"); avoid "should", "may", "might" (non-binary)
- **Named persona** — use the actor from the narrative ("a data steward can approve…") not the generic "the user"

Use `{placeholder}` syntax when a value varies, and list the concrete values immediately below. During elicitation, capture ACs using structured condition / action / outcome language; in the final JSON, convert each accepted AC into a plain-language description.
After the narrative and Feature question are covered, explicitly ask the user for: (1) one happy-path Given / When / Then AC, and (2) at least two error or alternative-path Given / When / Then ACs. If they provide only happy-path ACs, warn and add the missing failure-path prompts before finalizing.

When reviewing an existing User Story, classify **only happy-path ACs present** as an **Important** gap. Name the missing cases in domain language and propose 2-3 extra **Given / When / Then** ACs. For password-reset stories, explicitly check for: unregistered email or phone, expired token or code, already-used token or code, wrong code, and retry limits. Do **not** nitpick narrative wording, status, or Feature links unless the user explicitly asks for full schema validation or those fields are the direct problem under review.

Example review additions:
- **Given** a registered customer enters an email address that is not in the system, **When** they request a password reset, **Then** they are told the reset request cannot be completed.
- **Given** a registered customer has a reset token that is expired or already used, **When** they submit it, **Then** they are told to request a new reset link or code.

If the request is really for a single atomic rule or technical behavior rather than an end-to-end user outcome, say so explicitly: this is a **Functionality-level behavior**, not a User Story. Stop and redirect to `living-doc-create-functionality`. State that this skill is the one to use for the extracted technical behavior.
When redirecting, name the target skill explicitly: **use `living-doc-create-functionality`**.

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
> Do not guess or infer the numeric ID without showing that allocator step.
>
> If the prompt states an existing catalog range (for example `US-001` through `US-013`), reflect the allocator call in the answer as `Ran: python scripts/next_id.py --type US --catalog catalog.json -> US-014` and use that returned numeric ID in the JSON.
>
> If the prompt explicitly says the catalog is missing / `next_id.py` cannot run for a real save, use `US-PENDING` and warn: `Catalog not available — ID could not be assigned. Run next_id.py --type US once the catalog is present and update this field before saving.`
>
> If the prompt is a normal create/output-format request and catalog state is not discussed, use a numeric-looking draft ID such as `US-001` and matching AC ids such as `AC:US-001-01` in the starter JSON.
>
> If the prompt gives a known catalog range (for example through `US-013`), ask the missing narrative questions briefly and still emit starter JSON immediately with the allocated ID (`US-014` in that example).
> Show that allocator step explicitly, for example: `Running: python scripts/next_id.py --type US --catalog catalog.json -> US-014`

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
      "id": "AC:US-001-01",
      "description": "A registered customer with a phone number on file can request a password reset code by SMS and sees confirmation that the code was sent."
    },
    {
      "id": "AC:US-001-02",
      "description": "A customer who enters an unregistered phone number is told that the reset request cannot be completed."
    },
    {
      "id": "AC:US-001-03",
      "description": "A customer who submits an expired or already-used reset code is told to request a new code."
    }
  ]
}
```

Rules:
- Use `title` rather than `name`
- Use `as_a`, `i_want`, and `so_that`
- Every AC object must have `id` in `AC:US-<nnn>-<nn>` format and a plain-language `description`
- Write AC descriptions in plain language — no structured language keywords in JSON values
- For create/document requests, the response itself must contain the JSON artifact — do not say "then I will output the entity later"
- If details remain unknown, ask the missing questions briefly **before** the JSON, but still include a starter JSON draft immediately after

Starter example for a create request:
```json
{
  "type": "UserStory",
  "id": "US-001",
  "title": "Reset password via SMS",
  "status": "planned",
  "as_a": "registered customer",
  "i_want": "reset my password via SMS",
  "so_that": "I can regain access even when I cannot use email",
  "features": ["FEAT-login", "[NEW: SMS Authentication]"],
  "acceptance_criteria": [
    {
      "id": "AC:US-001-01",
      "description": "A registered customer can request a password reset code by SMS and sees confirmation that the code was sent."
    },
    {
      "id": "AC:US-001-02",
      "description": "A customer who enters an unregistered phone number is told that the reset request cannot be completed."
    },
    {
      "id": "AC:US-001-03",
      "description": "A customer who submits an expired or already-used reset code is told to request a new code."
    }
  ],
  "functionalities": []
}
```

For password-reset stories, the starter JSON should already include error-path ACs such as unregistered contact detail and expired/already-used reset token or code.
For a generic password-reset prompt with no channel specified, default the starter draft to `title: "Reset password"`, `features: ["FEAT-login"]`, and still emit the JSON immediately after the four questions.

> **Next steps after creation:** The User Story is created with `status: "planned"`. When all ACs are finalised and at least one Feature is linked, use `living-doc-update` to promote it to `active`. After promotion, use `living-doc-scenario-creator` to generate BDD feature files for each `active` AC.

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

Exits 0 if valid (warnings are non-blocking). Exits 1 if any required field is missing, the ID format is wrong, no AC is present, or the status value is invalid.

## Anti-patterns to flag

| Anti-pattern | Warning |
|---|---|
| AC says "the system saves to the database" | Technical implementation — restate as user outcome. Provide a rewritten AC: e.g. "When the customer confirms the order, then the order is acknowledged and the customer sees a confirmation message." |
| AC says "unit test passes" | Test is not an AC — describe the behavior, not how it's verified |
| Narrative says "As a system..." | Not prohibited, but strongly discouraged — system-initiated flows are better modelled as Functionality entities. If kept, the `so that` clause must name a human beneficiary. |
| Same capability described for two different actors | Two actors = two separate User Stories. Different actors have different permissions, audit requirements, and AC sets. Mixing two actor perspectives in one User Story produces ambiguous ACs. Shared Functionalities (e.g. OTP generation, email delivery) can be linked to both User Stories. |
| User Story "I want" clause contains "and" | Multiple capabilities in one User Story — split at each “and”. Each capability has its own failure paths and may touch different Features; bundling them makes ACs ambiguous and traceability impossible. |
| AC uses `{placeholder}` for a single value | Placeholder syntax is only justified when two or more values vary. If only one value applies, write it inline. Example: instead of `{error type}: inline validation message`, write `When the customer submits an invalid email address, an inline validation message is shown.` If the error types are genuinely different, write a separate AC for each error type. |
| AC describes a non-observable outcome | e.g. “a background job processes the record” — the user cannot observe this. Restate as the observable signal (e.g. “the customer receives a confirmation email within 60 seconds”), or redirect the behavior to **living-doc-create-functionality** if it is purely technical. |
| AC identifier does not follow `AC:US-<nnn>-<nn>` | Every acceptance criterion in the JSON output needs a stable `AC:US-<nnn>-<nn>` id so it can be referenced unambiguously. |
| AC behavior already documented in another User Story | Duplicate ACs create a maintenance burden — any change must be applied in every copy. Extract the shared behavior into a Functionality entity with **living-doc-create-functionality** and link both User Stories to it. |
| AC uses "should", "may", or "might" | Non-binary modal — the AC cannot be passed or failed decisively. Use `can` for user capability ("a data steward can approve…") and drop the modal for outcome statements ("a confirmation message is displayed"). Also avoid future-tense predictions like `will be able to` and `should be shown`; User Story ACs are present-tense contracts. |
| AC subject is "the user" (generic) | Use the named actor from the narrative — "a data steward can approve…" not "the user can approve…". Generic "user" creates ambiguity when multiple roles share a surface and should be called out explicitly during review. |
| AC outcome is vague ("success is shown", "an error appears") | State what the user experiences specifically enough to test: "a confirmation message is displayed" or "an inline error states the email is already in use". Avoid both vague and over-specific (visual style, pixel dimensions, CSS class names, component internals). Say this explicitly when reviewing wording. |

---

## Out-of-scope routing

| Request | Correct skill |
|---|---|
| Document an atomic behavior or business rule | `living-doc-create-functionality` |
| Document a system surface (screen, API) | `living-doc-create-feature` |
| Generate BDD scenarios for User Story ACs | `living-doc-scenario-creator` |
| Update or deprecate an existing User Story | `living-doc-update` |