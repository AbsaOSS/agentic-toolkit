---
name: living-doc-pageobject-scan
description: >
  Discover, create, and maintain PageObject classes for webapp exploration.
  Covers seed.yaml assembly, MCP Playwright crawl, entity harvesting, PageObject generation,
  Functionality stubs, and manifest.json output.
  Three scopes: CREATE (first scan), RE-SCAN (full manifest refresh after UI changes),
  HEALING (fix selector drift in failing tests only).
  Triggers on: "scan this webapp", "generate pageobjects", "crawl the UI", "explore the app",
  "discover routes", "seed.yaml", "manifest.json", "first scan", "create page objects",
  "pageobject drift", "re-scan", "refresh manifest", "heal pageobjects", "fix failing tests",
  "selector drift", "tests are failing", "generate functionality stubs",
  "bootstrap pageobjects", "bootstrap page objects".
  Does NOT trigger for: adding/fixing Gherkin (use living-doc-scenario-creator); resolving
  missing data-cy (use data-cy-instrument); deleting deprecated BDD files (use bdd-maintain).
  Pairs with data-cy-instrument, living-doc-create-feature, living-doc-scenario-creator,
  and gherkin-living-doc-sync.
license: Apache-2.0
compatibility: GitHub Copilot
---

# Living Doc — PageObject Scan & Webapp Exploration

