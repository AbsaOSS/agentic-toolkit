---
name: gherkin-living-doc-sync
description: >
  Synchronise Gherkin feature files and BDD scenarios with the living documentation catalog.
  Activate when scenarios diverge from User Story ACs, when step text drifts after a UI
  refactor, when AC link headers or # AC: comment annotations are missing or stale, or when
  propagating AC changes from the living doc back to feature files. Distinct from gap-finder
  (which detects missing coverage) — corrects existing links.
  Triggers on: "sync gherkin to living doc", "feature file out of sync", "scenario not linked
  to AC", "step text changed", "gherkin drift", "update living doc after BDD change",
  "BDD sync", "AC link missing in feature file", "sync scenarios",
  "gherkin out of sync with living doc", "traceability broken", "propagate AC changes".
  Does NOT trigger for: writing new scenarios (use gherkin-scenario), implementing step
  definitions (use gherkin-step), finding living doc gaps (use living-doc-gap-finder),
  creating new US/Feature entities (use living-doc-create-user-story).
---

# Gherkin ↔ Living Doc Sync

> **Glossary:** Feature, Functionality, User Story, AC — see [living-doc-glossary](../references/living-doc-glossary.md) ([remote](https://github.com/AbsaOSS/agentic-toolkit/blob/master/skills/references/living-doc-glossary.md)).

Sync runs in three directions: (1) feature file → living doc, (2) living doc AC → feature file,
(3) step text → PageObject method signature.

Use `scripts/scan_ac_links.py` to detect missing or malformed `# AC:` headers before a full
sync run.

---

## Step 1 — Detect the sync direction

| Change event | Sync direction | Action |
|---|---|---|
| New `.feature` file added | Feature file → living doc | Link each scenario to an AC; create AC if missing |
| User Story AC modified or added | Living doc → feature file | Update or add the corresponding scenario |
| UI refactored (selector / method renamed) | Step text → PageObject | Update step text; re-link to PageObject method |
| US deprecated | Living doc → feature file | Emit one sync action per linked scenario; add `@deprecated`, record the reason, and flag `@review-needed` |
| Scenario added without an AC comment | Feature file → living doc | Propose an AC and add the `# AC:` header |

---

## Step 2 — Audit AC link headers

**Required AC link format** (from the glossary):

```gherkin
# AC: US-001-01 (v1.0.0 – Active) — Customer places an order
Scenario: Customer successfully places an order
```

- AC ID format: `AC:<parent-id>-<nn>` — e.g. `AC:US-001-01`, `AC:FUNC-001-02`
- The `# AC:` comment(s) must appear on the lines immediately above `Scenario:` or `Scenario Outline:`. Multiple `# AC:` lines are allowed — a scenario may cover more than one AC, and annotation comments (e.g. `# @tag`, free-text notes) may also appear in the block.

**Audit checklist:**
1. Does every `Scenario:` / `Scenario Outline:` have a `# AC:` comment?
2. Does the referenced AC ID exist in the living doc catalog?
3. Does the AC state match (`Active` or `Implemented` — not `Deprecated` or `Planned`)?
4. Does the AC description match the scenario intent?

For each missing or mismatched link:

```
SYNC ACTION: checkout.feature:14
  Scenario: "Customer successfully places an order"
  → Missing AC link header
  → Proposed link: # AC: US-001-01 (v1.0.0 – Active) — Customer places an order
  → Confirm or select a different AC
```

---

## Step 3 — Detect step text drift

When step text changes after a UI refactor, the step definition binding breaks:

```
DRIFT DETECTED: checkout.feature:17
  Step: "When the customer clicks the Confirm Purchase button"
  → No matching step definition found
  → Previous match: "When the customer confirms the order" (checkout_steps.py:34)
  → PageObject method: CheckoutPage.confirm_order()
  → Suggested fix: update step text to "When the customer confirms the order"
    OR update the step definition regex to match the new wording
```

---

## Step 4 — Apply sync changes

Apply the minimum necessary change per action:

- **Add missing AC link** → insert `# AC: <id> (v<version> – <State>) — <description>` above `Scenario:`
- **Update stale AC description** → update comment text only; do not change the AC ID. Show the exact change as `OLD:` and `NEW:` lines. If the revised AC intent changed materially, flag the linked step text for review instead of restructuring the scenario in the same sync action.
- **Update scenario to match revised AC** → update step text; keep the `# AC:` link unchanged
- **Fix broken step text** → prefer updating the `.feature` file to match the existing step definition and PageObject method; only update the step definition regex when the business wording genuinely changed
- **Mark deprecated scenarios** → add `@deprecated` and `@review-needed`, plus a comment with the date and reason. Emit one action per affected scenario with file and line number.
- **Broken AC reference** → never silently remove the `# AC:` comment. Either relink it to the correct AC ID, or create the missing living doc entity with `living-doc-create-user-story` / `living-doc-create-functionality`, then update the link.
- **AC split into multiple ACs** → update the existing scenario's `# AC:` link to the primary AC; create new scenarios for additional ACs

Never delete a scenario during sync — flag it with `@review-needed` for developer decision.

---

## Step 5 — Output sync report

Do **not** apply sync changes automatically. Report `DRIFT DETECTED` blocks first (tests fail), then `SYNC ACTION` blocks (traceability), and ask the developer to confirm each action before editing files.

```
DRIFT DETECTED: checkout.feature:17
  Step: "When the customer clicks the Confirm Purchase button"
  → No matching step definition found
  → Previous match: "When the customer confirms the order" (checkout_steps.py:34)
  → PageObject method: CheckoutPage.confirm_order()
  → Recommended fix: update the feature file step text to match the existing step definition
    OR update the step definition regex to match the new wording
  → Apply change? (y/n)

SYNC ACTION: checkout.feature:14
  Scenario: "Customer successfully places an order"
  → Missing AC link header
  → Proposed link: # AC: US-001-01 (v1.0.0 – Active) — Customer places an order
  → Apply change? (y/n)

SYNC ACTION: checkout.feature:32
  Scenario: "Customer reviews order totals before payment"
  → Missing AC link header
  → Proposed link: # AC: US-001-02 (v1.0.0 – Active) — Customer reviews the order summary before confirming payment
  → Apply change? (y/n)

Summary: 2 missing AC links, 1 step text drift detected — apply changes? (y/n per action)
```

---

## Anti-patterns to flag

| Anti-pattern | Flag |
|---|---|
| Scenario with no AC link | Missing traceability — add link or create AC |
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
