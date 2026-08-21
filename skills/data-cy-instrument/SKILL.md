---
name: data-cy-instrument
description: >
  Automatically resolve missing `data-cy` attributes in Angular templates and sync PageObjects
  to use `getByTestId()`. Angular-first but phases 1, 3, and 5 are framework-agnostic. Activates
  when coverage_gaps are non-empty, PageObjects carry "⚠️ PROPOSED" locator comments, or
  Functionalities have `status: planned` due to missing test IDs.
  Triggers on: "add missing data-cy", "instrument templates", "fix data-cy gaps", "add testids",
  "data-cy audit", "instrument angular templates", "fix locators", "add data-cy attributes",
  "add test ids to templates", "fix playwright selectors due to missing data-cy", "data-cy-instrument",
  "coverage_gaps", "Functionality status planned".
  Does NOT trigger for: adding Gherkin (use living-doc-scenario-creator); PageObject
  healing without data-cy gaps (use living-doc-pageobject-scan HEALING).
  Pairs with living-doc-pageobject-scan (upstream) and living-doc-scenario-creator (downstream);
  invokes living-doc-update for Functionality promotion.
license: Apache-2.0
---

# data-cy-instrument

> **Glossary:** Feature, Functionality, status vocabulary — see [living-doc-glossary](../shared/references/living-doc-glossary.md).
> **BDD schemas:** manifest.json coverage_gaps schema, seed.yaml form_fixtures — see [living-doc-bdd-schemas](../shared/references/living-doc-bdd-schemas.md).

**Framework scope:** **Angular-first. Phases 1, 3, and 5 are framework-agnostic; Phases 2 and 4 are Angular-only.** For React or Vue, use the project's configured test-id attribute (often `data-testid`; `data-cy` is only the default), keep the same audit and PageObject-sync flow, and skip Angular-only route-to-component and host-wiring instructions. If the question is specifically “What do I do for React or Vue?”, start the answer with that bold sentence, then add: **Phases 2 and 4 are Angular-only and should be skipped for React or Vue.** In user-facing answers, prefer the plain labels **Instrument** and **Sync** (see "User-facing labels" below) — not phase numbers, to avoid colliding with the internal Phase 1–7 sequence.

Resolves missing test-id attributes end-to-end: gap discovery in `manifest.json`, template edits, PageObject sync, Functionality promotion, and WORK_LOG update. Follow the phases in order.

**Project Profile:** Read `<bdd_artifacts_dir>/.project-profile.yaml` (default `.copilot/bdd/.project-profile.yaml`) for `test_id_attribute` (default `data-cy`), `paths.pageobjects`, `feature_dirs.functionality`, and `paths.bdd_artifacts`. Substitute the profile and local layout. If asked whether to use `data-cy` or `data-testid`, answer explicitly: read `test_id_attribute` first, use that value, and never hardcode `data-cy` when a profile is present.

---

## When this skill activates

- `manifest.json` has one or more surfaces with a non-empty `coverage_gaps` array
- A PageObject file contains a locator comment marked `⚠️ PROPOSED` or `⚠️ NOT YET IN TEMPLATE`
- A Functionality `.feature` file has `status: planned` with a comment indicating the reason is missing `data-cy`
- WORK_LOG.md §4 has rows marked 🔴 or ⚠️
- User asks to add/fix data-cy or instrument an Angular template

---

## Phase 1 · Gap Audit

Build a prioritised gap list before editing:

1. Load `.copilot/bdd/manifest.json` and extract every `coverage_gaps` item.
2. Load `.copilot/bdd/WORK_LOG.md` §4 and find rows with status 🔴 (pending) or ⚠️ (lib-limited).
3. Cross-reference `.copilot/bdd/issue-missing-data-cy.md` if present.
4. For each gap, record:

   ```
   route:             /auth/domain-access-control
   element_desc:      Status filter toggle (Pending / Approved / Rejected)
   suggested_data_cy: filter-access-status
   component_hint:    domain-access-approvals-new.component.html
   priority:          P1 | P2 | P3
   ```

