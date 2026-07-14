---
name: gherkin-living-doc-sync
description: >
  Synchronise Gherkin feature files and BDD scenarios with the living documentation catalog.
  Corrects existing links — distinct from living-doc-gap-finder (which detects missing coverage).
  Activate when `@AC:` tags or `# AC:` comments are missing or stale, step text drifts after
  a refactor, ACs are descoped, or AC changes must propagate from the living doc to feature files.
  Run scan_ac_links.py to audit AC link health before a sync pass.
  Triggers on: "sync gherkin to living doc", "feature file out of sync", "scenario not linked
  to AC", "step text changed", "gherkin drift", "BDD sync", "AC link missing in feature file",
  "sync scenarios", "traceability broken", "propagate AC changes", "AC was descoped".
  Does NOT trigger for: writing new scenarios (use living-doc-scenario-creator); implementing
  step definitions (use gherkin-step); finding gaps (use living-doc-gap-finder);
  creating entities (use living-doc-create-*).
  Pairs with living-doc-update (upstream) and gherkin-step (downstream).
license: Apache-2.0
compatibility: GitHub Copilot
---

# Gherkin ↔ Living Doc Sync

> **Glossary:** Feature, Functionality, User Story, AC — see [living-doc-glossary](../../shared/references/living-doc-glossary.md) ([remote](https://github.com/AbsaOSS/agentic-toolkit/blob/master/skills/shared/references/living-doc-glossary.md)).
> **BDD schemas:** US and Functionality feature file headers, `# Acceptance Criteria:` block format — see [living-doc-bdd-schemas](../references/living-doc-bdd-schemas.md) ([remote](https://github.com/AbsaOSS/agentic-toolkit/blob/master/skills/references/living-doc-bdd-schemas.md)).

Sync runs in three directions: (1) feature file to living doc, (2) living doc AC to feature file,
(3) step text to PageObject method signature.

Use `scripts/scan_ac_links.py` to detect missing or malformed `@AC:` tags and missing `# AC:`
comments before a full sync run. The script only checks the living-doc feature directories
(`feature_dirs.user_story` and `feature_dirs.functionality` from the Project Profile, defaults
`features/liv_doc_us/` and `features/liv_doc_func/`; pass them via `--us-dir`/`--func-dir`) — other
feature files are skipped.
For a full audit, run:

```bash
python skills/gherkin-living-doc-sync/scripts/scan_ac_links.py <features_dir> \
  --us-dir <feature_dirs.user_story> \
  --func-dir <feature_dirs.functionality> \
  --catalog <catalog_path>
```

The report should distinguish: (1) missing `# AC:` comments, (2) stale AC IDs not found in the
catalog, and (3) mismatched `# AC:` / `@AC:` pairs where only one side or the aspect details differ.
Use the report in this repair order: broken links first, then missing links, then mismatches.

---

## Step 1 — Detect the sync direction

**Upstream dependencies:** Directions that flow from the living documentation into feature files are initiated by catalog-layer operations from `@living-doc-bdd-copilot`:
- `living-doc-update` modified, added, or deprecated an AC → triggers directions 2 and 4 below
- `living-doc-impact-analysis` identified High-impact AC changes that require resync → may trigger directions 2 and 3

| Change event | Sync direction | Action |
|---|---|---|
| New `.feature` file added | Feature file to living doc | Link each scenario to an AC; create AC if missing |
| User Story AC modified or added | Living doc to feature file | Update or add the corresponding scenario |
| UI refactored (selector / method renamed) | Step text to PageObject | Update step text and `@AC:` tag if scenario intent changed; for the PageObject side of the rename (method signature or locator), load `living-doc-pageobject-scan` HEALING scope — this skill owns only the Gherkin step text, not the PageObject code |
| US deprecated | Living doc to feature file | Emit one sync action per linked scenario; add `@deprecated`, record the reason, and flag `@review-needed` |
| Scenario added without an `@AC:` tag | Feature file to living doc | Propose an AC and add the `@AC:` tag |

---

## Step 2 — Audit `@AC:` traceability tags

> **Authoritative source:** The `@AC:` format is defined in `living-doc-scenario-creator`. The spec below is a reference copy for sync validation — load `living-doc-scenario-creator` for the canonical definition.

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

**Deprecated US detection (Direction 4):** When the trigger is a deprecated User Story, first
build the list of affected scenarios before running the standard checklist:

1. Collect all AC IDs owned by the deprecated US (from the US entity or its feature file header).
2. Search all `.feature` files under the living-doc directories (`feature_dirs.user_story` and
   `feature_dirs.functionality`) for
   `@AC:` tags matching those IDs.
3. For each matching scenario, emit a SYNC ACTION to add `@deprecated` and `@review-needed`,
   with a comment recording the deprecation date and reason from the US entity.
4. After tagging, continue with the standard checklist below to catch any remaining link issues.

**Audit checklist:**
1. Does every `Scenario:` / `Scenario Outline:` in living-doc files have at least one `@AC:` tag?
2. Is the corresponding `# AC:` comment present and matching the tag's AC ID?
3. Does the referenced AC ID exist in the living documentation?
4. Does the AC state match (logically `Active` — not `Deprecated`, `Planned`, or `In Review`, per the profile `ac_states`)?
5. Does the AC description (in the file header) match the scenario intent?

For each missing or mismatched tag:

```
SYNC ACTION: checkout.feature:14
  Scenario: "Customer successfully places an order"
  Missing @AC: tag
  Proposed tag: @AC:US-001-01
  Confirm or select a different AC
```

For each missing or mismatched `# AC:` comment, emit the same style of block and propose the full
comment line:

```text
SYNC ACTION: checkout.feature:14 — Missing AC link header
  Scenario: "Customer successfully places an order"
  Proposed link: # AC:US-001-01 (v1.0.0 - Active) — customer places an order with a saved payment method
  Apply change? (y/n)
```

When multiple scenarios are affected, emit one `SYNC ACTION` block per scenario and identify each
scenario by file path, line number, and title before proposing the `# AC:` line. Preserve every
scenario — syncing missing headers never deletes or restructures the scenario itself.
If the prompt states a concrete count (for example “3 scenarios”), say that all 3 scenarios are
missing AC link headers, then emit 3 separate `SYNC ACTION` blocks and propose a matching AC for
each scenario from the living doc catalog. Do not hedge with “for example” or generic placeholders
in that answer — show the concrete proposed mappings directly in the blocks.

If only one of `@AC:` or `# AC:` is present, that is still a sync issue — raise a SYNC ACTION and
repair the missing side rather than treating the scenario as already synced.

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

> **Scope boundary with `living-doc-pageobject-scan` HEALING:** This step corrects step text in `.feature` files and step definition pattern strings. If the underlying PageObject selector or method signature drifted (renamed in the DOM or PageObject class), use `living-doc-pageobject-scan` HEALING mode to fix the PageObject class first, then re-run this sync to align feature files.
>
> **Step definition code changes:** When a step definition regex pattern must be updated (not just the feature file wording), load `gherkin-step` to apply the code change correctly.
>
> **Output rule:** Always emit the full `DRIFT DETECTED` block header with file path, line number,
> broken step text, previous matching definition, PageObject method, and the two fix options. Prefer
> fixing the `.feature` file wording first because it is the lower-risk change when the existing step
> definition and PageObject method still work.

---

## Step 4 — Apply sync changes

Apply the minimum necessary change per action:

- **Add missing `@AC:` tag**: insert `@AC:<id>` above `Scenario:`
- **Update stale AC reference**: this is **living doc → feature file** sync. Update the file header's `# Acceptance Criteria:` block entry; the `@AC:` tag on the scenario stays unchanged. Show the exact change as `OLD:` and `NEW:` lines, and mirror the current version/state text from the living doc in the `NEW:` line (for example `v1.0.0` → `v1.1.0` when the AC version changed). If the revised AC intent changed materially, add an explicit `Step text review:` note so the linked step wording can be checked before any scenario restructuring.
- **Update scenario to match revised AC**: update step text; keep the `@AC:` tag unchanged
- **Fix broken step text**: prefer updating the `.feature` file to match the existing step definition and PageObject method; only update the step definition regex when the business wording genuinely changed
- **Mark deprecated scenarios**: add `@deprecated` and `@review-needed`, plus a comment with the date and reason. Emit one action per affected scenario with file and line number.
- **Mark descoped scenarios**: add `@wip` or `@pending` and `@review-needed`, plus a comment with the descope reason and target-release reference. Preserve the scenario — never delete it — so it can be reinstated when the AC is promoted back to Active. Emit one SYNC ACTION per affected scenario.
- **Broken AC reference**: never silently remove the `@AC:` tag. Either relink it to the correct AC ID, or create the missing living doc entity with `living-doc-create-user-story` / `living-doc-create-functionality`, then update the tag.
- **AC split into multiple ACs**: update the existing scenario's `@AC:` tag to the primary AC; emit a separate `SYNC ACTION` proposing each additional scenario, including the required `# AC:` header and `@AC:` tag for the new AC. Developer confirmation is still required before any new scenario is created.
- **Aspect mismatch** (`@AC:.../aspect:...` present but comment missing the aspect): raise a SYNC ACTION and update the comment to include the human-readable `| aspect: ...` suffix. Confirm before applying.

Never delete a scenario during sync — flag it with `@review-needed` for developer decision.

---

## Step 5 — Output sync report

Do **not** apply sync changes automatically. Report `DRIFT DETECTED` blocks first (tests fail), then `SYNC ACTION` blocks (traceability), and ask the developer to confirm each action before editing files. List every affected scenario with file path and line number. This confirmation rule also applies to comment-only edits such as updating a `# AC:` description or adding an aspect suffix.
Prioritise repair in this order: broken step bindings first because they cause immediate test
failures, then stale / broken AC links because they create traceability gaps, then lower-risk
comment/tag mismatches.

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

For deprecated or descoped entities, emit one `SYNC ACTION` per affected scenario, each with its own
file path and line number, plus the added tags/comments (`@deprecated` + `@review-needed`, or
`@wip`/`@pending` + descope reason).
For missing-link report examples, include the full proposed `# AC:` comment (ID, version, state,
description, and aspect if relevant) — not just the `@AC:` tag.

---

## Anti-patterns to flag

| Anti-pattern | Flag |
|---|---|
| Scenario with no `@AC:` tag | Missing traceability — add tag or create AC |
| Two scenarios linked to the same AC | Usually a duplicate — review |
| AC linked from a scenario in a different User Story's feature file | Passive cross-US coverage — permitted but note it in the sync report. Only flag if the scenario's primary intent belongs to a different User Story (misplaced scenario) |
| Step text describes implementation (selector, endpoint) | Gherkin business-language violation — refer to `living-doc-scenario-creator` |

---

## Out-of-scope routing

| Request | Use instead |
|---|---|
| Writing new Gherkin scenarios from scratch | `living-doc-scenario-creator` |
| Implementing step definition code | `gherkin-step` |
| Finding ACs with no scenario coverage | `living-doc-gap-finder` |
| Creating new User Story, Feature, or Functionality entities | `living-doc-create-user-story` / `living-doc-create-functionality` |
