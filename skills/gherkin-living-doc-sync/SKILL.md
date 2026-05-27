---
name: gherkin-living-doc-sync
description: >
  Synchronise Gherkin feature files and BDD scenarios with the living documentation catalog.
  Activate when scenarios diverge from User Story ACs, step text drifts after a refactor,
  `@AC:` tag or `# AC:` comment annotations are missing or stale, descoped ACs need their
  linked scenarios updated, or AC changes must propagate from the living doc back to feature
  files. Run scan_ac_links.py to audit AC link health before a sync pass.
  Distinct from gap-finder (which detects missing coverage) — corrects existing links.
  Triggers on: "sync gherkin to living doc", "feature file out of sync", "scenario not linked
  to AC", "step text changed", "gherkin drift", "BDD sync", "AC link missing in feature file",
  "sync scenarios", "traceability broken", "propagate AC changes", "AC was descoped".
  Does NOT trigger for: writing new scenarios (use gherkin-scenario), implementing step
  definitions (use gherkin-step), finding living doc gaps (use living-doc-gap-finder),
  creating new US/Feature entities (use living-doc-create-user-story).
---

# Gherkin ↔ Living Doc Sync

> **Glossary:** Feature, Functionality, User Story, AC — see [living-doc-glossary](../references/living-doc-glossary.md) ([remote](https://github.com/AbsaOSS/agentic-toolkit/blob/master/skills/references/living-doc-glossary.md)).

Sync runs in three directions: (1) feature file to living doc, (2) living doc AC to feature file,
(3) step text to PageObject method signature.

Use `scripts/scan_ac_links.py` to detect missing or malformed `@AC:` tags and missing `# AC:`
comments before a full sync run. The script only checks living-doc feature files (`features/us/`
and `features/functionalities/`) — other feature files are skipped.

---

## Step 1 — Detect the sync direction

**Upstream dependencies:** Directions that flow from the living documentation into feature files are initiated by catalog-layer operations from `@living-doc-copilot`:
- `living-doc-update` modified, added, or deprecated an AC → triggers directions 2 and 4 below
- `living-doc-impact-analysis` identified High-impact AC changes that require resync → may trigger directions 2 and 3

| Change event | Sync direction | Action |
|---|---|---|
| New `.feature` file added | Feature file to living doc | Link each scenario to an AC; create AC if missing |
| User Story AC modified or added | Living doc to feature file | Update or add the corresponding scenario |
| UI refactored (selector / method renamed) | Step text to PageObject | Update step text; re-link to PageObject method |
| US deprecated | Living doc to feature file | Emit one sync action per linked scenario; add `@deprecated`, record the reason, and flag `@review-needed` |
| Scenario added without an `@AC:` tag | Feature file to living doc | Propose an AC and add the `@AC:` tag |

---

## Step 2 — Audit `@AC:` traceability tags

**Required traceability format** for living-doc feature files (from the glossary):

```gherkin
# AC:US-1-01 (v1.0.0 - Active) — customer places an order with a saved payment method
@AC:US-1-01
Scenario: Customer successfully places an order
```

With aspect param — when the scenario covers only one aspect of a multi-aspect AC:

```gherkin
# AC:US-1-01 (v1.0.0 - Active) — displays {required field} on login screen | aspect: username input
@AC:US-1-01/aspect:username-input
Scenario: Login form shows the username input field
```

- `# AC:` comment: human-readable context — ID, version, state, description, optional aspect.
- `@AC:` Cucumber tag: `@AC:<id>[/param:value...]` — machine-readable link. The `/param:value` format is extensible.
- The `@AC:` tag(s) must appear on the lines immediately above `Scenario:` or `Scenario Outline:`. Additional tags (e.g. `@Regression`, `@skip`) may appear in the same block.
- Full AC details (version, state, description) live in the file's `# Acceptance Criteria:` header block.

**Audit checklist:**
1. Does every `Scenario:` / `Scenario Outline:` in living-doc files have at least one `@AC:` tag?
2. Is the corresponding `# AC:` comment present and matching the tag's AC ID?
3. Does the referenced AC ID exist in the living documentation?
4. Does the AC state match (`Active` or `Implemented` — not `Deprecated` or `Planned`)?
5. Does the AC description (in the file header) match the scenario intent?

For each missing or mismatched tag:

```
SYNC ACTION: checkout.feature:14
  Scenario: "Customer successfully places an order"
  Missing @AC: tag
  Proposed tag: @AC:US-001-01
  Confirm or select a different AC
```

## Step 3 — Detect step text drift

When step text changes after a UI refactor, the step definition binding breaks:

```
DRIFT DETECTED: checkout.feature:17
  Step: "When the customer clicks the Confirm Purchase button"
  No matching step definition found
  Previous match: "When the customer confirms the order" (checkout_steps.py:34)
  PageObject method: CheckoutPage.confirm_order()
  Suggested fix: update step text to "When the customer confirms the order"
    OR update the step definition regex to match the new wording
```

---

## Step 4 — Apply sync changes

Apply the minimum necessary change per action:

- **Add missing `@AC:` tag**: insert `@AC:<id>` above `Scenario:`
- **Update stale AC reference**: update the file header's `# Acceptance Criteria:` block entry; the `@AC:` tag on the scenario stays unchanged. Show the exact change as `OLD:` and `NEW:` lines. If the revised AC intent changed materially, flag the linked step text for review instead of restructuring the scenario in the same sync action.
- **Update scenario to match revised AC**: update step text; keep the `@AC:` tag unchanged
- **Fix broken step text**: prefer updating the `.feature` file to match the existing step definition and PageObject method; only update the step definition regex when the business wording genuinely changed
- **Mark deprecated scenarios**: add `@deprecated` and `@review-needed`, plus a comment with the date and reason. Emit one action per affected scenario with file and line number.
- **Mark descoped scenarios**: add `@wip` or `@pending` and `@review-needed`, plus a comment with the descope reason and target-release reference. Preserve the scenario — never delete it — so it can be reinstated when the AC is promoted back to Active. Emit one SYNC ACTION per affected scenario.
- **Broken AC reference**: never silently remove the `@AC:` tag. Either relink it to the correct AC ID, or create the missing living doc entity with `living-doc-create-user-story` / `living-doc-create-functionality`, then update the tag.
- **AC split into multiple ACs**: update the existing scenario's `@AC:` tag to the primary AC; create new scenarios for additional ACs

Never delete a scenario during sync — flag it with `@review-needed` for developer decision.

---

## Step 5 — Output sync report

Do **not** apply sync changes automatically. Report `DRIFT DETECTED` blocks first (tests fail), then `SYNC ACTION` blocks (traceability), and ask the developer to confirm each action before editing files.

```
DRIFT DETECTED: checkout.feature:17
  Step: "When the customer clicks the Confirm Purchase button"
  No matching step definition found
  Previous match: "When the customer confirms the order" (checkout_steps.py:34)
  PageObject method: CheckoutPage.confirm_order()
  Recommended fix: update the feature file step text to match the existing step definition
    OR update the step definition regex to match the new wording
  Apply change? (y/n)

SYNC ACTION: checkout.feature:14
  Scenario: "Customer successfully places an order"
  Missing @AC: tag
  Proposed tag: @AC:US-001-01
  Apply change? (y/n)

SYNC ACTION: checkout.feature:32
  Scenario: "Customer reviews order totals before payment"
  Missing @AC: tag
  Proposed tag: @AC:US-001-02
  Apply change? (y/n)

Summary: 2 missing AC links, 1 step text drift detected — apply changes? (y/n per action)
```

---

## Anti-patterns to flag

| Anti-pattern | Flag |
|---|---|
| Scenario with no `@AC:` tag | Missing traceability — add tag or create AC |
| Two scenarios linked to the same AC | Usually a duplicate — review |
| AC linked from a scenario in a different User Story's feature file | Passive cross-US coverage — permitted but note it in the sync report. Only flag if the scenario's primary intent belongs to a different User Story (misplaced scenario) |
| Step text describes implementation (selector, endpoint) | Gherkin business-language violation — refer to `gherkin-scenario` |

---

## Out-of-scope routing

| Request | Use instead |
|---|---|
| Writing new Gherkin scenarios from scratch | `gherkin-scenario` |
| Implementing step definition code | `gherkin-step` |
| Finding ACs with no scenario coverage | `living-doc-gap-finder` |
| Creating new User Story, Feature, or Functionality entities | `living-doc-create-user-story` / `living-doc-create-functionality` |
