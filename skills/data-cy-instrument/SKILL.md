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
compatibility: GitHub Copilot
---

# data-cy-instrument

> **Glossary:** Feature, Functionality, status vocabulary — see [living-doc-glossary](../references/living-doc-glossary.md) ([remote](https://github.com/AbsaOSS/agentic-toolkit/blob/master/skills/references/living-doc-glossary.md)).
> **BDD schemas:** manifest.json coverage_gaps schema, seed.yaml form_fixtures — see [living-doc-bdd-schemas](../references/living-doc-bdd-schemas.md) ([remote](https://github.com/AbsaOSS/agentic-toolkit/blob/master/skills/references/living-doc-bdd-schemas.md)).

**Framework scope:** This skill is **Angular-first** — naming conventions, routing module paths,
and feature-flag patterns are Angular-specific. The gap audit, naming validation, and PageObject
sync phases (Phases 1, 3, 5) are framework-agnostic and apply to any frontend stack. For
React, Vue, or other frameworks, adapt the component resolution in Phase 2 to the project's
routing and component model; all other phases apply unchanged.

Resolves missing `data-cy` attributes end-to-end: from gap discovery in `manifest.json`
through Angular template edits, PageObject sync, Functionality promotion, and WORK_LOG
status update. All steps are in sequence — do not skip steps or re-order them.

---

## When this skill activates

- `manifest.json` has one or more surfaces with a non-empty `coverage_gaps` array
- A PageObject file contains a locator comment marked `⚠️ PROPOSED` or `⚠️ NOT YET IN TEMPLATE`
- A Functionality `.feature` file has `status: planned` with a comment indicating the reason is missing `data-cy`
- WORK_LOG.md §4 has rows marked 🔴 or ⚠️
- User asks to add/fix data-cy or instrument an Angular template

---

## Phase 1 · Gap Audit

Build a prioritised gap list before touching any file.

1. Load `.copilot/bdd/manifest.json`. For each surface entry, extract `coverage_gaps` items.
2. Load `.copilot/bdd/WORK_LOG.md` §4 — identify rows with status 🔴 (pending) or ⚠️ (lib-limited).
3. Cross-reference with `issue-missing-data-cy.md` if present at `.copilot/bdd/`.
4. For each gap, record:

   ```
   route:             /auth/domain-access-control
   element_desc:      Status filter toggle (Pending / Approved / Rejected)
   suggested_data_cy: filter-access-status
   component_hint:    domain-access-approvals-new.component.html
   priority:          P1 | P2 | P3
   ```

5. Sort by priority P1 → P3. Process in that order.

**Skip list — do not attempt to instrument these:**
- Elements inside third-party library internals where the host attribute is confirmed not to be propagated (e.g. `cps-table` inner paginator buttons, `cps-tab` inner `<li role="tab">` when the lib does not forward host attributes). Mark these ⚠️ "needs lib support" — add a WORK_LOG.md §4 row with status ⚠️, element description, library name and version, and a link to the library's issue tracker if one exists. Do not leave these as silent skips.
- Elements that require authenticated roles to render — flag as needing an integration test fixture, not a data-cy change.

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

Before writing any `data-cy` value, validate the candidate name.

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

## Phase 4 · Apply to Angular Template

Add `data-cy` to the **host** Angular component element, not the inner native element.

**The rule:**
```html
<!-- ✅ Correct — data-cy on the CPS host component -->
<cps-button data-cy="btn-create-draft-version" label="Create new draft version" ...>
</cps-button>

<!-- ❌ Wrong — data-cy on the inner native button rendered by the library -->
<cps-button ...>
  <button data-cy="btn-create-draft-version">Create new draft version</button>
</cps-button>
```

**Placement:** Add `data-cy` as the second attribute after the component tag name (or after any structural directive like `*ngIf`, `@if`, `[ngClass]`). Preserve all existing attributes and indentation exactly.

**Multi-line component elements:**
```html
<!-- Before -->
<cps-button
  class="go-to-all-access-requests-btn"
  type="borderless"
  label="Apply for access"
  (clicked)="goToAllAccessRequests()">

<!-- After — data-cy on the second line, before class -->
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

When a gap covers multiple instances of the same component in a loop (e.g. one "View" button per table row), add the `data-cy` once on the template element — the PageObject will use `.nth(index)` to distinguish instances.

---

## Phase 5 · PageObject Sync

After every template change, update the matching PageObject in `aul-ui/playwright/pages/`.

**Replace proposed/fallback locators with `getByTestId()`:**

```typescript
// Before — text fallback or proposed comment
// ⚠️ PROPOSED data-cy: btn-request-access-rights
readonly requestAccessButton: Locator = page.locator('cps-button', { hasText: 'Request access' });

// After
readonly requestAccessButton: Locator = page.getByTestId('btn-request-access-rights').locator('button');
```

**Inner element resolution:** `getByTestId()` resolves the host Angular component element. For Playwright interactions (`click`, `fill`), chain `.locator('button')` or `.locator('input')` on the result if the interaction target is the native element inside the host.

**Remove stub markers:** Delete any comment lines containing `⚠️ PROPOSED`, `⚠️ NOT YET IN TEMPLATE`, or `will resolve once template is updated` that relate to the now-instrumented elements.

**Update PageObject header comments:**
- Change `status: candidate` → `status: active` if all locators for the page are now resolved.
- Remove `stub-reason:` line if no un-instrumented elements remain.

---

## Phase 6 · Living Doc Promotion

For each Functionality whose `status: planned` was solely due to missing `data-cy`:

1. Open `aul-ui/playwright/features/liv_doc_func/func-{NNN}-*.feature`.
2. Change `# status: planned` → `# status: active` in the comment header.
3. Remove the `# planned-reason: no data-cy attributes` comment line if present.
4. Do **not** change any other header fields (AC text, func_type, feature, etc.).

Only promote if the data-cy attributes required by that Functionality's ACs have all been added in Phase 4. If a Functionality depends on multiple elements and only some were instrumented, leave it as `planned` and add a comment listing the remaining blockers.

After updating the BDD feature file header, also invoke `living-doc-update` to change the matching catalog entity's `status` from `planned` to `active`. The BDD file header and the catalog entity must stay in sync.

---

## Phase 7 · WORK_LOG Update

Update `.copilot/bdd/WORK_LOG.md` §4 and §8 to reflect completed work.

**§4 row updates:**
- Change 🔴 → ✅ for each element that was instrumented.
- Change `Suggested data-cy` column to the `data-cy` column for confirmed values.
- Add a "Files updated:" note under the section header listing the template file(s) changed.

**§8 open items:**
- Close OI items that are now fully resolved: change status column to `✅ closed` or remove the row.
- If a gap was partially resolved (e.g. some elements done, some need lib support), update the item description to reflect remaining scope.

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
| `living-doc-pageobject-scan` | Upstream — produces `manifest.json` with `coverage_gaps`. This skill consumes that output. |
| `living-doc-pageobject-scan` RE-SCAN scope | Upstream — re-generates `coverage_gaps` after a UI change. Trigger this skill after RE-SCAN if new gaps appear. |
| `living-doc-scenario-creator` | Downstream — after Functionalities are promoted from `planned` to `active`, generate Gherkin scenarios for them. |
| `living-doc-update` | Downstream — if PageObject header `status` changes, the corresponding Feature entity in the living doc may also need a status update. |

**Pipeline position:**
```
living-doc-pageobject-scan (or RE-SCAN)  →  data-cy-instrument
  →  living-doc-update  (promote Functionalities: planned → active)
  →  living-doc-scenario-creator
```

---

## Out-of-scope routing

| Request | Correct skill |
|---|---|
| Add or fix Gherkin scenarios | `living-doc-scenario-creator` |
| Generate or heal PageObjects (no missing data-cy) | `living-doc-pageobject-scan` |
| Fix selector drift from DOM structure changes (no missing data-cy) | `living-doc-pageobject-scan` HEALING scope |
| Deprecate a Functionality entity | `living-doc-update` |
