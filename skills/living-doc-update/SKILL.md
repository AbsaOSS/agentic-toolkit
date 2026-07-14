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
  Pairs with gherkin-living-doc-sync (propagate AC changes) and bdd-maintain (cleanup after deprecation).
license: Apache-2.0
compatibility: GitHub Copilot
---

# Living Doc — Update

> **Key concepts:** Feature, Functionality, User Story, AC — see [living-doc-glossary](../../shared/references/living-doc-glossary.md) ([remote](https://github.com/AbsaOSS/agentic-toolkit/blob/master/skills/shared/references/living-doc-glossary.md)).

## Identify the entity and change type

Ask: *Which entity is being updated, and what kind of change is this?*

If the user says "update the story" but the substance is a newly discovered edge case, missing behavior, or new business rule, classify it explicitly as an **add a new AC** request before proceeding.

| Change type | Entity | Update action |
|---|---|---|
| Add a new AC | User Story / Functionality | Append a new AC entry with the next sequential AC ID |
| Modify AC description | User Story / Functionality | Edit the description; keep the AC ID stable |
| Change status | Any entity | Update `status` field; record the transition event |
| Change owner | Feature | Update `owners` field; add `owner_changed_at` (ISO date) and `owner_change_reason` fields; notify the new owner if open User Stories are linked to the Feature |
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
5. Flag linked scenarios for `gherkin-living-doc-sync` so feature files can pick up the new or changed AC text and tags.
6. Emit a change summary showing the new AC ID and its Given / When / Then content.

Do not stop at workflow narration or ask for a fixture file before demonstrating the update shape. For add-AC requests, output the concrete change summary block immediately using the supplied entity ID and the new AC content.

When modifying an existing AC **keep the AC ID stable** — changing the ID breaks traceability
to linked tests. Only update the `description`, `given`, `when`, `then`, or
state fields. If the changed AC text affects linked tests, flag them for update.

**AC versioning:** ACs carry a `(vMAJOR.MINOR.PATCH – state)` annotation.
- Bump the **minor** version for any business-rule change to an `Active` AC (e.g. `v1.0.0 → v1.1.0`).
- Bump the **patch** version for a wording clarification that does not change the rule (e.g. `v1.0.0 → v1.0.1`).
- The version must appear in the `# AC:` comment in linked Gherkin feature files — trigger `gherkin-living-doc-sync` to propagate the new version into those comments.

## Promote a Functionality from planned to active

A Functionality is ready to move from `planned` to `active` when all its ACs have passing tests.

| Check | Requirement |
|---|---|
| `test_coverage` entries present | Every AC has a `test_type` and `justification` |
| Tests passing | All referenced unit/integration tests pass in CI |
| No `FUNC-UNKNOWN` placeholder | Functionality has a stable registered ID |

After promoting a Functionality to `active`, run `living-doc-gap-finder` to confirm no `UNDOCUMENTED_FUNCTIONALITY` gaps remain.

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

When promotion is blocked because only a happy-path AC exists, give a concrete example error/alternative AC in the reply (for example: `When the delivery address is outside the shipping zone, the order is rejected with a clear reason.`).

After promoting a User Story to `active`, trigger `living-doc-scenario-creator` to generate BDD feature files for each `Active` AC if they do not yet exist.

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
- If a deprecated Feature owns Functionalities, flag every owned Functionality for deprecation review before closing the change.
- Flag any tests linked to the deprecated entity for update or removal
- If the deprecated entity has `ACTIVE` ACs with linked Gherkin scenarios, trigger
  `gherkin-living-doc-sync` to propagate `@deprecated` and `@review-needed` tags to those scenarios
- After `gherkin-living-doc-sync` has tagged the deprecated scenarios, trigger `bdd-maintain`
  REMOVE mode if the automation files for this entity should be deleted from the repository

## Rename a Feature

Changing a Feature's `id` or `name` requires these cascading updates:

1. Update the Feature entity (`id`, `name`, and any self-referencing fields).
2. Update `feature_id` in every Functionality linked to this Feature.
3. Update the `feature_registry` entry in `catalog.json` (change the `feature_id` key and any path comments).
4. Search `manifest.json` and `seed.yaml` for the old name or ID and update.
5. Search PageObject file headers for the old Feature reference and update.
6. If Gherkin feature files have a `# Feature:` header with the old name, update those headers.
7. Run `living-doc-gap-finder` to confirm no `ORPHAN_FUNCTIONALITY` gaps remain after the rename.

## Update Feature ownership or dependencies

When a team changes ownership of a Feature, update the `owners` field and set `owner_changed_at`
(date) and `owner_change_reason`. If the Feature has open User Stories, notify the new owner.

## Descope an AC mid-sprint

When an AC is moved out of the current sprint but not permanently removed:

- Set `status: descoped` — do not delete the AC (preserves audit trail and reinstating intent)
- Add `descoped_at` (date) and `descoped_reason` fields
- Add `future_release` field if the work is planned for a later sprint
- Flag any linked Gherkin scenarios for `@wip` or `@pending` tagging via `gherkin-living-doc-sync`

```

For **business-rule changes to an ACTIVE AC**, first show the AC side-by-side for confirmation, then apply the version bump:

```
OLD: AC:US-042-01 (v1.0.0 - Active) — Minimum order value is £50.
NEW: AC:US-042-01 (v1.1.0 - Active) — Minimum order value is £75.
```
AC:US-042-03 (v1.2.0 – descoped)
   – Promo codes can be stacked and applied in defined priority order.
   – descoped_at: 2026-05-15
   – descoped_reason: Promo stacking rule deferred — too complex for current sprint
   – future_release: sprint-52
```

## Out-of-scope routing

| Request | Correct skill |
|---|---|
| Create a new User Story | `living-doc-create-user-story` |
| Create a new Feature | `living-doc-create-feature` |
| Create a new Functionality | `living-doc-create-functionality` |
| Find gaps in living documentation | `living-doc-gap-finder` |
| AC modified, deprecated, or descoped — sync linked scenarios | `gherkin-living-doc-sync` |
| Deprecated entity — remove associated automation files | `bdd-maintain` |
| Assess impact of an AC change on Features and User Stories | `living-doc-impact-analysis` |

## Script — `scripts/validate_entity.py`

After updating any entity, run this script to validate the result against the canonical schema.
It checks required fields, ID format, status values, AC structure, and (with `--catalog`)
referential integrity against the full catalog.

```bash
# Validate a single entity file
python scripts/validate_entity.py entity.json

# Validate with referential integrity checks
python scripts/validate_entity.py entity.json --catalog catalog.json

# Enforce the project's AC state vocabulary (reads `ac_states` from the Project Profile)
python scripts/validate_entity.py entity.json --profile .copilot/bdd/.project-profile.yaml

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

For **added ACs**, use the same summary pattern rather than ending with validation only:

```
LIVING DOC UPDATE — 2026-05-15
  Entity:  US-089 — Delivery restrictions
  Changes:
    + Added AC AC:US-089-04 (state: Planned)
      GIVEN a customer enters an address outside the shipping zone
      WHEN they place the order
      THEN the order is blocked with SHIPPING_ZONE_EXCLUDED and a clear message
  Downstream flags:
    Run gherkin-living-doc-sync
```
