---
name: bdd-maintain
description: >
  Lifecycle cleanup for BDD automation artifacts. REMOVE: delete feature files, step
  definitions, and PageObjects linked to a deprecated entity. DEAD CODE AUDIT: find
  unused step definitions, PageObject methods, and PO components via three Python scripts.
  Third step in the entity-deprecation chain — after living-doc-update and gherkin-living-doc-sync.
  Triggers on: "remove feature", "deprecate bdd", "delete feature files", "bdd cleanup",
  "remove pageobject", "unused steps", "dead pageobject methods", "find unused steps",
  "dead code audit", "unused po methods", "dead po components", "bdd-maintain".
  Does NOT trigger for: re-scanning manifest after UI changes (use living-doc-pageobject-scan
  RE-SCAN); healing selector drift (use living-doc-pageobject-scan HEALING); syncing @AC:
  traceability tags (use gherkin-living-doc-sync).
  Pairs with living-doc-update (upstream — deprecate entity first) and
  gherkin-living-doc-sync (upstream — tag scenarios first).
license: Apache-2.0
compatibility: GitHub Copilot
---

# BDD Maintenance

> **Glossary:** Feature, Functionality, User Story — see [living-doc-glossary](../references/living-doc-glossary.md) ([remote](https://github.com/AbsaOSS/agentic-toolkit/blob/master/skills/references/living-doc-glossary.md)).
> **BDD schemas:** manifest.json schema (routes, elements, coverage_gaps, navigation_context) — see [living-doc-bdd-schemas](../references/living-doc-bdd-schemas.md) ([remote](https://github.com/AbsaOSS/agentic-toolkit/blob/master/skills/references/living-doc-bdd-schemas.md)).

Two modes — activate the one that matches the trigger.

---

## REMOVE mode

**Trigger:** Feature deprecated or deleted from the product.

**Prerequisite:** `living-doc-update` must have already deprecated the entity and `gherkin-living-doc-sync` must have already tagged linked scenarios with `@deprecated` and `@review-needed`. Run those two skills first if they have not yet run — removing files before scenarios are tagged silently breaks traceability.

**Scope:** Only files linked to the removed entity — do not touch other Features, PageObjects, or step definitions.

1. Identify the specific Feature/US/AC being removed.
2. Find all `.feature` files whose scenarios carry an `@AC:` tag matching the removed entity's IDs.
3. Find PageObjects referenced only by those scenarios; find step definitions used only by those scenarios. Also check `playwright/fixtures.ts` (or the project's fixture file) for fixture registrations that import the PageObjects being removed — those imports and constructor parameters must be removed too.
4. Confirm the full deletion list with the user before touching any file.
5. Remove confirmed files; remove the deprecated entry from `manifest.json`. Do not restructure or regenerate the manifest — `living-doc-pageobject-scan` owns the manifest for all active entries.
6. If any child entities (linked User Stories, Functionalities) were not yet deprecated in the catalog, flag them and load `living-doc-update` to deprecate them now.

---

## DEAD CODE AUDIT mode

**Trigger:** Step definitions added but scenarios removed, PageObject redesigned, new PO classes created but not yet wired into steps.

**Scope:** Full audit of `playwright/steps/`, `playwright/pages/`, and `playwright/features/` for dead code.

Three standalone Python scripts live in `scripts`:

### 1 · `find_unused_steps.py` — step definitions with no feature coverage

Parses all `*.steps.ts` files for `Given(…)`, `When(…)`, `Then(…)` pattern strings, then scans every `.feature` file for matching step usages (Cucumber expression placeholders resolved to regex wildcards). Reports any step definition that is never exercised.

```bash
# Run from aul-ui/
python playwright/scripts/find_unused_steps.py \
  --steps-dir playwright/steps \
  --features-dir playwright/features
```

### 2 · `find_unused_po_methods.py` — PageObject methods never called from step files

Parses every `playwright/pages/*.ts` for public method declarations (`async name(` / `name(`), then scans all step files for `.name(` call sites. Reports methods that are defined but never invoked from any step.

```bash
python playwright/scripts/find_unused_po_methods.py \
  --pages-dir playwright/pages \
  --steps-dir playwright/steps
```

### 3 · `find_unused_po_components.py` — PageObject classes not imported anywhere

Scans all exported `class` names from `playwright/pages/*.ts`, then checks every `*.steps.ts` and `fixtures.ts` for import statements. Reports classes that are defined but never imported.

```bash
python playwright/scripts/find_unused_po_components.py \
  --pages-dir playwright/pages \
  --steps-dir playwright/steps
```

### When to run

| Trigger | Script(s) to run |
|---------|-----------------|
| Step definition added or removed | `find_unused_steps.py` |
| PageObject method added, renamed, or deleted | `find_unused_po_methods.py` |
| New PageObject class created | `find_unused_po_components.py` |
| Before any REMOVE operation | All three |
| CI / pre-merge gate | All three (each exits 1 on findings) |

### Handling findings

- **Unused step def**: either add a scenario that exercises it, or delete the step definition.
- **Unused PO method**: either write a step that calls it, or remove the method from the PageObject.
- **Unused PO class**: either add an import and fixture entry, or remove the `.ts` file — after confirming nothing references it outside the test suite.

All three scripts exit `0` on clean, `1` on findings, `2` on bad arguments — safe for CI gating.

---

## Out-of-scope routing

| Request | Correct skill |
|---|---|
| Re-scan manifest after UI changes | `living-doc-pageobject-scan` RE-SCAN scope |
| Fix failing tests due to selector drift | `living-doc-pageobject-scan` HEALING scope |
| Sync `@AC:` traceability tags | `gherkin-living-doc-sync` |
| Deprecate an entity in the catalog | `living-doc-update` |
| Tag deprecated scenarios before deletion | `gherkin-living-doc-sync` |
