---
name: living-doc-pageobject-scan
description: >
  Discover, create, and maintain PageObject classes for webapp exploration.
  Covers seed.yaml assembly, MCP Playwright crawl, entity harvesting, PageObject generation,
  Functionality stubs, and manifest.json output.
  Three scopes: CREATE (first scan), RE-SCAN (full manifest refresh after UI changes),
  HEALING (fix selector drift in failing tests only).
  Triggers on: "scan this webapp", "generate pageobjects", "crawl the UI", "discover routes",
  "seed.yaml", "manifest.json", "first scan", "create page objects", "pageobject drift",
  "re-scan", "refresh manifest", "heal pageobjects", "fix failing e2e tests after UI changes",
  "selector drift", "generate functionality stubs", "bootstrap pageobjects".
  Does NOT trigger for: adding/fixing Gherkin (use living-doc-scenario-creator); resolving
  missing data-cy (use data-cy-instrument); deleting deprecated BDD files (use bdd-maintain);
  ordinary unit/integration test failures (use test-unit-write/test-unit-review).
license: Apache-2.0
---

# Living Doc — PageObject Scan & Webapp Exploration

> **Glossary:** Feature, PageObject, Functionality — see [living-doc-glossary](../shared/references/living-doc-glossary.md).
> **BDD schemas:** Project Profile, seed.yaml, manifest.json, PageObject file header — see [living-doc-bdd-schemas](../shared/references/living-doc-bdd-schemas.md). Machine-readable contracts: [schemas/](../shared/references/schemas/).

