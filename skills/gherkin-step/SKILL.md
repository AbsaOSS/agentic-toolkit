---
name: gherkin-step
description: >
  Implement Gherkin step definitions that are clean, reusable, and maintainable. Activate when
  writing or reviewing step definition code, binding Gherkin text to automation, managing shared
  state between steps, configuring parameter types, parsing DataTable or DocString arguments, or
  setting up Before/After hooks. Covers Python behave, Cucumber TypeScript/Java, and Cucumber-Scala.
  Triggers on: "step definitions", "implement Gherkin steps", "Cucumber step", "behave step",
  "parameter type", "DataTable", "DocString", "Before hook", "After hook", "World object",
  "step context", "step state sharing", "how to share state between steps",
  "register step definition", "hook setup".
  Does NOT trigger for: writing Gherkin scenarios (use living-doc-scenario-creator); writing
  unit tests (use your project's test framework).
  Pairs with living-doc-scenario-creator and living-doc-pageobject-scan (PageObjects must
  exist before step definitions reference them).
license: Apache-2.0
compatibility: GitHub Copilot
---

# Gherkin Step Definition Standards

> **Glossary:** Feature, PageObject, Functionality — see [living-doc-glossary](../references/living-doc-glossary.md) ([remote](https://github.com/AbsaOSS/agentic-toolkit/blob/master/skills/references/living-doc-glossary.md)).

> **Framework scope:** This skill covers step definition idioms for **Python behave**, **Cucumber TypeScript**, **Cucumber Java**, and **Cucumber-Scala**. The PageObject ecosystem in this toolkit uses **Playwright + TypeScript** — Python or Java projects must adapt PageObject patterns to their own test framework. All BDD principles (thin steps, no selectors in steps, context object) apply regardless of language.

## Respect the boundary with Gherkin text

If the user asks to write or review a **Gherkin scenario / feature file**, do not draft the
scenario here. Explain that this skill covers **step definition code** only, then route the user to
`living-doc-scenario-creator` for the Gherkin text itself.

---

## Context initialization — how PageObjects reach steps

> **Prerequisite:** PageObject classes must exist before step definitions can reference them. If PageObjects have not yet been generated for the screens under test, use `living-doc-pageobject-scan` first to produce them.

**Python behave:** Step definitions receive a fresh `context` object each scenario. Attach PageObjects in a `before_scenario` hook.

```python
# ✅ — Before hook initialises the PageObject once per scenario
@before_scenario
def setup_pages(context):
    context.checkout_page = CheckoutPage(context.browser.new_page())
```

**Cucumber TypeScript (Playwright):** Use a typed `World` class registered with `setWorldConstructor`.

```typescript
// world.ts
import { setWorldConstructor, World, IWorldOptions } from '@cucumber/cucumber';
import { Browser, Page } from '@playwright/test';
import { CheckoutPage } from './pages/checkout.page';

export interface AppWorld extends World {
  browser: Browser;
  page: Page;
  checkoutPage: CheckoutPage;
}

class AppWorldImpl extends World implements AppWorld {
  browser!: Browser;
  page!: Page;
  checkoutPage!: CheckoutPage;
  constructor(options: IWorldOptions) { super(options); }
}
setWorldConstructor(AppWorldImpl);
```

```typescript
// hooks.ts
Before(async function (this: AppWorld) {
  this.browser = await chromium.launch();
  this.page   = await this.browser.newPage();
  this.checkoutPage = new CheckoutPage(this.page);
});
```

**Step definition file naming:**
- One file per domain area: `checkout.steps.ts` / `checkout_steps.py`
- Place under `playwright/steps/` (TS) or `features/steps/` (Python)
- Never name a file `steps.ts` or `steps.py` — the name must identify the domain

**Given precondition state — OGP-01:** `Given` preconditions that navigate to an arbitrary element using `.first()` (or any positional selector) without asserting the domain-specific state required by the scenario create false positives. If the scenario distinguishes between, for example, a domain the user owns versus one they do not own, supply fixture-provided IDs via the env fixture (`ownedDomainId`, `nonOwnedDomainId`) rather than picking the first element from a list.

```typescript
// ✅ — uses fixture-provided ID to guarantee correct ownership state
Given('I am on the Domain Detail page for a domain I own', async ({ page, env }) => {
  await page.goto(`/auth/domain/${env.ownedDomainId}`);
});

// ❌ — both "own" and "do not own" variants resolve to the same arbitrary domain
Given('I am on the Domain Detail page for a domain I own', async ({ page }) => {
  await page.goto('/auth/all-domains');
  await page.getByTestId('domain-name-link').first().click();
});
```

---

## Function naming convention

Name step functions after the business action, not the full step text:
- `step_confirm_order` ✅ — concise, action-based
- `step_customer_confirms_the_order` ❌ — verbatim transcription of the step

---

## Keep step definitions thin

Step definitions are bindings — they translate Gherkin text into calls to PageObjects, domain
objects, or service clients. Business logic must not live in step definitions.

**Keyword rules:**
- `Given` steps must not contain assertions — they set up preconditions only
- `When` steps must not contain assertions — they perform actions only
- Assertions belong exclusively in `Then` steps
- A step body consisting only of comments is a no-op and is not permitted as a final implementation — NOP-01. If the system pre-establishes state externally, the step must assert that state is actually present rather than silently pass.

```typescript
// ✅ — pre-populated state is explicitly asserted
When('I select a domain', async ({ page }) => {
  // Domain is pre-populated from context; assert selector shows a value
  await expect(page.getByTestId('domain-selector')).not.toBeEmpty();
});

// ❌ — comment-only body; regression goes undetected
When('I select a domain', async ({ page }) => {
  // Domain is pre-selected when navigated from within a domain context
  // No additional action needed
});
```

```python
# ✅ — thin; delegates to PageObject
@when('the customer confirms the order')
def step_confirm_order(context):
    context.checkout_page.confirm_order()

# ❌ — business logic embedded in the step
@when('the customer confirms the order')
def step_confirm_order(context):
    context.cart.total *= (1 - context.discount / 100)
    context.order_status = "placed"
```

---

## Encapsulate selectors in PageObjects

Step definitions for domain-level scenarios must not contain CSS selectors, element IDs, or XPath.
Encapsulate all selector logic in PageObjects (selector preference: `data-testid` > `aria-label`/role > CSS class).

```typescript
// ✅ — PageObject hides selector details
When("the customer submits the order", async function (this: OrderWorld) {
  await this.checkoutPage.submitOrder();          // CheckoutPage owns the selector
});

// ❌ — selector leaks into the step definition
When("the customer submits the order", async function (this: OrderWorld) {
  await this.page.click('[data-testid="submit-order-btn"]');
});
```

**Pending data-cy rule — SS-01:** Do not write CSS-class-OR-data-cy fallback combos (e.g. `'.modal, [data-cy="x"]'`) in step files or PageObjects. A fallback combo either always passes (the CSS class matches when the data-cy does not exist) or always fails (neither exists), both masking real failures. If the confirmed `data-cy` attribute does not yet exist in the template:
1. Use the most stable interim selector available and mark it with `// @pending data-cy: <candidate-name>`.
2. Raise it as a gap in WORK_LOG.md §4 so it is tracked for instrumentation via `data-cy-instrument`.

```typescript
// ✅ — interim selector clearly flagged
await expect(page.locator('[role="dialog"]')).toBeVisible(); // @pending data-cy: dialog-access-request

// ❌ — fallback combo hides whether the real selector ever lands
await expect(page.locator('[role="dialog"], .access-request-form')).toBeVisible();
```

---

## Share state using the context / World object

Never use global or module-level variables — they cause test contamination across scenarios.
Use the framework-provided context object, which is instantiated fresh for each scenario.

| Framework | State object | Pattern |
|-----------|-------------|---------|
| behave (Python) | `context` | Attach attributes: `context.order = ...` |
| Cucumber (TypeScript) | `World` class | Extend `World`; access via `this` |

```python
# ✅ behave — context carries state across steps
@given('a customer with a "{tier}" membership')
def step_given_customer(context, tier):
    context.customer = Customer(tier=tier)

@then("the discount is {rate:d}%")
def step_assert_discount(context, rate):
    assert context.customer.discount_rate() == rate
```

**Hardcoded assertion rule — HTA-01:** `Then` assertions must not contain string literals that were set in a preceding `When` step (magic constants). Pass the value through the World context or as a `{string}` Cucumber parameter, or assert a structural property instead.

```typescript
// ✅ — domain name flows through World context
When('I import a domain named {string}', async function (this: AppWorld, name: string) {
  this.importedDomainName = name;
  await this.importDomainPage.importDomain(name);
});
Then('the imported domain is visible in the domain list', async function (this: AppWorld) {
  await expect(this.page.getByTestId('domain-name-link').getByText(this.importedDomainName)).toBeVisible();
});

// ❌ — hardcoded constant couples assertion to the When step's implementation detail
Then('the imported domain is visible in the domain list', async ({ page }) => {
  await expect(page.getByTestId('domain-name-link').getByText('E2E Import Test')).toBeVisible();
});
```

---

## Use typed parameters

**PTM-01 — `{string}` over `{word}` for UI labels:** Use `{string}` (quoted) for any step parameter that could contain spaces — tab names, button labels, section headings, status values. `{word}` matches only a single token without spaces and will silently fail to match multi-word values, and having both `{word}` and `{string}` variants in the same file causes Cucumber ambiguity errors. Remove all `{word}` variants and consolidate on `{string}`.

```typescript
// ✅ — {string} matches "Version management", "Run history", "About"
When('I click the {string} tab', async ({ domainDetailPage }, tab: string) => {
  await domainDetailPage.gotoTab(tab);
});

// ❌ — {word} silently fails for "Version management" and "Run history"
When('I click the {word} tab', async ({ domainDetailPage }, tab: string) => {
  await domainDetailPage.gotoTab(tab);
});
```

```python
# ✅ — :d casts to int automatically
@when("the customer purchases {quantity:d} units")
def step_purchase(context, quantity: int):
    context.cart.add_item(context.sku, quantity)
```

---

## Parse DataTable and DocString arguments

```python
# ✅ — DataTable as list of dicts
@when("the customer adds the following items")
def step_add_items(context):
    for row in context.table:
        context.cart.add_item(row["sku"], int(row["quantity"]))

# ✅ — DocString as raw text
@when("the system receives the following payload")
def step_receive_payload(context):
    context.payload = json.loads(context.text)
```

---

## Configure hooks correctly

| Hook | Use for | Must not use for |
|------|---------|-----------------|
| `before_scenario` / `Before` | Set up context state, seed data | Asserting behaviour |
| `after_scenario` / `After` | Cleanup: rollback DB, close browser | Seeding data |
| `before_all` / `BeforeAll` | Expensive one-time setup (start containers) | Per-test state |
| `after_all` / `AfterAll` | Stop containers, close connections | Per-test cleanup |

`before_scenario` runs before **every** scenario by default, so add a tag check when setup
should only apply to a subset. When explaining this pattern, say explicitly that the hook still
fires for every scenario; the `if "database" in context.tags` check only gates the expensive setup.

Tag hooks to scope them to specific scenarios, and pair setup with matching cleanup:

```python
@before_scenario
def setup_database(context):
    if "database" in context.tags:
        context.db = create_test_db()

@after_scenario
def teardown_database(context):
    if "database" in context.tags:
        context.db.teardown()
```

---

## Wizard navigation rules

Apply these rules when implementing step definitions for multi-step wizards. They detect
"cheat steps" — steps that appear to navigate a wizard but exercise no real behaviour.

### CS-01 — Assert arrival at each wizard step

Every wizard step navigation must verify arrival at the next step via a step-specific element
assertion before the step completes. Blind `continueButton.click()` chains without an arrival
assertion are forbidden: if the Continue button is disabled (validation failure), the click
silently does nothing and the test continues with a false pass.

```typescript
// ✅ — arrival at the Owner step is explicitly verified
When('I complete the About step', async ({ createDomainAboutPage, createDomainOwnerPage }) => {
  await createDomainAboutPage.fillDomainName('E2E Test Domain');
  await createDomainAboutPage.fillCostCenter('1234');
  await createDomainAboutPage.continueButton.click();
  await expect(createDomainOwnerPage.ownersTable).toBeVisible(); // arrival assertion
});

// ❌ — two blind clicks; no assertion that either step was actually reached
Given('I am on the Target dataset step', async ({ createDomainPage }) => {
  await createDomainPage.continueButton.click();
  await createDomainPage.continueButton.click();
});
```

### CS-02 — Do not use `toHaveURL()` to detect wizard step progress in a scrolling stepper

In a single-URL scrolling stepper the URL does not change between wizard steps. A
`toHaveURL(/step-name/)` assertion always passes regardless of which step is active,
giving false confidence. Assert the step-specific landmark element is visible instead.

```typescript
// ✅ — asserts the Owner step's landmark element is in view
await expect(createDomainOwnerPage.ownersTable).toBeVisible();

// ❌ — URL never changes; assertion always passes
await expect(page).toHaveURL(/owner/i);
```

Once `data-cy` attributes are added to wizard step headers, prefer:
```typescript
await expect(page.getByTestId('step-owner')).toBeVisible();
```

### CS-03 — Do not use `page.goBack()` inside an SPA wizard

`page.goBack()` navigates the browser's URL history, not the wizard's internal state. Inside
an Angular (or other SPA) wizard, this takes the user back to the *previous page* (e.g. All
Domains), not to the previous wizard step. Use the wizard's own Back button or click the
stepper step header to navigate backward.

```typescript
// ✅ — uses the wizard's own back navigation
await createDomainWizardPage.backButton.click();
await expect(createDomainAboutPage.domainNameInput).not.toBeEmpty();

// ❌ — navigates away from the wizard entirely
await page.goBack();
await expect(createDomainPage.domainNameInput).not.toBeEmpty();
```

---

## Out-of-scope routing

| Request | Correct skill |
|---|---|
| Write or review Gherkin scenarios / feature files | `living-doc-scenario-creator` |
| Generate or update PageObject classes | `living-doc-pageobject-scan` |
| Sync `@AC:` traceability tags in feature files | `gherkin-living-doc-sync` |
| Write unit tests | Use your project's test framework directly |