5. Sort P1 → P3 and process in that order.
6. Classify each gap before editing:
   - **Native/app-owned element or component that forwards attributes:** add the configured test-id attribute (**Instrument** step), then update the PageObject to `getByTestId()` (**Sync** step).
   - **Third-party component that does not forward attributes:** do **not** silently skip it. Mark it ⚠️ `needs lib support` and add a `WORK_LOG.md` §4 row with status ⚠️, element description, library name + version, and an issue-tracker link.

**For “what next after a Phase 1 scan?” answers, use this explicit decision tree:**
1. Decide whether each target is native/app-owned or third-party.
2. If native/app-owned, add the configured test-id attribute in the template.
3. If third-party and forwarding is blocked, add the ⚠️ `WORK_LOG.md` §4 row with element description, library name + version, and issue-tracker link — never silently skip it.
4. After all native/app-owned elements are instrumented, proceed to the **Sync** step and replace fallback selectors with `getByTestId()`.
For this question shape, use the user-facing labels `Instrument` (template) and `Sync` (PageObject), not the internal Phase numbers.

**Skip list — do not attempt to instrument these:**
- Elements inside third-party library internals where the host attribute is confirmed not to propagate (e.g. `cps-table` inner paginator buttons, `cps-tab` inner `<li role="tab">`). Mark these ⚠️ "needs lib support" — add a WORK_LOG.md §4 row with status ⚠️, element description, library name/version, and a library-issue link. Do not leave silent skips.
- Elements that require authenticated roles to render — flag as needing an integration test fixture, not a data-cy change.

Example `WORK_LOG.md` §4 row for a lib-limited element:

```md
| ⚠️ | Checkout confirm button | MatButton (Angular Material v17.3.0) | Cannot forward data-cy; tracked at https://github.com/angular/components/issues/XXXX |
```
When asked for the expected row format, emit this concrete row shape with a specific element description (for example `Checkout confirm button`), not a generic placeholder.
Keep the issue link as a plain-text URL — no rich-link or terminal-link formatting.

**User-facing labels:** call template instrumentation **Instrument** and PageObject sync **Sync** — plain names, not phase numbers, so they never collide with the internal Phase 1–7 sequence above. For `⚠️ PROPOSED` or remaining `coverage_gaps`, say: “run Instrument first to add the attribute, then Sync to update the PageObject.”

---

## Phase 2 · Route → Component Resolution

For each gap, resolve which Angular component owns the element.

1. Open `aul-ui/src/app/pages/authenticated/authenticated-routing.module.ts` (or the relevant routing module).
2. Find the route path matching the gap's route.
3. Check feature-flag conditionals:
   - `environment.useBoundedCtxApi` (runtime flag `BD_CTX_API`) — if present, there are two component variants: `-new` (flag on) and the legacy component (flag off). **Instrument both.**
   - `SHOW_EXPERIMENTAL_FEATURES` — instrument only if the element is inside that guard.
4. If the component is a wrapper that delegates to a child (`<app-*>` sub-component), follow the child selector to its `.html` file. Repeat until the element is found.
5. Record the resolved template path(s) before making any edits.

---

## Phase 3 · Name Validation

Before writing any test-id value, validate the candidate name.

**Naming prefix rules:**

| Prefix | Use for | Example |
|---|---|---|
| `btn-` | Any CTA button (`<cps-button>`, `<button>`) | `btn-request-access-rights` |
| `tab-` | Tab host element (`<cps-tab>`, `<li role="tab">`) | `tab-version-management` |
| `filter-` | Filter control (toggle group, dropdown used to filter) | `filter-access-status` |
| `toggle-` | Boolean toggle (checkbox, switch) | `toggle-primary-ownership` |
| `input-` | Text / number input field | `input-domain-name` |
| `row-` | Clickable / selectable table row | `row-run-history` |
| `metric-` | Read-only display card / KPI tile | `metric-coverage` |
| `pagination-` | Pagination control | `pagination-page` |
| `dialog-` | Modal / side-nav container | `dialog-import-domain` |
| `select-` | Dropdown / select used to choose a value | `select-country-code` |

