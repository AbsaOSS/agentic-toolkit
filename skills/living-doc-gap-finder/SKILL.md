---
name: living-doc-gap-finder
description: >
  Identify gaps in the living documentation by combining bottom-up UI/code exploration with
  top-down requirement checking. Activate when auditing living doc completeness, finding
  undocumented behaviors, discovering orphan tests with no AC link, orphan Functionalities with
  no parent Feature, detecting untested ACs, producing a documentation coverage gap report
  (including batch runs for large suites), or proposing new living doc entities to fill
  identified gaps. Orchestrates living-doc-pageobject-scan and living-doc-create-* skills.
  Triggers on: "find what's not documented", "living doc gaps", "what's missing in living doc",
  "find undocumented features", "orphan tests", "orphan functionalities", "untested AC",
  "documentation coverage", "gap report", "what's not covered", "living doc audit",
  "documentation audit".
  Does NOT trigger for: creating new living doc objects (use living-doc-create-* skills).
  Orchestrates: living-doc-pageobject-scan, living-doc-scenario-creator, and all create-* skills.
license: Apache-2.0
compatibility: GitHub Copilot
---

# Living Doc — Gap Finder

> **Key concepts:** Feature, Functionality, User Story, AC — see [living-doc-glossary](../references/living-doc-glossary.md) ([remote](https://github.com/AbsaOSS/agentic-toolkit/blob/master/skills/references/living-doc-glossary.md)).

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
- Report documentation coverage **separately** for User Story ACs and Functionality ACs, even if the raw script output gives a combined number.
- For `UNDOCUMENTED_SURFACE`, treat a discovered screen/API as already documented when an existing Feature clearly owns the same surface by path, name, or domain meaning (for example `/account/orders` ↔ `Account Dashboard`, `/reports/legacy` ↔ `Legacy Report Screen`). Only raise `UNDOCUMENTED_SURFACE` when no plausible owning Feature exists.
- **Always refer to gap types by their name** (e.g. `ORPHAN_TEST`, `UNTESTED_AC`) — never by an ordinal number (e.g. "Gap type 6"). The priority order below is for triage, not for labelling gaps in the report.

---

## Gap taxonomy

Nine types of gaps are detected, in order of risk:

| Priority | Gap type | Description |
|---|---|---|
| 1 — Blocker | **Untested AC** | An Active or Implemented AC in a User Story or Functionality has no linked test. |
| 2 — Important | **Undocumented UI surface** | A screen or API endpoint exists in the app with no Feature entity |
| 3 — Important | **Orphan Feature** | A Feature entity exists with no linked User Story |
| 4 — Important | **Orphan User Story** | A User Story exists with no linked Feature |
| 5 — Important | **Orphan Functionality** | A Functionality exists with no parent Feature |
| 6 — Important | **Orphan test** | A test exists with no linked AC |
| 7 — Important | **Stale reference** | An active test references a Deprecated AC |
| 8 — Nit | **Undocumented Functionality** | A Functionality entity exists with no associated tests |
| 9 — Nit | **Empty Feature** | A Feature entity exists with no Functionalities defined |

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
  where status IN (Active, Implemented)
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
  where user_story.features == []:
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

**UNDOCUMENTED_FUNCTIONALITY:**
```
For each Functionality reachable via Feature `functionalities` links
  where no test references this Functionality's ACs:
    GAP: UNDOCUMENTED_FUNCTIONALITY
```

**EMPTY_FEATURE:**
```
For each Feature reachable via entity relationships
  where functionalities == []:
    GAP: EMPTY_FEATURE
```

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
| STALE_REFERENCE | Update the test to reference the active replacement AC. If the deprecated behavior was intentionally removed, delete the test after product owner confirmation. If removed in error, reinstate the AC using `living-doc-update`. |
| UNDOCUMENTED_FUNCTIONALITY | Create unit/integration tests for the Functionality's ACs |
| EMPTY_FEATURE | Create Functionalities for the Feature's known behaviors — `living-doc-create-functionality` |

> **Out-of-scope actions:** living-doc-gap-finder identifies and proposes new entities — it does
> not create them. Direct creation requests (e.g. "create a User Story", "create a Feature") must
> be delegated to the appropriate skill: `living-doc-create-user-story`, `living-doc-create-feature`,
> or `living-doc-create-functionality`.

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

A project with 100% documentation coverage has every AC backed by at least one test.

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
