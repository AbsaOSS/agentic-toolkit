---
name: living-doc-update
description: >
  Update, amend, or deprecate existing living documentation entities (User Stories, Features,
  Functionalities). Activate when adding new ACs to an existing User Story, changing a Feature's
  ownership or status, deprecating a Functionality whose code has been deleted, or promoting a
  User Story from draft to ready.
  Triggers on: "update user story", "add AC to user story", "deprecate feature", "mark US ready",
  "change feature owner", "update functionality", "deprecate functionality",
  "living doc update", "update living doc entity", "mark feature deprecated", "update AC",
  "change status of user story".
  Does NOT trigger for: creating new entities from scratch (use living-doc-create-user-story,
  living-doc-create-feature, or living-doc-create-functionality), finding gaps
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
| Deprecate an entity | Any entity | Set `status: deprecated`; add `deprecated_at` and `reason` |
| Delete a Functionality | Functionality | Do not delete — deprecate it and link to the commit that removed the code |

## Update a User Story — add or modify ACs

When adding a new AC to an existing User Story:

1. Load the existing User Story entity
2. Assign the next sequential AC ID: `AC:US-<nnn>-<nn>`
3. Elicit the new AC using the same completeness checklist as `living-doc-create-user-story`:
   - Happy path covered?
   - Error paths covered?
   - Alternative flows covered?
4. Check whether the new AC affects any existing Gherkin scenarios — flag for
   `gherkin-living-doc-sync` if so

When modifying an existing AC **keep the AC ID stable** — changing the ID breaks traceability
to linked tests and Gherkin scenarios. Only change the description text or state. If the changed
AC text affects the wording of linked Gherkin steps, flag the linked scenarios for
`gherkin-living-doc-sync`.

## Promote a User Story from draft to ready

Invariants that must hold before setting `status: ready`:

| Check | Requirement |
|---|---|
| Narrative complete | As-a/I-can/so-that is filled in with a named actor |
| At least one Feature linked | Not `[]` and not `[NEW: ...]` |
| At least one AC | And at least one error/alternative-path AC |
| No open `[TODO]` markers | Description and ACs are finalised |

Warn if any invariant fails:
> "User Story US-042 cannot be moved to 'ready': no error-path AC exists. Add at least one
> AC for a failure or edge case before promoting."

## Deprecate a Feature or Functionality

Use this workflow when code backing an entity is deleted or a business capability is retired.
Set the relevant fields in the project's Storage Profile format:

| Field | Value |
|---|---|
| `status` | `deprecated` |
| `deprecated_at` | Date of deprecation |
| `deprecation_reason` | Why it was deprecated |
| `superseded_by` | ID of the replacement entity (if applicable) |

Rules:
- Always deprecate — never delete entities (preserves audit trail)
- Add `superseded_by` when a replacement entity exists
- Flag any Gherkin scenarios linked to the deprecated entity for `gherkin-living-doc-sync`

## Update Feature ownership or dependencies

When a team changes ownership of a Feature, update the `owners` field and set `owner_changed_at`
(date) and `owner_change_reason`. If the Feature has open User Stories, notify the new owner.

## Descope an AC mid-sprint

When an AC is moved out of the current sprint but not permanently removed:

- Add `descoped_at` (date) and `descoped_reason` fields — **do not delete the AC** (preserves audit trail)
- The AC's official lifecycle state remains `Planned` (still required, just deferred)
- Add `future_release` field if the work is planned for a later sprint
- Flag any linked Gherkin scenarios for `@wip` or `@pending` tagging via `gherkin-living-doc-sync`

```
AC:US-042-03 (v1.2.0 – Planned)
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
| Generate Gherkin scenarios from a User Story | `living-doc-scenario-creator` |

## Output change summary

After every update, emit a structured change record. For **modified AC text**, show the old and
new values clearly labelled, and list any linked Gherkin scenarios that need re-syncing:

```
LIVING DOC UPDATE — 2026-05-15
  Entity:  US-042 — Customer applies a promotional discount
  Changes:
    + Added AC AC:US-042-04 (state: Planned) — Promo code expired returns 422 with error message
    ~ Modified AC AC:US-042-01:
        OLD: "Payment must complete within 3 seconds under normal load (p99 SLA)"
        NEW: "Payment must complete within 2 seconds under normal load (p99 SLA)"
      Linked Gherkin scenarios requiring re-sync:
        → checkout.feature:41 — Scenario: Payment completes within SLA
  Downstream flags:
    → Run gherkin-living-doc-sync: changed AC text affects linked scenario wording
    → Run living-doc-gap-finder to confirm coverage after update
```
