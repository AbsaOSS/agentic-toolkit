---
name: living-doc-pageobject-scan
description: >
  Explore an existing web application or test codebase to discover, create, and maintain PageObject
  classes — the bottom-up entry point for BDD-driven UI testing. Activate when generating
  PageObjects from a live webapp URL or test directory, updating PageObjects after UI changes,
  bootstrapping a test suite for a new screen, linking discovered UI surfaces to Feature entities
  in the living doc, or detecting PageObject drift after a UI refactor.
  Triggers on: "scan this webapp", "generate pageobjects", "update pageobjects",
  "pageobject for this screen", "crawl the UI", "discover UI elements", "create page objects",
  "scan test suite for pageobjects", "living doc bottom-up", "bootstrap page objects",
  "pageobject drift", "sync pageobjects".
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
class CheckoutPage:
    """Checkout screen: /checkout — FEAT-003"""

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

Include the Feature ID (`FEAT-<nnn>`) in the class docstring to maintain traceability to the
living doc catalog.

Flag fragile selectors:

> "Element `<description>` has a positional CSS selector. Please add:
> `data-testid='<descriptive-kebab-name>'` — e.g. `data-testid='confirm-order-btn'`"

**4. Map PageObjects to Feature entities**

One PageObject ≈ one `UI` Feature. For each generated PageObject:
- If a matching Feature (`FEAT-<nnn>`) exists in the catalog: link them in the manifest
- If no Feature exists: generate a draft Feature stub (JSON) for `living-doc-create-feature`

**5. Generate Functionality stubs from discovered elements**

For each interactive element, propose a Functionality stub (`FUNC-<nnn>`) with a name following
the glossary pattern `<Feature name> – <behavior phrase>`:

- Button → `"Checkout Page – Confirm Order"`
- Form → `"Login Page – Submit Credentials"`
- Table → `"Order History Page – Display Order List"`

Output as draft JSON for review — not auto-committed.

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

**1. Diff existing PageObjects against current DOM**

For each selector in the existing PageObject, check if it still resolves:
- **Present and unchanged**: no action
- **Present but changed**: update selector; log as `UPDATED`
- **Missing**: flag as `BREAKING CHANGE` — linked test steps may fail

**2. Detect new elements** → propose additions.

**3. Update PageObject files** — modify selector constants only. Preserve existing action and
assertion method logic. Never auto-delete methods — flag removals for developer review.

**4. Breaking change report:**

```
BREAKING CHANGES DETECTED:
  CheckoutPage.CONFIRM_BUTTON: '[data-testid="confirm-order-btn"]' not found in DOM
    → Linked step: "When the customer confirms the order" (checkout.feature:14)
    → Action required: verify selector and update, or remove step if element is gone
```

Use `scripts/manifest_diff.py` to detect stale manifest entries and undocumented PageObject
files before running a full rescan.

---

## Output artifacts

| Artifact | Location |
|---|---|
| PageObject files | `tests/pages/<ScreenName>Page.py` |
| Draft Feature stubs | `docs/living-doc/features/draft/FEAT-<name>.json` |
| Draft Functionality stubs | `docs/living-doc/functionalities/draft/FUNC-<name>.json` |
| Breaking change report | stdout / PR comment |
| Exploration manifest | Path discovered by agent on session start (search for `manifest.json` with `pageobject_path` entries); created at `.copilot/bdd/manifest.json` only if no existing manifest is found |

---

## Out-of-scope redirects

| Request | Correct skill |
|---|---|
| Generate BDD scenarios for a User Story | `living-doc-scenario-creator` |
| Create a User Story for this screen | `living-doc-create-user-story` |
