---
name: gherkin-living-doc-sync
description: >
  Synchronise Gherkin feature files and BDD scenarios with the living documentation catalog.
  Activate when scenarios diverge from User Story ACs, when step text drifts after a UI
  refactor, or when AC link headers are missing or stale. Distinct from gap-finder (which
  detects missing coverage) — corrects existing links.
  Triggers on: "sync gherkin to living doc", "feature file out of sync", "scenario not linked
  to AC", "step text changed", "gherkin drift", "update living doc after BDD change",
  "BDD sync", "AC link missing in feature file", "sync scenarios",
  "gherkin out of sync with living doc", "traceability broken".
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
| US deprecated | Living doc → feature file | Mark linked scenarios as `@deprecated` or remove |
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
- **Update stale AC description** → update comment text; do not change the AC ID
- **Update scenario to match revised AC** → update step text; keep the `# AC:` link unchanged
- **Fix broken step text** → update the `.feature` file to match the step definition
- **Mark deprecated scenarios** → add `@deprecated` tag and a comment with the reason
- **AC split into multiple ACs** → update the existing scenario's `# AC:` link to the primary AC; create new scenarios for additional ACs

Never delete a scenario during sync — flag it with `@review-needed` for developer decision.

---

## Step 5 — Output sync report

```
SYNC REPORT — 2026-05-22
  Applied automatically (3):
    checkout.feature:14 — added AC link header AC:US-001-01
    checkout.feature:28 — updated AC description (AC:US-001-02)
    login.feature:7    — fixed step text drift → "When the user submits valid credentials"

  Requires manual review (1):
    checkout.feature:45 — Scenario "Apply promo and checkout" has no matching AC
      → Either create a new AC in US-001, or remove this scenario if it is obsolete
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
| Creating new User Story or Feature entities | `living-doc-create-user-story` |