**Format rules:**
- Kebab-case only — no underscores, no camelCase.
- Must be unique in the workspace: run `grep_search` for the candidate value across `aul-ui/src/**/*.html` before writing. If already present, append a disambiguating suffix (e.g. `-header`, `-row`, `-footer`).
- Must be descriptive enough to understand the element's purpose without context.

---

## Phase 4 · Apply to Angular Template (user-facing label: Instrument)

Add `data-cy` to the **host** Angular component element, not the inner native element.

**The rule:**
```html
<!-- ✅ correct: data-cy on the CPS host -->
<cps-button data-cy="btn-create-draft-version" label="Create new draft version" ...>
</cps-button>

<!-- ❌ wrong: data-cy on the inner native button -->
<cps-button ...>
  <button data-cy="btn-create-draft-version">Create new draft version</button>
</cps-button>
```

**Placement:** Add `data-cy` as the second attribute after the component tag name (or after any structural directive like `*ngIf`, `@if`, `[ngClass]`). Preserve existing attributes and indentation.

**Multi-line component elements:**
```html
<!-- Before -->
<cps-button
  class="go-to-all-access-requests-btn"
  type="borderless"
  label="Apply for access"
  (clicked)="goToAllAccessRequests()">

<!-- After -->
<cps-button
  data-cy="btn-apply-access-other"
  class="go-to-all-access-requests-btn"
  type="borderless"
  label="Apply for access"
  (clicked)="goToAllAccessRequests()">
```

**Inline component elements:**
```html
<!-- Before -->
<cps-button (clicked)="openViewAccessReqSidenav(item)" color="prepared" label="View" type="borderless">

<!-- After -->
<cps-button (clicked)="openViewAccessReqSidenav(item)" color="prepared" data-cy="btn-view-access-request" label="View" type="borderless">
```

When a gap covers multiple instances of the same component in a loop (e.g. one "View" button per row), add the `data-cy` once on the template element — the PageObject will use `.nth(index)` to distinguish instances.

---

## Phase 5 · PageObject Sync (user-facing label: Sync)

After every template change, update the matching PageObject in `<paths.pageobjects>/`.

**Instrument is required first:** `⚠️ PROPOSED` means the template still lacks the required test-id attribute. Add it in **Instrument**, then update the PageObject in **Sync**. When explaining `⚠️ PROPOSED`, say: “Instrument has not yet been done for that element. Run Instrument to add the missing test-id attribute to the template, then replace the PROPOSED locator with `getByTestId()` in Sync.”

**Replace proposed/fallback locators with `getByTestId()`:**

```typescript
// Before — text fallback or proposed comment
// ⚠️ PROPOSED data-cy: confirm-order-btn
readonly confirmOrderButton: Locator = this.page.locator('button.confirm-order');

// After
readonly confirmOrderButton: Locator = this.page.getByTestId('confirm-order-btn');
```

When answering a locator-conversion question, explicitly say: replace the old locator with `getByTestId('<value>')`, then remove the related `⚠️ PROPOSED` comment after updating the locator in Sync.

**Inner element resolution:** `getByTestId()` resolves the host Angular component element. Chain `.locator('button')` or `.locator('input')` only when the real interaction target is a native child and direct `getByTestId()` is insufficient.

**Remove stub markers:** Delete any comment lines containing `⚠️ PROPOSED`, `⚠️ NOT YET IN TEMPLATE`, or `will resolve once template is updated` that relate to the now-instrumented elements.

**If `coverage_gaps` is still non-empty after Sync, check in this order:**
1. Did **Instrument** actually add the configured test-id attribute to the template?
2. Did **Sync** update the PageObject locator to `getByTestId('<same-value>')`?
3. Is the element conditionally rendered (for example `*ngIf`) and therefore absent during the scan?
4. Is the element inside a Shadow DOM or other boundary that blocks standard attribute access?
If all four checks pass and the gap remains, add or update a `WORK_LOG.md` §4 row so the remaining blocker is tracked.

**Update PageObject header comments:**
- Change `status: candidate` → `status: active` if all locators for the page are now resolved.
- Remove `stub-reason:` line if no un-instrumented elements remain.

---

## Phase 6 · Living Doc Promotion

For each Functionality whose `status: planned` was solely due to missing `data-cy`, act only after **Instrument** (template instrumentation) and **Sync** (PageObject update) are complete.

