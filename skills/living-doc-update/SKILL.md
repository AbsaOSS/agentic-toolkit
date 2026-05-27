---
name: living-doc-update
description: >
  Update, amend, or deprecate existing living documentation entities (User Stories, Features,
  Functionalities). Use when adding new ACs to an existing User Story, descoping or removing
  an AC, changing a Feature's ownership or status, updating the Feature Registry after a team
  restructure, deprecating a Functionality whose code has been deleted, or promoting a User
  Story from draft to ready.
  Triggers on: "update user story", "add AC to user story", "descope AC", "deprecate feature",
  "mark US ready", "change feature owner", "update functionality", "deprecate functionality",
  "living doc update", "update living doc entity", "mark feature deprecated", "update AC",
  "change status of user story", "update feature registry".
  Does NOT trigger for: creating new entities (use living-doc-create-*), finding gaps
  (use living-doc-gap-finder), generating scenarios (use living-doc-scenario-creator).

license: Apache-2.0
compatibility: GitHub Copilot
---

# Living Doc — Update

> **Key concepts:** Feature, Functionality, User Story, AC — see [living-doc-glossary](../references/living-doc-glossary.md) ([remote](https://github.com/AbsaOSS/agentic-toolkit/blob/master/skills/references/living-doc-glossary.md)).

## Identify the entity and change type

Ask: *Which entity is being updated, and what kind of change is this?*

| Change type | Entity | Update action |
|---|---|---|
| Add a new AC | User Story / Functionality | Append a new AC entry with the next sequential AC ID |
| Modify AC description | User Story / Functionality | Edit the description; keep the AC ID stable |
| Change status | Any entity | Update `status` field; record the transition event |
| Change owner | Feature | Update `owners` field |
| Add a linked User Story | Feature | Append to `user_stories` |
| Deprecate an entity | Any entity | Set `status: deprecated`; add `deprecated_at`, `deprecation_reason`, and optionally `superseded_by` |
| Delete a Functionality | Functionality | Do not delete — deprecate it and link to the commit that removed the code |

## Update a User Story — add or modify ACs

When adding a new AC to an existing User Story:

1. Load the existing User Story entity
2. Assign the next sequential AC ID (for example `US-042-AC-4`; preserve an existing project
   prefix such as `AC:US-042-04` if the catalog already uses it)
3. Elicit the new AC using the same completeness checklist as `living-doc-create-user-story` and
   capture it in `description`, `given`, `when`, `then` form:
   - Happy path covered?
   - Error paths covered?
   - Alternative flows covered?
4. Confirm whether the new AC requires new or updated tests — flag for the appropriate testing
   workflow if so

When modifying an existing AC **keep the AC ID stable** — changing the ID breaks traceability
to linked tests. Only update the `description`, `given`, `when`, `then`, or
state fields. If the changed AC text affects linked tests, flag them for update.

## Promote a User Story from planned to active

Invariants that must hold before setting `status: active`:

| Check | Requirement |
|---|---|
| Narrative complete | As-a/I-can/so-that is filled in with a named actor |
| At least one Feature linked | Not `[]` and not `[NEW: ...]` |
| At least one AC | And at least one error/alternative-path AC |
| No open `[TODO]` markers | Description and ACs are finalised |

Warn if any invariant fails:
> "User Story US-042 cannot be promoted from 'planned' to 'active': no error-path AC exists. Add at least one
> AC for a failure or edge case before promoting."

## Deprecate a Feature or Functionality

Use this workflow when code backing an entity is deleted or a business capability is retired.
Set the relevant fields in the project's Storage Profile format:

| Field | Value |
|---|---|
| `status` | `deprecated` |
| `deprecated_at` | Date of deprecation |
| `deprecation_reason` | Why it was deprecated |
| `deprecated_code_commit` | Commit SHA or URL that removed the backing code (if applicable) |
| `superseded_by` | ID of the replacement entity (if applicable) |

Rules:
- Always deprecate — never delete entities (preserves audit trail)
- Add `deprecated_code_commit` when the code was removed in a commit
- Add `superseded_by` when a replacement entity exists
- Flag any tests linked to the deprecated entity for update or removal

## Update Feature ownership or dependencies

When a team changes ownership of a Feature, update the `owners` field and set `owner_changed_at`
(date) and `owner_change_reason`. If the Feature has open User Stories, notify the new owner.

## Descope an AC mid-sprint

When an AC is moved out of the current sprint but not permanently removed:

- Set `status: descoped` and add `descoped_at` (date) and `descoped_reason` fields — **do not delete the AC** (preserves audit trail)
- Add `future_release` field if the work is planned for a later sprint
- Flag any linked tests for `@skip` or `@pending` tagging

```
AC:US-042-03 (v1.2.0 – descoped)
   – Promo codes can be stacked and applied in defined priority order.
   – descoped_at: 2026-05-15
   – descoped_reason: Promo stacking rule deferred — too complex for current sprint
   – future_release: sprint-52
```

## Routing

| Request | Correct skill |
|---|---|
| Create a new User Story | `living-doc-create-user-story` |
| Create a new Feature | `living-doc-create-feature` |
| Create a new Functionality | `living-doc-create-functionality` |
| Find gaps in living documentation | `living-doc-gap-finder` |

## Script — `scripts/validate_entity.py`

After updating any entity, run this script to validate the result against the canonical schema.
It checks required fields, ID format, status values, AC structure, and (with `--catalog`)
referential integrity against the full catalog.

```bash
# Validate a single entity file
python scripts/validate_entity.py entity.json

# Validate with referential integrity checks
python scripts/validate_entity.py entity.json --catalog catalog.json

# Machine-readable output (exits 1 if any error)
python scripts/validate_entity.py entity.json --json
```

Exits 0 if valid (warnings are non-blocking). Exits 1 if any required field is missing,
an ID format is wrong, or a status value is invalid.

---

## Output change summary

After every update, emit a structured change record. For **modified AC text**, show the old and
new values clearly labelled, and list any linked tests that need updating:

```
LIVING DOC UPDATE — 2026-05-15
  Entity:  US-042 — Customer applies a promotional discount
  Changes:
    + Added AC AC:US-042-04 (state: Planned) — Promo code expired returns 422 with error message
    ~ Modified AC AC:US-042-01:
        OLD: "Payment must complete within 3 seconds under normal load (p99 SLA)"
        NEW: "Payment must complete within 2 seconds under normal load (p99 SLA)"
      Linked tests requiring update:
        checkout.feature:41 — Scenario: Payment completes within SLA
  Downstream flags:
    Run living-doc-gap-finder to confirm coverage after update
```
