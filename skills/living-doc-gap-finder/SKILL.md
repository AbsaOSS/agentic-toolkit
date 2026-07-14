---
name: living-doc-gap-finder
description: >
  Identify gaps in the living documentation by combining bottom-up and top-down analysis.
  Use when auditing living doc completeness, finding undocumented behaviors, orphan tests,
  orphan Functionalities, untested ACs, or producing a documentation coverage gap report.
  Proposes actions executed by living-doc-create-*, living-doc-scenario-creator, and
  living-doc-update. Re-run after entity creation or status changes to confirm gaps are closed.
  Triggers on: "find what's not documented", "living doc gaps", "what's missing in living doc",
  "find undocumented features", "orphan tests", "orphan functionalities", "untested AC",
  "documentation coverage", "gap report", "what's not covered", "living doc audit",
  "documentation audit", "stale reference", "broken AC link", "test points to deprecated AC",
  "PLAN mode", "AUDIT mode", "draft ACs from PageObject descriptions".
  Does NOT trigger for: creating new living doc objects (use living-doc-create-* skills).
  Pairs with living-doc-update and living-doc-create-* skills.
license: Apache-2.0
compatibility: GitHub Copilot
---

# Living Doc — Gap Finder

> **Key concepts:** Feature, Functionality, User Story, AC — see [living-doc-glossary](../../shared/references/living-doc-glossary.md) ([remote](https://github.com/AbsaOSS/agentic-toolkit/blob/master/skills/shared/references/living-doc-glossary.md)).

## Script — `scripts/compute_gaps.py`

Run this script to compute all 9 gap types deterministically before producing the gap report.
It takes a catalog snapshot JSON as input and outputs the `gaps[]` array and coverage stats.

```bash
# Human-readable summary
python scripts/compute_gaps.py catalog-snapshot.json --summary

# Machine-readable report
python scripts/compute_gaps.py catalog-snapshot.json --output gap-report.json
```

The catalog must contain `catalog`, `inventory`, and `known_test_links` sections —
see `evals/files/catalog-snapshot.json` for a worked example.

Run the script first, then use its output to drive the Prioritise and Propose steps below.
The Workflow section describes the logic the script encodes — read it for understanding, but
delegate the computation to the script rather than reproducing it through reasoning.

Before presenting the final report, normalise the script output against the taxonomy in this skill:
- The first gap type (`UNTESTED_AC`) applies to **both User Story ACs and Functionality ACs**. If a Functionality has ACs and no linked tests, report those ACs as `UNTESTED_AC` **Blockers** (you may summarise as `FUNC-xyz has N ACs with no linked tests`) and do **not** leave the same root cause only as `UNDOCUMENTED_FUNCTIONALITY`.
- Do **not** duplicate the same Functionality root cause as both `UNTESTED_AC` and `UNDOCUMENTED_FUNCTIONALITY` in one report. For example: `FUNC-apply-discount has 5 ACs with no linked tests` belongs under `UNTESTED_AC` only.
- Report documentation coverage **separately** for User Story ACs and Functionality ACs, even if the raw script output gives a combined number.
- For `UNDOCUMENTED_SURFACE`, treat a discovered screen/API as already documented when an existing Feature clearly owns the same surface by path, name, or domain meaning (for example `/account/orders` ↔ `Account Dashboard`, `/reports/legacy` ↔ `Legacy Report Screen`). Only raise `UNDOCUMENTED_SURFACE` when no plausible owning Feature exists.
- **Always refer to gap types by their name** (e.g. `ORPHAN_TEST`, `UNTESTED_AC`) — never by an ordinal number (e.g. "Gap type 6"). The priority order below is for triage, not for labelling gaps in the report.
- When a User Story has an empty `features` list, report a separate `ORPHAN_USER_STORY` finding even if other gaps already mention the same story.

---

## Mode names

| Mode | When to use |
|---|---|
| **AUDIT mode** | Full catalog audit — runs the 9-type taxonomy top-down across all entities. Use after a sprint with entity changes or when the living doc hasn’t been reviewed recently. |
| **PLAN mode** | Bootstrap new coverage — draft ACs from PageObject descriptions or discovered UI surfaces (bottom-up). Produces `PLANNED`-state AC drafts for user confirmation before creating entities. |

Both modes use `compute_gaps.py` and the same gap taxonomy. AUDIT mode spans the full catalog; PLAN mode is scoped to the surfaces being bootstrapped.

---

## Gap taxonomy

Nine types of gaps are detected, in order of risk:

| Priority | Gap type | Description |
|---|---|---|
| 1 — Blocker | **Untested AC** | An `ACTIVE` AC in a User Story or Functionality has no linked test. |
| 2 — Important | **Undocumented UI surface** | A screen or API endpoint exists in the app with no Feature entity |
| 3 — Important | **Orphan Feature** | A Feature entity exists with no linked User Story |
| 4 — Important | **Orphan User Story** | A User Story exists with no linked Feature |
| 5 — Important | **Orphan Functionality** | A Functionality exists with no parent Feature |
| 6 — Important | **Orphan test** | A test exists with no linked AC |
| 7 — Important | **Stale reference** | An active test references a Deprecated AC |
| 8 — Nit | **Undocumented Functionality** | A Functionality entity exists with no associated tests |
| 9 — Nit | **Empty Feature** | A Feature entity exists with no Functionalities defined |

> **Resolution routing:** `UNTESTED_AC` → `living-doc-scenario-creator`; `UNDOCUMENTED_SURFACE` / `ORPHAN_FUNCTIONALITY` / `EMPTY_FEATURE` → `living-doc-create-*`; `ORPHAN_FEATURE` / `ORPHAN_USER_STORY` → `living-doc-update` (add missing link); `ORPHAN_TEST` → `gherkin-living-doc-sync`; **`STALE_REFERENCE`** → `living-doc-update` (deprecate the AC or update the test `@AC:` tag); `UNDOCUMENTED_FUNCTIONALITY` → `living-doc-scenario-creator`.

> **ORPHAN_TEST — never delete a test to resolve the gap.** Deleting a test removes coverage; it does not close the gap — it masks it. Instead: (1) find an existing AC that matches the test's intent and add the `@AC:` link, or (2) if no AC exists, create a Functionality with `living-doc-create-functionality` and link the test to the new AC. Only delete a test after explicit product owner confirmation that the behavior is no longer required.

> **ORPHAN_TEST — broken-link variant:** A test may reference an AC that was deleted from the catalog entirely (not merely deprecated). Classify this as `ORPHAN_TEST` (broken-link variant) — not `STALE_REFERENCE`. Resolution options: (1) recreate the entity if the behavior is still required and relink; (2) update the test link to the AC that superseded it; (3) delete the test after product owner confirmation. Never delete without confirmation.

> **Large-scale ORPHAN_TEST remediation:** When a codebase has dozens or hundreds of orphan tests, do not attempt a single full-codebase pass. Batch by domain or Feature area (for example payment, auth, reporting) and process the highest-business-risk areas first. For each batch, identify which Functionalities or User Stories the tests correspond to, create missing entities, and link tests. A single unmanageable gap report leads to paralysis — smaller focused batches produce actionable outcomes.

## Workflow

### Step 1 — Bottom-up scan

Build an **inventory** of:
- All discoverable UI screens and API endpoints
- All existing test files

Output: `inventory.json` — a flat list of discovered artifacts.

### Step 2 — Top-down entity traversal

Traverse the entity graph top-down, starting from User Stories as roots:

- **User Stories** (root) — load all entities with their ACs and status
- **Features** — for each User Story, follow its `features` list to reach linked Features
- **Functionalities** — for each Feature, follow its `functionalities` list to reach owned Functionalities
- **Test links** — collect all test file to AC mappings for cross-referencing in Step 3

### Step 3 — Compute gaps

For each gap type:

**UNTESTED_AC:**
```
For each AC in (UserStory.ACs + Functionality.ACs)
  where status == ACTIVE
  where no linked test exists:
    GAP: UNTESTED_AC
```

**UNDOCUMENTED_SURFACE:**
```
For each item in inventory (screens, API endpoints)
  where no Feature entity exists for this surface:
    GAP: UNDOCUMENTED_SURFACE
```

**ORPHAN_FEATURE:**
```
For each Feature reachable via entity relationships
  where user_stories == []:
    GAP: ORPHAN_FEATURE
```

**ORPHAN_USER_STORY:**
```
For each User Story in entity graph
  where user_story.features is missing OR user_story.features == []:
    GAP: ORPHAN_USER_STORY
```

**ORPHAN_FUNCTIONALITY:**
```
For each Functionality in entity graph
  where functionality.parent_feature == null:
    GAP: ORPHAN_FUNCTIONALITY
```

**ORPHAN_TEST:**
```
For each test in inventory
  where no linked AC exists in any UserStory or Functionality:
    GAP: ORPHAN_TEST
```

**STALE_REFERENCE:**
```
For each test in inventory
  where linked_ac.status == Deprecated:
    GAP: STALE_REFERENCE
```

**ORPHAN_TEST — broken-link variant:**
Also report `ORPHAN_TEST` when a test references an AC ID that **no longer exists** in the catalog (deleted, not merely deprecated). Distinguishing the two: a deprecated AC still has a living entity and can be reinstated; a deleted AC has no catalog entry at all. Resolution options are the same as standard `ORPHAN_TEST` — see the resolution routing note above.

**UNDOCUMENTED_FUNCTIONALITY:**
```
For each Functionality reachable via Feature `functionalities` links
  where no test references this Functionality's ACs:
    GAP: UNDOCUMENTED_FUNCTIONALITY
```

**EMPTY_FEATURE:**
```
For each Feature reachable via entity relationships
  where functionalities is missing OR functionalities == []:
    GAP: EMPTY_FEATURE
```

`EMPTY_FEATURE` is independent of whether the Feature has linked User Stories. A Feature with linked User Stories but no Functionalities (for example `FEAT-account`) is still an `EMPTY_FEATURE`.

### Step 4 — Prioritise by risk

Sort all gaps by:
1. Priority (Blocker before Important before Nit)
2. Within priority: by the number of dependent entities (higher impact first)
3. Within that: alphabetically by entity ID

### Step 5 — Propose new entities

For each gap, propose the living doc action:

| Gap type | Proposed action |
|---|---|
| UNTESTED_AC | Create a test for the uncovered AC — use `living-doc-create-functionality` to define the behavior if not yet documented |
| UNDOCUMENTED_SURFACE | Create Feature entity — `living-doc-create-feature` |
| ORPHAN_FEATURE | (1) Confirm the Feature entity actually exists in the storage profile — a broken reference may mean the Feature was renamed or deleted without updating the link. (2) If the Feature exists: link it to an existing User Story or propose creating one. (3) If deletion is the right action: **always confirm with the user before deleting** — state the Feature ID, name, and any Functionalities it owns, and ask explicitly: *"No User Story references FEAT-nnn. Delete this Feature and its N Functionalities?"* |
| ORPHAN_USER_STORY | Link to an existing Feature, or create the missing Feature — `living-doc-create-feature` |
| ORPHAN_FUNCTIONALITY | Link to an existing Feature, or delete if the behavior has no owning surface. Do not delete if tests reference this Functionality's ACs — resolve those first (see ORPHAN_TEST). |
| ORPHAN_TEST | Link test to an existing AC, or create a Functionality — `living-doc-create-functionality`. **Never delete a test to resolve an orphan — that would silently remove coverage.** If the linked AC ID no longer exists (broken link), choose from: (1) recreate the AC/Functionality if the behavior is still required; (2) update the link to the merged AC ID if the entity was merged; (3) delete the test only after product owner confirmation that the behavior has been intentionally removed. |
| STALE_REFERENCE | Use `living-doc-update` to manage the AC state first: reinstate the AC if the deprecation was in error, or confirm the deprecation is intentional. Then update the test to reference the active replacement AC, or delete the test after product owner confirmation if the behavior has been intentionally retired. |
| UNDOCUMENTED_FUNCTIONALITY | Create unit/integration tests for the Functionality's ACs |
| EMPTY_FEATURE | Create Functionalities for the Feature's known behaviors — `living-doc-create-functionality` |

## Out-of-scope routing

| Request | Correct skill |
|---|---|
| Create a User Story | `living-doc-create-user-story` |
| Create a Feature | `living-doc-create-feature` |
| Create a Functionality | `living-doc-create-functionality` |
| Update or deprecate an entity / AC | `living-doc-update` |
| Generate BDD scenarios | `living-doc-scenario-creator` |

Living-doc-gap-finder identifies and proposes — it does not create or edit entities.

### Step 6 — Output gap report

```json
{
  "generated_at": "2026-05-15T10:00:00Z",
  "documentation_coverage": {
    "user_stories_with_full_coverage": 12,
    "user_stories_with_gaps": 3,
    "coverage_percentage": 80
  },
  "gaps": [
    {
      "id": "GAP-001",
      "type": "UNTESTED_AC",
      "severity": "Blocker",
      "entity": "AC:US-007-02",
      "description": "Active AC 'Payment declined' has no linked E2E test",
      "proposed_action": "Create a test to cover AC:US-007-02 for US-007"
    },
    {
      "id": "GAP-002",
      "type": "UNDOCUMENTED_SURFACE",
      "severity": "Important",
      "entity": "/account/preferences",
      "description": "Screen /account/preferences discovered in webapp scan — no Feature entity",
      "proposed_action": "Create Feature entity using living-doc-create-feature"
    }
  ]
}
```

## Documentation coverage metric

```
Coverage % = (ACs with at least one linked test) / (total ACs) × 100
```

Report separately for:
- User Story ACs (E2E coverage)
- Functionality ACs (unit/integration coverage)
- Overall AC coverage may be shown as an extra summary line, but it does **not** replace the separate User Story and Functionality coverage lines.

A project with 100% documentation coverage has every AC backed by at least one test.

**Classification reminders for final reports:**
- If `US-007.features == []`, emit `ORPHAN_USER_STORY — US-007 has no linked Feature entity`.
- If `FEAT-account.functionalities == []`, emit `EMPTY_FEATURE — FEAT-account has no Functionalities defined`.
- If `FEAT-orphan.functionalities == []`, emit `EMPTY_FEATURE — FEAT-orphan has no Functionalities defined`.
- If `FUNC-apply-discount` has ACs but no linked tests, list it only once under `UNTESTED_AC` Blockers — not again under `UNDOCUMENTED_FUNCTIONALITY`.
- If a `.feature` file itself has no `@AC:` tag **and** one of its scenarios is also independently unlinked, report both orphan-test artifacts separately (for example `test_login_flow.feature` and `View paginated order history`).
- Do not infer `EMPTY_FEATURE` from lack of User Stories; only emit it when `functionalities == []`. In the worked snapshot, `FEAT-promo` is an orphan Feature, while `FEAT-account` and `FEAT-orphan` are the empty Features.

## Large-scale analysis: batching guidance

When the gap inventory is large (e.g. 100+ orphan tests or undocumented features from a legacy
codebase), running a single full-codebase gap-finder pass produces an unmanageable report.
Use the following two-phase strategy:

### Phase 1 — Baseline: ensure every User Story has at least one covered AC

Before addressing any other gap type, guarantee minimum traceability across all User Stories:

1. List all User Stories where **zero ACs** have a linked test.
2. For each, identify the highest-priority AC (first Active AC, or the first AC if none is Active).
3. Create one test for that AC using the appropriate testing workflow.
4. Repeat until every User Story has at least one covered AC.

This phase establishes a baseline coverage floor. Do not skip to Phase 2 until all User Stories
have at least one covered AC.

### Phase 2 — Depth: address gaps in order of size

Once the baseline is met, continue by tackling the biggest remaining gaps first:

1. **Rank gap clusters by count** — group all remaining gaps by type and sort descending by number of affected entities.
2. **Start with the highest-risk domain first** — payment, auth, security, or other release-critical areas take priority over lower-risk domains, even before broad legacy clean-up.
3. **Batch by domain** — within a cluster, process one Feature or service at a time.
4. **Iterate** — after each batch, re-run gap-finder on that domain before moving to the next.

Processing everything at once is discouraged because the resulting gap list is too large to action
without clear prioritisation.

## Lightweight coverage report format

When the focus is specifically on test-to-AC coverage (rather than the full gap taxonomy),
or when asked to demonstrate or describe the gap report output format,
use this simplified two-section format:

**Missing Tests** (ACs with no linked test):
- `<AC-ID>` — <description>

**Orphan Tests** (tests with no corresponding AC):
- `<test name>` — <file>

End with a summary line: `X ACs missing tests, Y tests missing ACs.`

This format is diagnostic only — it does not suggest implementation changes.