> **Glossary:** Feature, PageObject, Functionality — see [living-doc-glossary](../references/living-doc-glossary.md) ([remote](https://github.com/AbsaOSS/agentic-toolkit/blob/master/skills/references/living-doc-glossary.md)).
> **BDD schemas:** ExplorationFixture, seed.yaml, manifest field_constraints, PageObject file header — see [living-doc-bdd-schemas](../references/living-doc-bdd-schemas.md) ([remote](https://github.com/AbsaOSS/agentic-toolkit/blob/master/skills/references/living-doc-bdd-schemas.md)).

**Scope:** UI Features only (web pages, modals, screens). API Features use annotated endpoint methods — not PageObjects.

**Selector preference:** `data-testid` > `aria-label`/role > CSS class. Flag positional selectors (`nth-child`, `first-of-type`) as `FRAGILE`.

---

## Two modes

| Mode | Input | Use when |
|---|---|---|
| **Create** (initial scan) | App URL or test suite root | No PageObjects exist — bootstrapping or first session on a new app |
| **Maintain — RE-SCAN** | Existing PageObject files + current app | UI refactored, new feature shipped, or significant route changes — full manifest refresh |
| **Maintain — HEALING** | Failing test names / scenario titles | Test suite failures due to selector drift — failing tests only, do not touch passing tests |

---

## Create mode

### Step 0 — Business Seed assembly

Before crawling, locate or create `seed.yaml` and `manifest.json`:

1. Search for `seed.yaml` containing `base_url:`; search for `manifest.json` containing `pageobject_path` entries.
2. If found, load both and resume — all manifest entries are already discovered.
3. If not found, create at the living-doc directory or `.copilot/bdd/`.
4. On first discovery, propose adding both paths to `.github/copilot-instructions.md`:

```markdown
## BDD Artifacts
- **Business Seed:** `<path>/seed.yaml`
- **Exploration Manifest:** `<path>/manifest.json`
```

Collect seed content from whichever sources are available:

| Source | Behaviour |
|---|---|
| **A — Living documentation** | Extract Feature names, US titles, AC texts, and primary routes. |
| **B — Sitemap / route config** | Parse Angular router, React Router, or `sitemap.xml` for URL paths. |
| **C — OpenAPI / Swagger** | Extract endpoint paths; map REST resources to UI screens where obvious. |
| **D — Existing PageObjects** | Load current `manifest.json` — treat known surfaces as already discovered. |
| **E — Guided traversal** | See [Guided Traversal Protocol](#guided-traversal-protocol-source-e) below. |

**Credential rule:** Never store literals in `seed.yaml`. Always use `env:VAR_NAME`:

```yaml
base_url: https://...
credentials:
  username: env:BDD_USERNAME
  password: env:BDD_PASSWORD
known_routes:
  - path: /login
    feature: Authentication
guided_steps: []
form_fixtures: {}
```

**Partial state rule:** `seed.yaml` present, `manifest.json` absent = first run. Begin crawl from `base_url`; do not assume any surfaces are discovered.

### Step 1 — Crawl

Navigate each route in `seed.yaml` via MCP Playwright. Snapshot DOM; identify interactive elements, forms, navigation links, significant UI surfaces. Follow links to find new routes not yet in manifest.

**Entity harvesting:** when a domain ID, version, feed ID, or other parameterised value is read from the DOM, record it under `known_entities` in `seed.yaml` (fields: `id`, `version`, `name`, `status`, `owner`, `note`). Use before prompting the user for parameterised route values.

**Parameterised routes:** check `seed.yaml known_entities` for a match owned by the current test user before navigating `/path/{id}/{version}`. Only fall back to user-assist pause if none exists.

**Dismiss rule:** close any modal/overlay (Cancel → × → Escape) before moving to the next route.

Repeat until coverage plateau — no new surfaces in the last full iteration.

### Step 2 — Auth handling

| Auth type | Strategy |
|---|---|
| Cookie/session | Log in once via Playwright `storageState`, reuse across routes. |
| OAuth/OIDC | Inject pre-issued test token via `localStorage` or `Authorization` header. |
| MFA-protected | Use test account with MFA disabled, or TOTP library with known seed. |
| Multi-step wizard | Parse existing step definitions to reconstruct navigation sequence. |

### Step 3 — Form traversal (deep exploration)

Resolve field values using the **ExplorationFixture sourcing cascade** (see [living-doc-bdd-schemas](../references/living-doc-bdd-schemas.md#explorationfixture)):

1. `seed.yaml form_fixtures` pre-declared value for this route + field.
2. Value copied from an existing entity (`copyable`), or suffixed to avoid duplicate rejection (`derived`).
3. Inferred `fake` value from label + placeholder + tooltip.
4. User-assist pause for `real-world` fields — record to `form_fixtures` as `source: user_provided`.

Skip `condition`-gated fields until the controlling field holds the required value.

After successful submit, probe each text input: special characters (`<>'"&\`), oversized input (200+ chars), wrong type, duplicate value. Run core scan after each probe to capture `data-cy` error elements visible only in error state. Record in `navigation_context.field_constraints`.

#### Angular CPS component interactions

> **Angular-specific.** For React/Vue, adapt component resolution; all other steps apply unchanged.

| Component | Correct interaction |
|---|---|
| `cps-radio-group` | `browser_click` inner `<label>` or `<span>` matching option text. Do NOT use `fill()`. |
| `cps-select` | `browser_click` to open portal, then `browser_click` `<li>` by text. |
| `cps-autocomplete` | `browser_type` into inner `<input>`, wait for dropdown, `browser_click` option. |
| `cps-switch` / `cps-checkbox` | `browser_click` the wrapper. |
| `app-text-editor` (rich text) | `browser_click` `contenteditable` child, then `browser_type`. |
| `cps-button` | `browser_click` inner `<button>` (or `evaluate`: `el.querySelector('button').click()`). |
| `input[type=file]` | `mcp_browser_file_upload` or `page.setInputFiles()` with fixture path from `seed.yaml`. |

After interacting with a required field (e.g. `cps-radio-group`), re-check whether gated buttons (Continue, Save) have become enabled.

### Step 4 — Generate PageObject skeleton

One class per distinct screen. Naming: `<ScreenName>Page`.

```typescript
// living-doc: FEAT-003 | /checkout
import { type Page, type Locator, expect } from '@playwright/test';

export class CheckoutPage {
    readonly confirmButton: Locator;
    readonly promoInput:    Locator;
    readonly errorBanner:   Locator;

    constructor(readonly page: Page) {
        this.confirmButton = page.getByTestId('confirm-order-btn');
        this.promoInput    = page.getByTestId('promo-code-input');
        this.errorBanner   = page.getByTestId('error-banner');
    }

    async confirmOrder(): Promise<void> { await this.confirmButton.click(); }
    async enterPromoCode(code: string): Promise<void> { await this.promoInput.fill(code); }
    async assertErrorVisible(msg: string): Promise<void> { await expect(this.errorBanner).toContainText(msg); }
}
```

```python
# living-doc: FEAT-003 | /checkout
class CheckoutPage:
    ROUTE          = '/checkout'
    CONFIRM_BUTTON = '[data-testid="confirm-order-btn"]'
    PROMO_INPUT    = '[data-testid="promo-code-input"]'
    ERROR_BANNER   = '[data-testid="error-banner"]'

    def __init__(self, page, base_url=''):
        self.page = page

    def confirm_order(self): self.page.click(self.CONFIRM_BUTTON)
    def enter_promo_code(self, code): self.page.fill(self.PROMO_INPUT, code)
    def assert_error_visible(self, msg): expect(self.page.locator(self.ERROR_BANNER)).to_contain_text(msg)
```

Flag fragile selectors: annotate `# FRAGILE`, recommend `data-testid='<descriptive-name>'`. Keep the current selector so authoring is not blocked.

### Step 5 — Map PageObjects to Feature entities

One PageObject ≈ one `UI` Feature. Write `// living-doc: FEAT-<nnn> | <route>` as a file-level header and record `feature_id` in the manifest.

- Feature exists → add header and manifest entry.
- No Feature → write `FEAT-UNKNOWN` placeholder, flag as **"needs Feature entity"** in the scan report. Do not auto-create — raise via `living-doc-create-feature`.

### Step 6 — Generate Functionality stubs

For each discovered behavior, propose a stub named `<Feature name> – <behavior phrase>`:

- Button → `"Checkout Page – Confirm Order"`
- Form → `"Login Page – Submit Credentials"`
- Table → `"Order History Page – Display Order List"`

Output to `features/functionalities/<feat-kebab>/func-<kebab>.feature` with `@FUNC_ID:FUNC-UNKNOWN`. Promote via `living-doc-create-functionality` when IDs are assigned.

**Post-Create pipeline:**
- Non-empty `coverage_gaps` in the manifest → trigger `data-cy-instrument` to add missing `data-cy` attributes.
- PageObjects with `FEAT-UNKNOWN` placeholders → create Feature entities using `living-doc-create-feature`.
- Functionality stubs with `FUNC-UNKNOWN` → register Functionalities using `living-doc-create-functionality`.
- New surfaces with no Gherkin coverage → use `living-doc-scenario-creator` to generate scenarios.

---

## Guided Traversal Protocol (Source E)

Use when automated crawling cannot proceed — multi-step wizards, auth flows, role-gated screens, forms with missing business knowledge.

1. Screenshot; show user what the agent sees.
2. Ask: *"I've reached a decision point at [URL]. What should I do next?"*
3. Execute the action via MCP Playwright.
4. Append to `seed.yaml guided_steps`:

```yaml
guided_steps:
  - url: /checkout/payment
    action: fill
    field: card-number
    value: env:TEST_CARD_NUMBER
    note: "Test Visa card"
```

5. Continue crawl.

**CAPTCHA:** pause, ask user to solve manually, continue after confirmation, record `action: captcha_solved`.

---

## Maintain mode

Two scopes — activate the one that matches the trigger.

| Scope | Trigger | Breadth |
|---|---|---|
| **RE-SCAN** | New feature shipped, UI refactored, or significant route changes | Full manifest — all routes re-visited, new routes actively discovered |
| **HEALING** | Test suite failures due to selector drift or PageObject mismatch | Failing tests only — do not touch passing tests or unrelated PageObjects |

---

### RE-SCAN scope

#### Step 0 — Load and prioritise

Read `manifest.json`. Sort by `last_scanned` ascending.

```bash
python scripts/manifest_diff.py --manifest .copilot/bdd/manifest.json --pages-dir tests/pages
python scripts/manifest_diff.py --manifest .copilot/bdd/manifest.json --pages-dir tests/pages --diff
```

#### Steps 1–3 — Diff, detect, update

Navigate each route using `navigation_context.navigation_steps` if present. For each selector:

| State | Action |
|---|---|
| Present, unchanged | No action |
| Present, changed | Update constant; log `UPDATED` with new value |
| Missing | Flag `BREAKING CHANGE`; annotate constant `# BREAKING`; never auto-delete |

Propose additions for new elements. Update selector constants only; never auto-delete methods.

**Actively discover new routes** — do not limit discovery to routes already in `manifest.json`. On each page snapshot:
- Find all `<a href>` links that resolve to new paths not yet in the manifest.
- Find buttons whose purpose suggests navigation (e.g. "Create order", "View details") — click them and record the resulting URL.
- Find tab panels, side-nav items, and wizard steps that expose sub-routes.
- Any new URL discovered this way is a candidate manifest entry; add it and crawl it recursively.

#### Step 4 — Breaking change report

Overwrite `.copilot/bdd/breaking-changes.md`:

```markdown
# Breaking Changes Report
Generated: <ISO> | Scope: <full|healing|scoped>

## <route>
| Selector | Status | Linked test | Action |
|---|---|---|---|
| `Page.locatorName` | REMOVED | `file.feature:<line>` | Verify removed or renamed |
```

#### Step 5 — Update manifest and register new routes

After confirming changes: set `last_scanned`, update `elements` and `coverage_gaps`, update `navigation_context`. Add new surfaces; mark removed surfaces as `deprecated`. Generate new scenarios for newly discovered ACs (load `living-doc-scenario-creator`).

**Post-RE-SCAN pipeline:**
- Non-empty `coverage_gaps` → trigger `data-cy-instrument` to add missing `data-cy` attributes.
- New routes without PageObjects → continue in Create mode for those surfaces.
- Deprecated surfaces → trigger `bdd-maintain` REMOVE mode to clean up associated automation files.

---

### HEALING scope

**Before starting:** ask for the list of failing scenario titles if not provided — do not proceed without a confirmed scope.

1. Trace each failing scenario to its PageObject and step definition.
2. Navigate to the affected page via MCP Playwright; snapshot the current DOM.
3. Find updated element IDs or selectors; update only the affected PageObject(s).
4. Verify the step definition binding still resolves; fix if broken.
5. Re-run only the previously failing tests to confirm healing. Do not re-run the full suite.

> **Scope boundary with `gherkin-living-doc-sync`:** HEALING mode fixes selector drift in PageObject classes and step definition bindings. It does not resync `@AC:` traceability tags or correct scenario wording in `.feature` files. If healing reveals that feature file step text also drifted, trigger `gherkin-living-doc-sync` to realign the feature files.

---

## Manifest schema

```json
{
  "version": "1.0",
  "routes": {
    "/auth/all-domains": {
      "pageobject_path": "playwright/pages/AllDomainsPage.ts",
      "feature_id": "FEAT-001",
      "last_scanned": "2026-05-26T10:30:00Z",
      "elements": [{ "data_cy": "create-domain-btn", "tag": "cps-button" }],
      "coverage_gaps": [{ "tag": "input", "placeholder": "Search", "suggested_data_cy": "domains-search-input" }],
      "navigation_context": {
        "prerequisites": "User must be logged in.",
        "navigation_steps": "Click sidebar 'All Domains'.",
        "data_requirements": null,
        "auth_role": "standard user",
        "notes": null,
        "field_constraints": []
      }
    }
  }
}
```

| Field | Purpose |
|---|---|
| `last_scanned` | ISO 8601 timestamp; surfaces stale entries. |
| `elements` | All `data-cy` elements at last scan. |
| `coverage_gaps` | Interactive elements lacking `data-cy`; with suggested names. |
| `pageobject_path` | Relative path to PageObject file. |
| `feature_id` | Living doc Feature entity ID. |
| `navigation_context` | How to reach hard-to-access routes; reused in all subsequent sessions. |
| `navigation_context.field_constraints` | Per-field validation findings. Schema: `{ field_data_cy, max_length, special_chars, duplicate, duplicate_error_data_cy, real_world_required }`. |

---

## Output artifacts

| Artifact | Location |
|---|---|
| PageObject files | `tests/pages/<ScreenName>Page.py` / `.ts` |
| Feature link | `// living-doc: FEAT-<nnn> | <route>` header comment |
| Functionality stubs | `features/functionalities/<feat-kebab>/func-<kebab>.feature` |
| Breaking change report | `.copilot/bdd/breaking-changes.md` |
| Exploration manifest | `.copilot/bdd/manifest.json` |

> Paths are defaults — actual locations depend on the project's Storage Profile.

---

## Out-of-scope routing

| Request | Correct skill |
|---|---|
| Generate BDD scenarios for a User Story | `living-doc-scenario-creator` |
| Create a User Story for this screen | `living-doc-create-user-story` |
| Resolve missing `data-cy` attributes | `data-cy-instrument` |
| Delete deprecated BDD files | `bdd-maintain` |

