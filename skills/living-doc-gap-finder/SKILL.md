---
name: living-doc-gap-finder
description: >
  Identify gaps in the living documentation by combining bottom-up UI/code exploration with
  top-down requirement checking. Activate when auditing living doc completeness, finding
  undocumented behaviors, discovering orphan tests with no AC link, detecting untested ACs,
  producing a documentation coverage gap report, or proposing new living doc entities to fill
  identified gaps. Orchestrates living-doc-pageobject-scan, living-doc-scenario-creator (read-only),
  and living-doc-create-* skills.
  Triggers on: "find what's not documented", "living doc gaps", "what's missing in living doc",
  "find undocumented features", "orphan tests", "untested AC", "documentation coverage",
  "gap report", "what's not covered", "living doc audit", "documentation audit".
  Does NOT trigger for: creating new living doc objects (use living-doc-create-* skills),
  generating tutorials (use living-doc-tutorial-creator).
  Orchestrates: living-doc-pageobject-scan, living-doc-scenario-creator, and all create-* skills.
license: Apache-2.0
compatibility: GitHub Copilot
---

# Living Doc — Gap Finder

> **Key concepts:** Feature, Functionality, User Story, AC, PageObject — see `../references/living-doc-glossary.md`.

## Gap taxonomy

Five types of gaps are detected, in order of risk:

| Priority | Gap type | Description |
|---|---|---|
| 1 — Blocker | **Untested AC** | An Active or Implemented AC in a User Story or Functionality has no linked test |
| 2 — Important | **Undocumented UI surface** | A screen or API endpoint exists in the app with no Feature entity |
| 3 — Important | **Orphan Feature** | A Feature entity exists with no linked User Story |
| 4 — Important | **Orphan test** | A test or BDD scenario exists with no linked AC |
| 5 — Nit | **Undocumented Functionality** | A Functionality entity exists with no associated tests |

## Workflow

### Step 1 — Bottom-up scan (apply living-doc-pageobject-scan)

Load and follow the `living-doc-pageobject-scan` skill to build an **inventory** of:
- All discoverable UI screens and API endpoints
- All existing test files and BDD scenarios
- All existing PageObjects and their method coverage

Output: `inventory.json` — a flat list of discovered artifacts.

### Step 2 — Top-down entity traversal

Traverse the entity graph by following relationship fields:
- All User Stories (with their ACs and status) — the root entry points
- All Features (via User Story `features` links)
- All Functionalities (via Feature `functionalities` links)
- All existing test links (test file → AC mappings)

### Step 3 — Compute gaps

For each gap type:

**Gap type 1 — Untested AC:**
```
For each AC in (UserStory.ACs + Functionality.ACs)
  where status IN (Active, Implemented)
  where no linked test exists:
    → GAP: UNTESTED_AC
```

**Gap type 2 — Undocumented UI surface:**
```
For each item in inventory (screens, API endpoints)
  where no Feature entity exists for this surface:
    → GAP: UNDOCUMENTED_SURFACE
```

**Gap type 3 — Orphan Feature:**
```
For each Feature reachable via entity relationships
  where user_stories == [] AND functionalities == []:
    → GAP: ORPHAN_FEATURE
```

**Gap type 4 — Orphan test:**
```
For each test in inventory
  where no linked AC exists in any UserStory or Functionality:
    → GAP: ORPHAN_TEST
```

**Gap type 5 — Undocumented Functionality:**
```
For each Functionality reachable via Feature `functionalities` links
  where no test references this Functionality's ACs:
    → GAP: UNDOCUMENTED_FUNCTIONALITY
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
| UNTESTED_AC | Create BDD scenario → `living-doc-scenario-creator` |
| UNDOCUMENTED_SURFACE | Create Feature entity → `living-doc-create-feature` |
| ORPHAN_FEATURE | Link to a User Story or delete if not used |
| ORPHAN_TEST | Link test to an existing AC, or create a Functionality → `living-doc-create-functionality`. **Never delete a test to resolve an orphan — that would silently remove coverage.** If the linked AC ID no longer exists (broken link), choose from: (1) recreate the AC/Functionality if the behavior is still required; (2) update the link to the merged AC ID if the entity was merged; (3) delete the test only after product owner confirmation that the behavior has been intentionally removed. |
| UNDOCUMENTED_FUNCTIONALITY | Create unit/integration tests for the Functionality's ACs |

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
      "proposed_action": "Generate BDD scenario using living-doc-scenario-creator for US-007"
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
Instead:

1. **Batch by domain or Feature area** — process one Feature or service at a time.
2. **Prioritise by business risk** — start with the highest-risk domains first: payment, auth,
   security, regulatory compliance. These gaps pose the greatest production risk.
3. **Iterate** — after each batch, link tests, create entities, and re-run gap-finder on that
   domain before moving to the next.

Processing everything at once is discouraged because the resulting gap list is too large to action
without clear prioritisation.

## Lightweight scenario-coverage report format

When the focus is specifically on scenario-to-AC coverage (rather than the full gap taxonomy),
or when asked to demonstrate or describe the gap report output format,
use this simplified two-section format:

**Missing Scenarios** (ACs with no linked Gherkin scenario):
- `<AC-ID>` — <description>

**Missing ACs** (Gherkin scenarios with no corresponding AC):
- `<scenario title>` — <feature file>

End with a summary line: `X ACs missing scenarios, Y scenarios missing ACs.`

This format is diagnostic only — it does not suggest implementation changes.