1. Open `<feature_dirs.functionality>/func-{NNN}-*.feature` (e.g. `aul-ui/playwright/features/liv_doc_func/`).
2. Change `# status: planned` → `# status: active` in the comment header.
3. Remove the `# planned-reason: no data-cy attributes` comment line if present.
4. Do **not** change any other header fields (AC text, func_type, feature, etc.).

Only promote if the data-cy attributes required by that Functionality's ACs were all added during **Instrument**. If a Functionality depends on multiple elements and only some were instrumented, leave it as `planned` and add a comment listing the remaining blockers.

Primary downstream action: `living-doc-update` changes the matching catalog entity from `planned` to `active`. If the task also updates the BDD feature-file header, keep it in sync. For promotion questions, answer in routing form: after Instrument and Sync, load `living-doc-update`. Do **not** lead with manual feature-file edits.

Preferred promotion wording: `After Instrument and Sync complete, invoke living-doc-update and change FUNC-001 status from 'planned' to 'active'.`

---

## Phase 7 · WORK_LOG Update

Update `.copilot/bdd/WORK_LOG.md` §4 and §8 to reflect completed work.

**§4 row updates:** change 🔴 → ✅ for each instrumented element; change `Suggested data-cy` to the `data-cy` column for confirmed values; add a "Files updated:" note under the section header listing the template file(s) changed.

**§8 open items:** close resolved OI items (`✅ closed` or remove the row). If a gap was only partially resolved (e.g. some elements done, some need lib support), update the item description to reflect the remaining scope.

---

## Output after completing all phases

Report the following at the end of the run:

```
## data-cy-instrument run summary

### Templates updated
- <file-path>: <list of data-cy values added>

### PageObjects synced
- <PageObject.ts>: <locators updated>

### Functionalities promoted
- <func-NNN-*.feature>: planned → active

### Remaining gaps (lib-limited or deferred)
- <element description>: <reason>

### WORK_LOG §4 rows closed: N
### WORK_LOG OI items closed: N
```

---

## Interaction with other skills

| Skill | Relationship |
|---|---|
| `living-doc-pageobject-scan` | Upstream — produces `manifest.json` with `coverage_gaps` and may leave `⚠️ PROPOSED` locator comments when test-id attributes are missing. `data-cy-instrument` consumes both signals, adds the attributes to templates, and updates PageObjects to use `getByTestId()`. |
| `living-doc-pageobject-scan` RE-SCAN scope | Upstream — re-generates `coverage_gaps` after a UI change. Trigger this skill after RE-SCAN if new gaps appear. |
| `living-doc-scenario-creator` | Downstream — after Functionalities are promoted from `planned` to `active`, generate Gherkin scenarios for them. |
| `living-doc-update` | Downstream — if PageObject header `status` changes, the corresponding Feature entity in the living doc may also need a status update. |

When describing the relationship, state it in this order: `living-doc-pageobject-scan` is upstream, `data-cy-instrument` resolves missing test-id gaps and `⚠️ PROPOSED` locators, and `living-doc-scenario-creator` is downstream and uses the stable locators.

Say this explicitly when asked about the relationship: `living-doc-scenario-creator` is the downstream step after `data-cy-instrument` completes.

**Pipeline position:**
```
living-doc-pageobject-scan (or RE-SCAN)  →  data-cy-instrument
  →  living-doc-update  (promote Functionalities: planned → active)
  →  living-doc-scenario-creator
```

---

## Out-of-scope routing

This skill applies **only** when `coverage_gaps` are non-empty or PageObjects carry `⚠️ PROPOSED` / missing-test-id locators. Pure selector drift without missing test IDs belongs to `living-doc-pageobject-scan` HEALING.

| Request | Correct skill |
|---|---|
| Add or fix Gherkin scenarios | `living-doc-scenario-creator` |
| Generate or heal PageObjects (no missing data-cy) | `living-doc-pageobject-scan` |
| Fix selector drift from DOM structure changes (no missing data-cy) | `living-doc-pageobject-scan` HEALING scope |
| Deprecate a Functionality entity | `living-doc-update` |
