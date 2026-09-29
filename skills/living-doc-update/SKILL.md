---
name: living-doc-update
description: >
  Update or deprecate existing living-doc entities (User Stories, Features, Functionalities):
  add, modify, or descope an AC; change status or promote planned to active; change a
  Feature's owners, deprecation metadata, or dependencies; rename a Feature; update the
  Feature Registry; deprecate a Functionality whose code was deleted.
  Triggers on: "update user story", "add AC to user story", "update AC", "descope AC",
  "mark US ready", "change status of user story", "update functionality",
  "deprecate functionality", "deprecate feature", "mark feature deprecated",
  "change feature owner", "update feature registry", "change feature dependencies",
  "remove external dependency", "dependency became a feature", "promote external dependency",
  "living doc update".
  NOT for: creating entities (living-doc-create-*), finding gaps (living-doc-gap-finder),
  generating scenarios (living-doc-scenario-creator).
  Pairs with gherkin-living-doc-sync (AC changes) and bdd-maintain (post-deprecation cleanup).
license: Apache-2.0
---

# Living Doc — Update

> **Key concepts:** Feature, Functionality, User Story, AC — see [living-doc-glossary](../shared/references/living-doc-glossary.md) ([remote](https://github.com/AbsaOSS/agentic-toolkit/blob/master/skills/shared/references/living-doc-glossary.md)).

## Identify the entity and change type

Ask: *Which entity is being updated, and what kind of change is this?*

If the user says "update the story" but the substance is a newly discovered edge case, missing behavior, or new business rule, classify it explicitly as an **add a new AC** request before proceeding.

| Change type | Entity | Update action |
|---|---|---|
| Add a new AC | User Story / Functionality | Append a new AC entry with the next sequential AC ID |
| Modify AC description | User Story / Functionality | Edit the description; keep the AC ID stable |
| Change status | User Story / Functionality | Update `status` field; record the transition event — a Feature has no `status` field to change; its state is derived from its Functionalities |
| Change owner | Feature | Update `owners` field — there are no ownership-change metadata fields; list the Feature's non-`deprecated` User Stories in the change summary so the outgoing owner can hand them over |
| Add a linked User Story | Feature | Append to `user_stories` |
| Add, drop, or promote a dependency | Feature / Functionality | See [Change a Feature's dependencies](#change-a-features-dependencies) — a promotion cascades across every Feature that names the dependency |
| Deprecate a User Story or Functionality | User Story / Functionality | Set `status: deprecated`; add `deprecated_at`, `deprecation_reason`, and optionally `superseded_by` |
| Deprecate a Feature | Feature | Add `deprecation_reason` and optionally `superseded_by` — never set a `status` field, and never author `deprecated_at`; the surface's retirement is recorded through its Functionalities being deprecated, and its state and date are derived from them |
| Delete a Functionality | Functionality | Do not delete — deprecate it, and record the commit that removed the backing code as a `## Notes` bullet |

## Update a User Story — add or modify ACs

When adding a new AC to an existing User Story:

1. Load the existing User Story entity
2. Assign the next sequential AC ID in the canonical `AC:<parent-id>-<nn>` format
   (for example `AC:US-042-04`) - see [living-doc-glossary](../shared/references/living-doc-glossary.md#acceptance-criterion-ac)
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

**AC versioning:** Once an AC is targeted at a version, it carries a `(vMAJOR.MINOR.PATCH - state)` annotation. A backlog AC with no target version yet stays `(planned)` — do not invent a version for it.
- Bump the **minor** version for any business-rule change to an `active` AC (e.g. `v1.0.0 → v1.1.0`).
- Bump the **patch** version for a wording clarification that does not change the rule (e.g. `v1.0.0 → v1.0.1`).
- Deprecating an AC requires a removal note: `(v<version> - deprecated - removal planned v<version>)`.
- The version must appear in the `# AC:` comment in linked Gherkin feature files - trigger `gherkin-living-doc-sync` to propagate the new version into those comments.

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

After promoting a User Story to `active`, trigger `living-doc-scenario-creator` to generate BDD feature files for each `active` AC if they do not yet exist.

## Deprecate a Feature, Functionality, or User Story

Use this workflow when code backing an entity is deleted or a business capability is retired.
Set the relevant fields in the project's Storage Profile format:

| Field | Value | Applies to |
|---|---|---|
| `status` | `deprecated` | Functionality and User Story only — a Feature has no `status` field |
| `deprecated_at` | Date of deprecation | Functionality and User Story only — on a Feature it is **derived** alongside the state, never authored |
| `deprecation_reason` | Why it was deprecated | Feature, Functionality, and User Story |
| `superseded_by` | ID of the replacement entity (if applicable) | Feature, Functionality, and User Story |

Rules:
- Always deprecate — never delete entities (preserves audit trail)
- A Functionality or User Story being deprecated gets `status: deprecated` — never leave it on its prior status while adding deprecation metadata, or it reads as still active
- When the backing code was removed in a commit, record that commit as a **`## Notes` bullet** on
  the entity (feature-file header key `notes:`, issue-body section `## Notes`) — for example
  `- Backing code removed in abc1234 (PR #412).` There is no typed field for it: *deprecated is not
  removed*, and the commit is a pointer to where the removal actually happened, which is context,
  not schema. Do not invent a typed field for it — neither the canon nor `living-doc-utilities`
  defines one, and `validate_entity.py` treats any such key as unrecognised.
- Add `superseded_by` when a replacement entity exists
- A Feature never gets a `status` field, deprecated or otherwise — its state is derived from its Functionalities. Retiring a Feature means deprecating every Functionality it owns; the Feature entity itself only gains `deprecation_reason` / `superseded_by` as a record of why the surface was retired. Its `deprecated_at` is derived with the state, so do not author one — `validate_entity.py` flags a Feature that carries it.
- If a deprecated Feature owns Functionalities, flag every owned Functionality for deprecation review before closing the change.
- Flag any tests linked to the deprecated entity for update or removal
- If the deprecated entity has `ACTIVE` ACs with linked Gherkin scenarios, trigger
  `gherkin-living-doc-sync` to propagate `@deprecated` and `@review-needed` tags to those scenarios
- After `gherkin-living-doc-sync` has tagged the deprecated scenarios, trigger `bdd-maintain`
  REMOVE mode if the automation files for this entity should be deleted from the repository

## Rename a Feature

Changing a Feature's `id` or `name` requires these cascading updates:

1. Update the Feature entity (`id`, `name`, and any self-referencing fields).
2. Update `parent_feature` in every Functionality linked to this Feature.
3. Update the `feature_registry` entry in `catalog.json` (change the `feature_id` key and any path comments).
4. Search `manifest.json` and `seed.yaml` for the old name or ID and update.
5. Search PageObject file headers for the old Feature reference and update.
6. If Gherkin feature files have a `# Feature:` header with the old name, update those headers.
7. Run `living-doc-gap-finder` to confirm no `ORPHAN_FUNCTIONALITY` gaps remain after the rename.

## Update Feature ownership

When a team changes ownership of a Feature, update the `owners` field and nothing else. There are no
ownership-change metadata fields — no canonical layout places one, no contract model holds one, and
an authored `owner_changed_at` or `owner_change_reason` is silently dropped by the pipeline. The
tracked file's git history already records when the transfer happened and why.

A transfer leaves work in flight, so list the Feature's User Stories whose `status` is not
`deprecated` in the change summary. That is the handoff list for the two owners to work through —
this skill edits documentation and sends no messages, so do not claim the new owner was notified.

## Change a Feature's dependencies

Use this when the code behind a Feature starts calling a system, stops calling one, or when a system
it already calls gets documented as a Feature of its own. The job is to leave each call recorded in
the one place the canon puts it:

- A system with **no canonical anchor** is an `external_dependencies` entry on the calling Feature,
  by name — see [living-doc-glossary — Feature](../shared/references/living-doc-glossary.md#feature).
- An **`API` Feature** is a `feature_dependencies` entry on the **Functionality that makes the call** —
  see [living-doc-glossary — Functionality](../shared/references/living-doc-glossary.md#functionality-func).

A Feature's own `feature_dependencies` is **derived** from its Functionalities and never authored.
Never write the field onto a Feature — not to mirror a Functionality, and not as a place to park an
id while the calling Functionality is missing.

### A dependency is added

Record it in the one place above and stop — nothing cascades. Then ask one question: does the new
call bring behaviour that no existing Functionality covers yet? If it does, that is a
`living-doc-create-functionality` request, separate from this change.

### A dependency is dropped

Remove the entry from the list that held it. Then scan `catalog.json`: if no other
`external_dependencies` or `feature_dependencies` list still names it, say so — any test double,
fixture, or `manifest.json` entry standing in for it is now unreferenced. List what you find; this
skill does not delete them.

### A dependency graduates into its own Feature

An `external_dependencies` entry becomes a Feature when the system gains a contract anchor. From that
point the call is an edge to a Feature, and it moves off every Feature that named it:

1. **Confirm the trigger.** The dependency now has a canonical anchor — an annotated endpoint method,
   or a producer/consumer handler carrying an AsyncAPI (or equivalent schema-registry) annotation. If
   it has neither, stop: it stays an `external_dependencies` entry. The anchor rules belong to
   `living-doc-create-feature` — route there to decide, do not restate them here.
2. **Create the Feature** via `living-doc-create-feature`. It assigns the id, the `surface_type`, and
   the `feature_registry` entry in `catalog.json`. Come back with the new `FEAT-<nnn>`.
3. **Find every Feature that names the dependency.** Scan the `external_dependencies` of every Feature
   in `catalog.json`, not only the one the user mentioned. Entries are free-form names: match
   case-insensitively, treat a near miss (`payment-gateway` vs `payments-gateway`) as a question for
   the user rather than an automatic edit, and list what you found before changing anything.
4. **Move each occurrence.** Remove the `external_dependencies` entry from the Feature, and add the new
   `FEAT-<nnn>` to `feature_dependencies` on the Functionality that makes the call — never on the
   Feature, whose value is derived. If the caller has no Functionality describing that call, say so and
   offer `living-doc-create-functionality`; do not invent a Functionality, and do not park the id on
   the Feature.
5. **Leave the Functionalities where they are.** A Functionality describes the behaviour of the Feature
   that owns it, not of the system it calls, so the promotion never re-parents one. Flag the
   Functionalities whose tests stubbed the dependency for test review — they can now test against a
   documented contract.
6. **Expect the new Feature to be an orphan.** It owns no Functionalities yet, so
   `living-doc-gap-finder` reports `ORPHAN_FEATURE`, and its derived state is `planned` until its first
   Functionality is documented. Report that; do not invent placeholder Functionalities to silence it.
7. **Validate** the new Feature and every edited entity:
   `python scripts/validate_entity.py <entity>.json --catalog catalog.json`. With the catalog, the
   validator checks each `feature_dependencies` target exists, is an `API` Feature, is not deprecated,
   and is not the Functionality's own Feature.
8. **Emit the change summary** — the new Feature id, every entity the entry moved on, and the
   Functionalities flagged for test review:

```
LIVING DOC UPDATE — 2026-09-29
  Promoted: payment-events → FEAT-007 Payment Events API (surface_type: API)
  Changes:
    - FEAT-001 Checkout Page    external_dependencies: removed payment-events
    + FUNC-003                  feature_dependencies: added FEAT-007
    - FEAT-002 Orders API       external_dependencies: removed payment-events
    + FUNC-005                  feature_dependencies: added FEAT-007
  Flagged for test review (stubbed payment-events):
    FUNC-003, FUNC-005
  Downstream flags:
    FEAT-007 is ORPHAN_FEATURE and derives as planned until its first Functionality is documented
```

## Descope an AC mid-sprint

There is no `descoped` state. When an AC is moved out of the current sprint but not permanently
removed, it keeps its `planned` state and gains no extra fields — do not delete the AC (preserves
audit trail and reinstating intent):

- Drop the target version so the AC reads `AC:<id> (planned)` - backlog, agreed, no target version yet
- Record why on the AC's `- Rationale:` bullet
- Flag any linked Gherkin scenarios for `@wip` + `@review-needed` tagging via `gherkin-living-doc-sync`

For **business-rule changes to an active AC**, first show the AC side-by-side for confirmation, then apply the version bump:

```
OLD: AC:US-042-01 (v1.0.0 - active) - Minimum order value is £50.
NEW: AC:US-042-01 (v1.1.0 - active) - Minimum order value is £75.
```

For an AC **descoped** out of the current release (was targeting `v1.2.0`, no longer is):

```
OLD: AC:US-042-03 (v1.2.0 - planned)
       - Promo codes can be stacked and applied in defined priority order.
NEW: AC:US-042-03 (planned)
       - Promo codes can be stacked and applied in defined priority order.
       - Rationale: Promo stacking rule deferred - too complex for current sprint; reinstate when re-prioritised.
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
referential integrity against the full catalog — including every `feature_dependencies` edge:
the target exists, is an `API` Feature, is not deprecated, and is not the Functionality's own
Feature. Without `--catalog` it reports none of those four and says the basis is unavailable.

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
    + Added AC AC:US-042-04 (planned) - Promo code expired returns 422 with error message
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
    + Added AC AC:US-089-04 (planned)
      GIVEN a customer enters an address outside the shipping zone
      WHEN they place the order
      THEN the order is blocked with SHIPPING_ZONE_EXCLUDED and a clear message
  Downstream flags:
    Run gherkin-living-doc-sync
```