**Scope:** UI Features only. API surfaces such as `/api/orders` use **Functionality** entities, not PageObjects — route them to `living-doc-create-functionality`. Before any mode, load `<bdd_artifacts_dir>/.project-profile.yaml` (default `.copilot/bdd/.project-profile.yaml`) for the test-id attribute, paths, and state vocabularies; create it from the [Project Profile schema](../shared/references/living-doc-bdd-schemas.md#project-profile-config-driven-conventions) on first run. Default paths or `data-cy` yield to the profile. **Selector preference:** `getByTestId()` (profile `test_id_attribute`, default `data-cy`) > `aria-label`/role > CSS class; positional selectors are `FRAGILE`.

## Two modes

| Mode | Input | Use when |
|---|---|---|
| **Create** (initial scan) | App URL or test suite root | No PageObjects exist — bootstrapping or first session on a new app |
| **Maintain — RE-SCAN** | Existing PageObject files + current app | UI refactored, new feature shipped, or significant route changes — full manifest refresh |
| **Maintain — HEALING** | Failing test names / scenario titles | Test suite failures due to selector drift — failing tests only, do not touch passing tests |

## Pre-flight: MCP Playwright availability check

Run this check **before any other step, in every mode**:
1. Call any MCP Playwright browser tool with a no-op argument (for example the `*browser_snapshot*` tool from `@playwright/mcp`). Tool names vary by server build (for example `mcp_playwright2_browser_snapshot`) — use the browser tools your environment exposes; do not hardcode a prefix.
2. On the first successful call, record the working prefix (for example `mcp_playwright2_browser_`) in `<paths.bdd_artifacts>/.session-state.md` under `mcp_browser_prefix:` and reuse it for the session.
3. If the call succeeds, continue. If it fails or no tool is available, **stop immediately** — no static fallbacks, route-config inference, seed assembly, guided traversal, or DOM interaction. Output exactly:

   > **MCP Playwright server is not available.**
   > This skill requires the `@playwright/mcp` (or equivalent) MCP server to be running and connected.
   > Please enable it in your VS Code MCP configuration (`.vscode/mcp.json` or user settings) and restart the agent session, then retry.

   Do not attempt any crawl, seed assembly, or DOM interaction until the user confirms the server is available.

**Dry-run / example-answer exception:** for expected output shapes or starter artifacts — e.g. **"bootstrap a PageObject for /checkout"** or **"Maintain mode output?"** — provide the PageObject / manifest / report shape from the route and elements unless the prompt says MCP is unavailable. Reserve the hard stop above for unavailable MCP or scan/rescan requests.

## Create mode

### Step 0 — Business Seed assembly

Before crawling: (1) find `seed.yaml` (`base_url:`) and `manifest.json` (`pageobject_path` entries); (2) if both exist, load them and resume; (3) otherwise create them in the living-doc directory or `.copilot/bdd/`; (4) on first discovery, propose adding both paths to `.github/copilot-instructions.md`:

```markdown
## BDD Artifacts
- **Business Seed:** `<path>/seed.yaml`
- **Exploration Manifest:** `<path>/manifest.json`
```

Collect seed content from any available source:

| Source | Behaviour |
|---|---|
| **A — Living documentation** | Extract Feature names, US titles, AC texts, and primary routes. |
| **B — Sitemap / route config** | Parse router config or `sitemap.xml` for URL paths. |
| **C — OpenAPI / Swagger** | Extract endpoint paths; map REST resources to UI screens where obvious. |
| **D — Existing PageObjects** | Load current `manifest.json`; treat known surfaces as already discovered. |
| **E — Guided traversal** | See [Guided Traversal Protocol](#guided-traversal-protocol-source-e) below. |

**Rules:** Never store credential literals in `seed.yaml` — use `credentials_source` or `env:VAR_NAME`. For the full Business Seed shape (`app`, `business_domains`, `known_entities`, `user_roles`, `form_fixtures`) see [living-doc-bdd-schemas — seed.yaml](../shared/references/living-doc-bdd-schemas.md#seedyaml-business-seed); do not invent another shape. If `seed.yaml` exists and `manifest.json` does not, treat it as first run: start from `base_url` and assume nothing is discovered.

### Step 1 — Crawl

Navigate each route in `seed.yaml` via MCP Playwright. Snapshot the DOM; identify interactive elements, forms, links, and significant UI surfaces; follow links to routes not yet in the manifest.

**Crawl rules:** record parameterised values read from the DOM (domain ID, version, feed ID, etc.) under `seed.yaml known_entities` with `id`, `version`, `name`, `status`, `owner`, `note`; before navigating `/path/{id}/{version}`, check `known_entities` for a value owned by the current test user and fall back to user-assist pause only if none exists; close modals/overlays (Cancel → × → Escape) before moving on.

Repeat until coverage plateau — no new surfaces in the last full iteration.

### Step 2 — Auth handling

| Auth type | Strategy |
|---|---|
| Cookie/session | Log in once via Playwright `storageState`; reuse across routes. |
| OAuth/OIDC | Inject a pre-issued test token via `localStorage` or `Authorization` header. |
| MFA-protected | Use test account with MFA disabled, or TOTP library with known seed. |
| Multi-step wizard | Parse existing step definitions to reconstruct navigation sequence. |

### Step 3 — Form traversal (deep exploration)

Resolve field values using the **ExplorationFixture sourcing cascade** (see [living-doc-bdd-schemas](../shared/references/living-doc-bdd-schemas.md#explorationfixture)): (1) `seed.yaml form_fixtures`; (2) copied/derived value from an existing entity; (3) inferred `fake` value from label + placeholder + tooltip; (4) user-assist pause for `real-world` fields and record `source: user_provided`.

Skip `condition`-gated fields until the controlling field has the required value. After submit, probe each text input for special characters (`<>'"&\``), oversized input (200+ chars), wrong type, and duplicate value; after each probe, run the core scan to capture error elements (in the profile `test_id_attribute`) visible only in error state and record them in `field_constraints[]`.

#### Angular CPS component interactions

> **Angular-specific.** For React/Vue, adapt component resolution; all other steps stay the same.

| Component | Correct interaction |
|---|---|
| `cps-radio-group` | `browser_click` the inner `<label>` or `<span>` matching option text. Do NOT use `fill()`. |
| `cps-select` | `browser_click` to open portal, then `browser_click` `<li>` by text. |
| `cps-autocomplete` | `browser_type` into inner `<input>`, wait for dropdown, `browser_click` option. |
| `cps-switch` / `cps-checkbox` | `browser_click` the wrapper. |
| `app-text-editor` (rich text) | `browser_click` `contenteditable` child, then `browser_type`. |
| `cps-button` | `browser_click` the inner `<button>` (or `evaluate`: `el.querySelector('button').click()`). |
| `input[type=file]` | the MCP browser file-upload tool or `page.setInputFiles()` with fixture path from `seed.yaml`. |

After interacting with a required field (e.g. `cps-radio-group`), re-check whether gated buttons (Continue, Save) are now enabled.

### Step 4 — Generate PageObject skeleton

Create one class per screen named `<ScreenName>Page`. Every PageObject file starts with the full living-doc header block (`surface_type`, `route`, `owners`, `status`, `purpose`, `user_stories`, `functionalities`, `external_dependencies`, `page-object`) — see [living-doc-bdd-schemas — PageObject File Header](../shared/references/living-doc-bdd-schemas.md#pageobject-file-header). Secondary files sharing one Feature use the cross-reference header. Locators use `getByTestId()`.

For starter bootstrap answers, say **Create mode** and emit real code, not pseudocode. For `/checkout`, materialise concrete members/methods for the promo input, confirm-order button, and error banner (`enterPromoCode` / `enter_promo_code`, `confirmOrder` / `confirm_order`, `assertErrorVisible` / `assert_error_visible`) in the class body — never as TODOs. If no matching Feature exists in the catalog, explicitly propose drafting it via `living-doc-create-feature`.

```typescript
/* LIVING DOC — FEAT-003 · Checkout
 * surface_type: UI
 * route: /checkout
 * owners: <Team>
 * status: active
 * purpose: Checkout screen to confirm and pay for an order.
 * user_stories: US-7
 * functionalities: FUNC-005
 * external_dependencies: none
 * page-object: CheckoutPage.ts */
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
# same living-doc fields, as a module docstring or comment block
class CheckoutPage:
    ROUTE          = '/checkout'
    CONFIRM_BUTTON = '[data-cy="confirm-order-btn"]'   # profile test_id_attribute
    PROMO_INPUT    = '[data-cy="promo-code-input"]'
    ERROR_BANNER   = '[data-cy="error-banner"]'

    def __init__(self, page, base_url=''):
        self.page = page

    def confirm_order(self): self.page.click(self.CONFIRM_BUTTON)
    def enter_promo_code(self, code): self.page.fill(self.PROMO_INPUT, code)
    def assert_error_visible(self, msg): expect(self.page.locator(self.ERROR_BANNER)).to_contain_text(msg)
```

Flag fragile selectors with `# FRAGILE`, recommend adding the profile `test_id_attribute` (for example `data-cy='<descriptive-name>'`), and keep the current selector so authoring is not blocked.

### Step 5 — Map PageObjects to Feature entities

One PageObject ≈ one `UI` Feature. Write the full living-doc header block (see schema ref) with `feature_id`/`route`, and record `feature_id` in the manifest.

- Feature exists → add header and manifest entry.
- No Feature → write `FEAT-UNKNOWN`, flag **"needs Feature entity"** in the scan report, and propose drafting `FEAT-<nnn>` via `living-doc-create-feature`; replace `FEAT-UNKNOWN` in the header and manifest after the Feature exists. Do not auto-create it from this skill.

### Step 6 — Generate Functionality stubs

For each discovered behavior, propose a stub named `<Feature name> – <behavior phrase>`:

- Button → `"Checkout Page – Confirm Order"`
- Form → `"Login Page – Submit Credentials"`
- Table → `"Order History Page – Display Order List"`

Output to `<feature_dirs.functionality>/func-<nnn>-<kebab>.feature` (default `features/liv_doc_func/`) with `@FUNC_ID:FUNC-UNKNOWN`. Promote via `living-doc-create-functionality` once IDs are assigned.

**Post-Create pipeline:**
- Non-empty `coverage_gaps` in the manifest → trigger `data-cy-instrument` to add missing `data-cy` attributes.
- PageObjects with `FEAT-UNKNOWN` placeholders → create Feature entities using `living-doc-create-feature`.
- Functionality stubs with `FUNC-UNKNOWN` → register Functionalities using `living-doc-create-functionality`.
- New surfaces with no Gherkin coverage → use `living-doc-scenario-creator` to generate scenarios.

## Guided Traversal Protocol (Source E)

Use when automated crawling cannot proceed: multi-step wizards, auth flows, role-gated screens, or forms missing business knowledge.

1. Screenshot and show the user what the agent sees.
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

**CAPTCHA:** pause, ask the user to solve it manually, continue after confirmation, record `action: captcha_solved`.

## Maintain mode

**Pre-flight:** run the MCP availability check above; stop if unavailable. Maintain mode has two scopes — activate the one that matches the trigger.

| Scope | Trigger | Breadth |
|---|---|---|
| **RE-SCAN** | New feature shipped, UI refactored, or significant route changes | Full manifest — all routes re-visited, new routes actively discovered |
| **HEALING** | Test suite failures due to selector drift or PageObject mismatch | Failing tests only — do not touch passing tests or unrelated PageObjects |

### RE-SCAN scope

#### Step 0 — Load and prioritise

Read `manifest.json`. Sort by `last_scanned` ascending.

```bash
python scripts/manifest_diff.py --manifest .copilot/bdd/manifest.json --pages-dir tests/pages
python scripts/manifest_diff.py --manifest .copilot/bdd/manifest.json --pages-dir tests/pages --diff
```

#### Steps 1–3 — Diff, detect, update

Before navigating an authenticated or multi-step route (for example `/admin/orders`), read its `navigation_context` **string** from `manifest.json`: use it if present, ask the team to add it if empty/missing, and never skip the route because auth is required — apply the Create-mode auth strategy and continue.

Navigate each route using the recorded `navigation_context` if present. For each selector:

| State | Action |
|---|---|
| Present, unchanged | No action |
| Present, changed | Update constant; log `UPDATED` with new value |
| Missing | Flag `BREAKING CHANGE`; annotate constant `# BREAKING`; never auto-delete |

Propose additions for new elements. Update selector constants only; never auto-delete methods. If any remaining selector is positional, flag it `FRAGILE` and recommend adding a stable test-id/data-testid attribute.

**Actively discover new routes** — do not limit discovery to routes already in `manifest.json`. On each snapshot:
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

Also link each broken selector to the affected step text and `.feature` line (for example `When the customer confirms the order` → `checkout.feature:14`). Use the formal `BREAKING CHANGE` wording in the report/output.

Preferred phrasing: `Linked step: "When the customer confirms the order" (checkout.feature:14)`.

#### Step 5 — Update manifest and register new routes

After confirming changes: set `last_scanned`, update `elements`, `coverage_gaps`, and `navigation_context`; add new surfaces; mark removed surfaces as `deprecated`; generate scenarios for newly discovered ACs via `living-doc-scenario-creator`.

**Post-RE-SCAN pipeline:**
- Non-empty `coverage_gaps` → trigger `data-cy-instrument` to add missing `data-cy` attributes.
- New routes without PageObjects → continue in Create mode for those surfaces.
- Deprecated surfaces → trigger `bdd-maintain` REMOVE mode to clean up associated automation files.

### HEALING scope

**Before starting:** require the failing scenario titles; do not proceed without a confirmed scope.

1. Trace each failing scenario to its PageObject and step definition.
2. Navigate to the affected page via MCP Playwright; snapshot the current DOM.
3. Find updated element IDs or selectors; update only the affected PageObject(s).
4. Verify the step definition binding still resolves; fix if broken.
5. Re-run only the previously failing tests to confirm healing. Do not re-run the full suite.

> **Scope boundary with `gherkin-living-doc-sync`:** HEALING mode fixes selector drift in PageObjects and step bindings. It does not resync `@AC:` traceability tags or correct scenario wording in `.feature` files. If healing reveals feature-file text drift, trigger `gherkin-living-doc-sync`.

## Manifest schema

`manifest.json` `routes` is a **JSON array** of route objects. Each entry uses normalized `test_id` for elements, `suggested_test_id` for gaps, and a **string** `navigation_context`. Root-level `test_id_attribute` metadata maps these keys to the configured HTML attribute. The authoritative schema (route fields, `coverage_gaps[]`, optional `open_actions_menu`, `field_constraints[]`) lives in [living-doc-bdd-schemas — manifest.json](../shared/references/living-doc-bdd-schemas.md#manifestjson-exploration-manifest). Do not emit object-keyed routes, `test_id_*` snake-case variants, or object `navigation_context`.

```json
{"test_id_attribute":"data-cy","routes":[{"elements":[{"test_id":"confirm-order-btn"}],"coverage_gaps":[{"suggested_test_id":"promo-info"}],"navigation_context":"log in, open checkout"}]}
```

Before closeout, validate and canonicalize with `python skills/living-doc-pageobject-scan/scripts/validate_artifacts.py manifest <bdd_artifacts>/manifest.json --canonicalize`.

## Output artifacts

All paths come from the Project Profile (`paths.*`, `feature_dirs.*`); the defaults below match the reference project.

| Artifact | Location (default) |
|---|---|
| PageObject files | `<paths.pageobjects>/<ScreenName>Page.ts` |
| Feature link | Full living-doc header block in the PageObject file (see schema ref) |
| Functionality stubs | `<feature_dirs.functionality>/func-<nnn>-<kebab>.feature` |
| Breaking change report | `<paths.bdd_artifacts>/breaking-changes.md` |
| Exploration manifest | `<paths.bdd_artifacts>/manifest.json` |

## Validation gate (closeout — mandatory)

Before reporting the scan complete, run the artifact validators and **do not finish while any error remains**:

```bash
# Canonicalize (sort routes by url, elements by data-cy) AND validate in one step:
python skills/living-doc-pageobject-scan/scripts/validate_artifacts.py manifest <bdd_artifacts>/manifest.json --canonicalize
python skills/living-doc-pageobject-scan/scripts/validate_artifacts.py seed     <bdd_artifacts>/seed.yaml
```

- The **manifest** check rejects object-keyed routes, `data_cy`/`suggested_data_cy` snake_case keys, and object `navigation_context`; `--canonicalize` rewrites the file with sorted routes/elements and JSON keys for stable diffs.
- The **seed** check rejects inline credential literals and malformed shape.
- If a profile is in use, also run `validate_artifacts.py profile <bdd_artifacts>/.project-profile.yaml`.
- Fix every reported error and re-run until both pass (exit code 0) before closing the session.

## Out-of-scope routing

This skill discovers or maintains PageObjects from a live UI. It does **not** generate Gherkin scenarios; use `living-doc-scenario-creator` for scenario generation from User Stories or ACs.

| Request | Correct skill |
|---|---|
| Generate BDD scenarios for a User Story | `living-doc-scenario-creator` |
| Create a User Story for this screen | `living-doc-create-user-story` |
| Resolve missing `data-cy` attributes | `data-cy-instrument` |
| Delete deprecated BDD files | `bdd-maintain` |
