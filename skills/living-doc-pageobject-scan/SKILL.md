---
name: living-doc-pageobject-scan
description: >
  Explore an existing web application or test codebase to discover, create, and maintain PageObject
  classes — the bottom-up entry point for BDD-driven UI testing. Use when generating PageObjects
  from a live webapp URL or test directory, updating PageObjects after UI changes, bootstrapping
  a test suite for a new screen, generating Functionality stubs from discovered UI elements,
  updating the PageObject manifest after a redesign, or detecting PageObject drift.
  Triggers on: "scan this webapp", "generate pageobjects", "update pageobjects",
  "pageobject for this screen", "crawl the UI", "discover UI elements", "create page objects",
  "scan test suite for pageobjects", "living doc bottom-up", "bootstrap page objects",
  "pageobject drift", "sync pageobjects", "update manifest", "functionality stubs from UI".
  Does NOT trigger for: creating User Stories (use living-doc-create-user-story), writing BDD
  scenarios (use living-doc-scenario-creator). Pairs with living-doc-create-functionality
  and living-doc-gap-finder.
---

# Living Doc — PageObject Scan

> **Glossary:** Feature, PageObject, Functionality — see [living-doc-glossary](../references/living-doc-glossary.md) ([remote](https://github.com/AbsaOSS/agentic-toolkit/blob/master/skills/references/living-doc-glossary.md)).

**Scope:** This skill generates PageObjects only for `UI` Features (web pages, modals, screens).
API Features use annotated endpoint methods as their living contract anchor — not PageObjects.

**Selector preference (from glossary):** `data-testid` > `aria-label`/role > CSS class.
Flag any element that only has positional CSS selectors (`nth-child`, `first-of-type`) as fragile
and recommend the development team add a `data-testid` attribute.

---

## Two modes

| Mode | Input | Use when |
|---|---|---|
| **Create** (initial scan) | App URL or test suite root | No PageObjects exist yet — bootstrapping from scratch |
| **Maintain** (rescan/update) | Existing PageObject files + current app | UI has changed; detect drift and update |

---

## Create mode — initial scan

### Inputs

- `url`: root URL of the web application (authenticated access if needed)
- `dir`: path to an existing test suite with step files or PageObject skeletons

### Workflow

**1. Crawl the web application**

Traverse all reachable routes from the root URL:
- Enumerate all distinct routes (paths and query patterns)
- On each route: capture the rendered DOM
- For SPAs: trigger navigation events to reach client-side routes

**Handling authenticated routes:**

| Auth type | Strategy |
|---|---|
| Cookie/session | Log in once via Playwright `storageState` and reuse across routes |
| OAuth / OIDC | Inject a pre-issued test token via `localStorage` or `Authorization` header |
| MFA-protected | Use a dedicated test account with MFA disabled, or a TOTP library with a known seed |
| Multi-step wizard | Parse existing step definitions to reconstruct the navigation sequence |

**2. Discover elements per screen**

For each distinct screen/route, extract:
- Interactive elements: buttons, links, form inputs, dropdowns, checkboxes
- Display elements: tables, lists, notifications, modals
- Page-level: title, heading (h1), primary URL pattern

**3. Generate PageObject skeleton**

One PageObject class per distinct screen. Naming: `<ScreenName>Page`.

```python
# ✅ Generated skeleton — Python / Playwright
# living-doc: FEAT-003 | /checkout
class CheckoutPage:
    ORDER_SUMMARY  = '[data-testid="order-summary"]'
    CONFIRM_BUTTON = '[data-testid="confirm-order-btn"]'
    PROMO_INPUT    = '[data-testid="promo-code-input"]'
    ERROR_BANNER   = '[data-testid="error-banner"]'

    def __init__(self, page):
        self.page = page

    def enter_promo_code(self, code: str) -> None:
        self.page.fill(self.PROMO_INPUT, code)

    def confirm_order(self) -> None:
        self.page.click(self.CONFIRM_BUTTON)

    def assert_error_visible(self, message: str) -> None:
        expect(self.page.locator(self.ERROR_BANNER)).to_contain_text(message)
```

```typescript
// ✅ Generated skeleton — TypeScript / Playwright
// living-doc: FEAT-003 | /checkout
import { type Page, type Locator, expect } from '@playwright/test';

export class CheckoutPage {
    readonly orderSummary:  Locator;
    readonly confirmButton: Locator;
    readonly promoInput:    Locator;
    readonly errorBanner:   Locator;

    constructor(readonly page: Page) {
        this.orderSummary  = page.getByTestId('order-summary');
        this.confirmButton = page.getByTestId('confirm-order-btn');
        this.promoInput    = page.getByTestId('promo-code-input');
        this.errorBanner   = page.getByTestId('error-banner');
    }

    async enterPromoCode(code: string): Promise<void> {
        await this.promoInput.fill(code);
    }

    async confirmOrder(): Promise<void> {
        await this.confirmButton.click();
    }

    async assertErrorVisible(message: string): Promise<void> {
        await expect(this.errorBanner).toContainText(message);
    }
}
```

The Living Doc Feature link (`FEAT-<nnn>`) is recorded in a file-level header comment (see
examples above) — not in the class docstring. The exact multi-field header format for
PageObject files is TBD and will follow similar conventions to the US/FUNC feature file header.

Flag fragile selectors:

> "Element `<description>` has a positional CSS selector. Please add:
> `data-testid='<descriptive-kebab-name>'` — e.g. `data-testid='confirm-order-btn'`"

Still include the current selector in the generated PageObject so test authoring is not blocked, but
annotate that selector constant with a `FRAGILE` comment and repeat the warning in the scan / breaking
change report.

**4. Map PageObjects to Feature entities**

One PageObject ≈ one `UI` Feature. Write the Feature ID as a header comment in the generated PageObject file (the `// living-doc: FEAT-<nnn> | <route>` line shown in the templates above). Also record `feature_id` in the manifest entry for the route.

- If a matching Feature (`FEAT-<nnn>`) exists in the living documentation: add the header comment and manifest entry.
- If no Feature exists: write `// living-doc: FEAT-UNKNOWN | <route>` as a placeholder and flag the route in the scan report as **"needs Feature entity"**. Do not auto-create a Feature file — raise it for the team to create via `living-doc-create-feature`.

**5. Generate Functionality stubs from discovered behaviors**

For each **behavior** identified on the screen — an interaction pattern, business operation, or
component capability — propose a Functionality stub (`FUNC-<nnn>`) with a name following
the glossary pattern `<Feature name> – <behavior phrase>`:

- Button: `"Checkout Page – Confirm Order"`
- Form: `"Login Page – Submit Credentials"`
- Table: `"Order History Page – Display Order List"`

Note: a Functionality represents a business behavior, not an individual UI element. One interactive
element may map to one Functionality, or a group of elements may represent a single behavior.
The team decides the appropriate granularity when promoting stubs.

Output Functionality feature file stubs to `features/functionalities/<feat-kebab>/func-<kebab>.feature`
with `@FUNC_ID:FUNC-UNKNOWN` placeholder tags for team review. When the Functionality is confirmed
and an ID is assigned, use `living-doc-create-functionality` to populate the canonical entity file.

**Dynamic list elements:**

```python
# ✅ — dynamic lists: use locator methods, not positional selectors
def get_cart_items(self):
    return self.page.locator('[data-testid="cart-item"]').all()

def get_cart_item_by_sku(self, sku: str):
    return self.page.locator(f'[data-testid="cart-item"][data-sku="{sku}"]')
```

---

## Maintain mode — rescan and update

**0. Load manifest and prioritise routes**

Read `.copilot/bdd/manifest.json`. Sort routes by `last_scanned` ascending (oldest first). For focused healing (triggered by failing tests or a PR), filter to the routes linked to the failing test files or the changed UI paths provided by the caller.

**1. Diff existing PageObjects against current DOM**

For each route to scan, navigate using `navigation_context.navigation_steps` if present — this avoids rediscovering hard-to-reach routes. For each selector in the existing PageObject, check if it still resolves:
- **Present and unchanged**: no action
- **Present but changed**: update selector; log as `UPDATED`; if the replacement selector is evident
  (for example a renamed `data-testid`), report the exact new selector in the action required line
- **Missing**: flag as `BREAKING CHANGE` — linked test steps may fail

**2. Detect new elements**: propose additions.

**3. Update PageObject files** — modify selector constants only. Preserve existing action and
assertion method logic. Never auto-delete methods — flag removals for developer review. For missing
selectors, keep the selector constant and annotate it with a `BREAKING` comment so developers can
review whether the element was removed or renamed.

**4. Breaking change report**

Write results to `.copilot/bdd/breaking-changes.md`. The file has a fixed structure and is overwritten on each scan:

```markdown
# Breaking Changes Report

Generated: <ISO timestamp>  
Scan scope: <full | healing | scoped>

## <route-path>

| Selector | Status | Linked test | Action |
|---|---|---|---|
| `PageObject.locatorName` | REMOVED | `feature-file.feature:<line>` | Verify if element was removed or renamed |
| `PageObject.otherLocator` | CHANGED | — | Update selector constant |

## Routes needing a Feature entity

| Route | PageObject | Reason |
|---|---|---|
| `/auth/settings` | `SettingsPage.ts` | No matching FEAT-xxx found in the living documentation |
```

**5. Update manifest**

After confirmation of all changes, update the manifest entry for each scanned route:
- Set `last_scanned` to the current ISO 8601 timestamp.
- Update `elements` and `coverage_gaps` to reflect the current DOM state.
- Populate or update `navigation_context` if new information was gathered about how to reach the route.

Use `scripts/manifest_diff.py` to detect stale manifest entries and undocumented PageObject
files before running a full rescan.

---

## Output artifacts

| Artifact | Location |
|---|---|
| PageObject files | `tests/pages/<ScreenName>Page.py` (or `.ts`) |
| Feature link | `// living-doc: FEAT-<nnn> \| <route>` header comment in the PageObject file. If no Feature exists: `FEAT-UNKNOWN` placeholder and a note in the scan report. Header format TBD — will follow similar conventions to the US/FUNC feature file header. |
| Functionality feature file stubs | `features/functionalities/<feature-kebab>/func-<kebab>.feature` — one file per discovered Functionality behavior, `@FUNC_ID:FUNC-UNKNOWN` tag until ID is assigned |
| Breaking change report | `.copilot/bdd/breaking-changes.md` |
| Exploration manifest | `.copilot/bdd/manifest.json` |

> **Note:** Locations above are illustrative defaults. Actual paths depend on the project's repository structure and Storage Profile configuration.

---

## Manifest schema

The manifest records per-route exploration state. Agents and tools read it to drive healing sessions without re-discovering routes.

```json
{
  "version": "1.0",
  "routes": {
    "/auth/all-domains": {
      "pageobject_path": "aul-ui/playwright/pages/AllDomainsPage.ts",
      "feature_id": "FEAT-001",
      "last_scanned": "2026-05-26T10:30:00Z",
      "elements": [
        { "data_cy": "create-domain-btn", "tag": "cps-button" },
        { "data_cy": "domains-table",     "tag": "table" }
      ],
      "coverage_gaps": [
        { "tag": "input", "placeholder": "Search domains", "suggested_data_cy": "domains-search-input" }
      ],
      "navigation_context": {
        "prerequisites": "User must be logged in.",
        "navigation_steps": "Click sidebar item \u2018All Domains\u2019.",
        "data_requirements": null,
        "auth_role": "standard user",
        "notes": null
      }
    }
  }
}
```

| Field | Type | Purpose |
|---|---|---|
| `last_scanned` | ISO 8601 string | Timestamp of the last successful scan for this route. Used during healing to surface stale entries and prioritise rescans. |
| `elements` | array | All `data-cy` elements found on the route at last scan. |
| `coverage_gaps` | array | Interactive elements lacking `data-cy` at time of scan, with suggested names. |
| `pageobject_path` | string | Relative path to the linked PageObject file. |
| `feature_id` | string | Living doc Feature entity ID linked to this route. |
| `navigation_context` | object | **How to reach hard-to-access routes.** Populated on first discovery; reused in all subsequent healing sessions so the agent can navigate directly without re-discovering the path. |
| `navigation_context.prerequisites` | string | State that must exist before navigating (e.g. "a domain must have been visited at least once"). |
| `navigation_context.navigation_steps` | string | Step-by-step path to the route from the app root or login page. |
| `navigation_context.data_requirements` | string/null | Test data that must exist (e.g. "at least one published domain"). |
| `navigation_context.auth_role` | string | Minimum role required to reach this route. |
| `navigation_context.notes` | string/null | Any additional context for the agent (e.g. quirks, timing, overlay triggers). |

---

## Out-of-scope redirects

| Request | Correct skill |
|---|---|
| Generate BDD scenarios for a User Story | `living-doc-scenario-creator` |
| Create a User Story for this screen | `living-doc-create-user-story` |
| Document an API endpoint or REST surface | `living-doc-create-functionality` |
