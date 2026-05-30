---
name: bdd-maintain
description: >
  Maintenance modes for the @living-doc-bdd-copilot agent: RE-SCAN (full manifest refresh
  after UI changes), HEALING (fix selector drift in failing tests only), and REMOVE
  (delete files linked to a deprecated feature). Activate when the UI has changed and the
  manifest needs refreshing, when tests are failing due to selector drift, or when a feature
  has been removed from the product.
  Triggers on: "re-scan", "refresh manifest", "heal pageobjects", "fix failing tests",
  "selector drift", "tests are failing", "remove feature", "deprecate bdd", "bdd maintain",
  "update selectors", "pageobject broken", "scenario failing".
---

# BDD Maintenance

Three modes — activate the one that matches the trigger.

---

## RE-SCAN mode

**Trigger:** New feature shipped, UI refactored, or significant route changes.

**Scope:** Full re-run of every path recorded in `manifest.json`, plus active discovery of new routes not yet in the manifest.

1. Reload `seed.yaml` and `manifest.json`.
2. For every existing manifest entry: navigate to its URL, snapshot the DOM, and validate that every recorded `component_id` locator still resolves. Flag any locator that no longer matches as `BREAKING CHANGE`, including the linked step definition / scenario details that may fail.
3. **Actively discover new routes from each visited page** — do not limit discovery to routes already in `seed.yaml`. On each page snapshot:
   - Find all `<a href>` links that resolve to new paths not yet in the manifest.
   - Find all buttons and interactive components whose purpose suggests navigation to a new screen (e.g. "Create order", "View details", "Go to settings") — click them and record the resulting URL.
   - Find tab panels, side-nav items, and wizard steps that expose sub-routes.
   - Any new URL discovered this way is a candidate manifest entry; add it and crawl it recursively.
4. Add new surfaces to `manifest.json`; mark removed surfaces as `deprecated`.
5. Update stale selector constants in PageObjects for any locators flagged in step 2.
6. Generate new scenarios for newly discovered ACs (load `bdd-scenario-gen` skill).

---

## HEALING mode

**Trigger:** Test suite failures due to selector drift, broken step definitions, or PageObject mismatches.

**Scope:** Failing tests only — do not touch passing tests or unrelated PageObjects.

1. Receive or discover the list of failing test names / scenario titles. If the request only says tests are failing but does not include the failing list, ask for it before making changes so scope stays limited to the failing scenarios.
2. Trace each failure back to its PageObject and step definition.
3. Navigate to the affected page via MCP Playwright; snapshot the current DOM.
4. Find updated element IDs or selectors; update only the affected PageObject(s) accordingly.
5. Verify the step definition binding still resolves; fix if broken.
6. Re-run only the previously failing tests to confirm healing. Do not re-run the full suite.

---

## REMOVE mode

**Trigger:** Feature deprecated or deleted from the product.

**Scope:** Only files linked to the removed entity — do not touch other Features, PageObjects, or step definitions.

1. Identify the specific Feature/US/AC being removed.
2. Find all `.feature` files whose scenarios carry an `@AC:` tag matching the removed entity's IDs.
3. Find PageObjects referenced only by those scenarios; find step definitions used only by those scenarios.
4. Confirm the full deletion list with the user before touching any file.
5. Remove confirmed files; update `manifest.json` to remove the deprecated entry.
6. Flag linked US/AC entities in the living documentation as candidates for deprecation — hand off to `@living-doc-copilot`.

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
