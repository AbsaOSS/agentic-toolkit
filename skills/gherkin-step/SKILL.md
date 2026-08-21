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
---

# Gherkin Step Definition Standards

> **Glossary:** Feature, PageObject, Functionality — see [living-doc-glossary](../shared/references/living-doc-glossary.md).

> **Framework scope:** Covers **Python behave**, **Cucumber TypeScript**, **Cucumber Java**, and **Cucumber-Scala**. The toolkit's PageObject ecosystem is **Playwright + TypeScript**; Python or Java projects adapt the examples. The core rules — thin steps, no selectors in steps, shared state via context/World — apply everywhere.

## Respect the boundary with Gherkin text

If the user asks to write or review a **Gherkin scenario / feature file**, do not draft it here. This skill covers **step definition code** only; route Gherkin text requests to `living-doc-scenario-creator`.

---

## Context initialization — how PageObjects reach steps

> **Prerequisite:** PageObjects must exist before step definitions can reference them. If they do not, use `living-doc-pageobject-scan` first.

**Python behave:** each scenario gets a fresh `context`, so state must not leak between scenarios. Attach PageObjects in `before_scenario`.

```python
# ✅ init per scenario
@before_scenario
def setup_pages(context):
    context.checkout_page = CheckoutPage(context.browser.new_page())
```

**Cucumber TypeScript (Playwright):** use a typed `World` class and show `setWorldConstructor(...)` explicitly before the hooks.

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
  constructor(options: IWorldOptions & { browser: Browser }) {
    super(options);
    this.browser = options.browser;
  }
}
setWorldConstructor(AppWorldImpl);
```

Always show the registration call explicitly in setup answers: `setWorldConstructor(AppWorldImpl);`.

Do not launch the browser inside the World constructor. Inject it into the World/test context; let `Before` create only the scenario's fresh page or browser context.

```typescript
// hooks.ts
Before(async function (this: AppWorld) {
  this.page   = await this.browser.newPage();
  this.checkoutPage = new CheckoutPage(this.page);
});

After(async function (this: AppWorld) {
  await this.page?.close();
});
```

**Step definition file naming:**
- One file per domain area: `checkout.steps.ts` / `checkout_steps.py`
- Place under `playwright/steps/` (TS) or `features/steps/` (Python)
- Never name a file `steps.ts` or `steps.py` — the name must identify the domain

**Given precondition state — OGP-01:** A `Given` that uses `.first()` (or any positional selector) without asserting the required domain state creates false positives. If the scenario distinguishes owned from non-owned data, use fixture IDs (`ownedDomainId`, `nonOwnedDomainId`) instead of picking the first match.

```typescript
// ✅ fixture ID guarantees ownership state
Given('I am on the Domain Detail page for a domain I own', async ({ page, env }) => {
  await page.goto(`/auth/domain/${env.ownedDomainId}`);
});

// ❌ both variants pick the same arbitrary domain
Given('I am on the Domain Detail page for a domain I own', async ({ page }) => {
  await page.goto('/auth/all-domains');
  await page.getByTestId('domain-name-link').first().click();
});
```

## Step type taxonomy

Classify every step as one of four types. Follow the Project Profile / existing step files; the conventions below match the reference (AUL) project.

| Type | Keyword | Purpose | Convention |
|---|---|---|---|
| **Navigation Given** | `Given` | Move to a URL via real `page.goto()` (directly or a PageObject `goto()`). One navigation per step; **do not** add a `Then` just to assert it loaded. | `I am on the …` / `the user is on the …` |
| **Action When** | `When` | One atomic UI interaction (click, fill, select, toggle). Neutral text; expected values arrive as `{string}`/`{int}` params, never hardcoded. | `I click the …` / `the user fills in the …` |
| **Compound Given (accelerator)** | `Given` | A setup shortcut that chains several actions (e.g. log in + navigate) to skip flow not under test. Use **only** in `Background` or as the first step of a scenario — never mid-scenario. No assertions. | lives in `*.setup.steps.ts`; JSDoc lists the atomic steps it replaces |
| **Assertion Then** | `Then` | Verify a UI element or application state. Assertions only. | `the … should be …` / `the user should see …` |

Keep page-action steps (Navigation Given, Action When, Assertion Then) in `<area>.steps.ts`; keep compound accelerators in `<area>.setup.steps.ts`. Each accelerator JSDoc must list the atomic steps it replaces. If one appears mid-scenario, move it to `Background` / the first `Given`, or replace it with atomic steps.

## Function naming convention

Name step functions after the business action, not the full step text:
- `step_confirm_order` ✅ — concise, action-based
- `step_customer_confirms_the_order` ❌ — verbatim transcription of the step
The verbose full-phrase form is an anti-pattern: it duplicates Gherkin text, makes step files harder to scan, and truncates poorly in test output and stack traces.

## Keep step definitions thin

Step definitions are bindings: they translate Gherkin text into PageObject, domain-object, or service-client calls. Business logic must not live in them.

**Keyword rules:**
- `Given` steps must not contain assertions — they set up preconditions only
- `When` steps must not contain assertions — they perform actions only
- Assertions belong exclusively in `Then` steps
- A step body consisting only of comments is a no-op and is not permitted as a final implementation — NOP-01. If the system pre-establishes state externally, the step must assert that state is present rather than silently pass.

```typescript
// ✅ pre-populated state is asserted
When('I select a domain', async ({ page }) => {
  await expect(page.getByTestId('domain-selector')).not.toBeEmpty();
});

// ❌ comment-only body
When('I select a domain', async ({ page }) => {
  // no additional action
});
```

```python
# ✅ thin; delegates to PageObject
@when('the customer confirms the order')
def step_confirm_order(context):
    context.checkout_page.confirm_order()

# ❌ business logic in the step
@when('the customer confirms the order')
def step_confirm_order(context):
    context.cart.total *= (1 - context.discount / 100)
    context.order_status = "placed"
```

## Encapsulate selectors in PageObjects

Step definitions for domain-level scenarios must not contain CSS selectors, element IDs, or XPath.
Encapsulate all selector logic in PageObjects (selector preference: `getByTestId()` — resolves to the Project Profile `test_id_attribute`, default `data-cy` — > `aria-label`/role > CSS class).

```typescript
// ✅ PageObject hides selectors
When("the customer submits the order", async function (this: OrderWorld) {
  await this.checkoutPage.submitOrder(this.orderId);
});

// ❌ selector leaks into the step
When("the customer submits the order", async function (this: OrderWorld) {
  await this.page.click('[data-testid="submit-order-btn"]');
});
```

**Pending data-cy rule — SS-01:** Do not write CSS-class-OR-data-cy fallback combos (e.g. `'.modal, [data-cy="x"]'`) in step files or PageObjects. They either always pass (the CSS class matches when the data-cy does not exist) or always fail (neither exists), masking the gap. If the confirmed `data-cy` attribute does not yet exist in the template:
1. Use the most stable interim selector available and mark it `// @pending data-cy: <candidate-name>`.
2. Raise it as a gap in WORK_LOG.md §4 so it is tracked for instrumentation via `data-cy-instrument`.

```typescript
// ✅ interim selector clearly flagged
await expect(page.locator('[role="dialog"]')).toBeVisible(); // @pending data-cy: dialog-access-request

// ❌ fallback combo masks the real selector
await expect(page.locator('[role="dialog"], .access-request-form')).toBeVisible();
```

For Action `When` examples, always delegate to a PageObject method (for example
`await this.checkoutPage.clickConfirmOrder()`) rather than clicking a selector directly in the step.

## Share state using the context / World object

Never use global or module-level variables to share step state — they contaminate later scenarios. Use the framework-provided `context` / `World`, fresh per scenario and safe for cross-step or cross-file sharing within that scenario only. Say this explicitly in state-sharing answers.

| Framework | State object | Pattern |
|-----------|-------------|---------|
| behave (Python) | `context` | Attach attributes: `context.order = ...` |
| Cucumber (TypeScript) | `World` class | Extend `World`; access via `this` |

```python
# ✅ behave: context carries state across steps
@given('a customer with a "{tier}" membership')
def step_given_customer(context, tier):
    context.customer = Customer(tier=tier)

@then("the discount is {rate:d}%")
def step_assert_discount(context, rate):
    assert context.customer.discount_rate() == rate
```

**Hardcoded assertion rule — HTA-01:** `Then` assertions must not contain string literals set in a preceding `When` step (magic constants). Pass the value through the World context or as a `{string}` Cucumber parameter, or assert a structural property instead.

```typescript
// ✅ domain name flows through World context
When('I import a domain named {string}', async function (this: AppWorld, name: string) {
  this.importedDomainName = name;
  await this.importDomainPage.importDomain(name);
});
Then('the imported domain is visible in the domain list', async function (this: AppWorld) {
  await expect(this.page.getByTestId('domain-name-link').getByText(this.importedDomainName)).toBeVisible();
});

// ❌ hardcoded constant couples the assertion to the When step
Then('the imported domain is visible in the domain list', async ({ page }) => {
  await expect(page.getByTestId('domain-name-link').getByText('E2E Import Test')).toBeVisible();
});
```

## Use typed parameters

**PTM-01 — `{string}` over `{word}` for UI labels:** Use `{string}` (quoted) for any parameter that could contain spaces. `{word}` matches one token only, fails on multi-word values, and mixed `{word}`/`{string}` variants in one file cause Cucumber ambiguity errors. Remove all `{word}` variants and consolidate on `{string}`.

```typescript
// ✅ {string} matches multi-word labels
When('I click the {string} tab', async ({ domainDetailPage }, tab: string) => {
  await domainDetailPage.gotoTab(tab);
});

// ❌ {word} fails for multi-word labels
When('I click the {word} tab', async ({ domainDetailPage }, tab: string) => {
  await domainDetailPage.gotoTab(tab);
});
```

```python
# ✅ :d casts to int automatically
@when("the customer purchases {quantity:d} units")
def step_purchase(context, quantity: int):
    context.cart.add_item(context.sku, quantity)
```

## Parse DataTable and DocString arguments

```python
# ✅ DataTable as list of dicts
@when("the customer adds the following items")
def step_add_items(context):
    for row in context.table:
        context.cart.add_item(row["sku"], int(row["quantity"]))

# ✅ DocString as raw text
@when("the system receives the following payload")
def step_receive_payload(context):
    context.payload = json.loads(context.text)
```

## Configure hooks correctly

| Hook | Use for | Must not use for |
|------|---------|-----------------|
| `before_scenario` / `Before` | Set up context state, seed data | Asserting behaviour |
| `after_scenario` / `After` | Cleanup: rollback DB, close browser | Seeding data |
| `before_all` / `BeforeAll` | Expensive one-time setup (start containers) | Per-test state |
| `after_all` / `AfterAll` | Stop containers, close connections | Per-test cleanup |

`before_scenario` runs before **every** scenario by default, so add a tag check when setup applies only to a subset. State this explicitly: `if "database" in context.tags` gates the expensive work; it does not stop the hook from firing. Tag hooks to scope setup and pair them with matching cleanup:

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

## Wizard navigation rules

Apply these rules to multi-step wizards. They detect "cheat steps" — steps that appear to navigate the wizard but exercise no real behaviour.

### CS-01 — Assert arrival at each wizard step

Every wizard navigation step must verify arrival at the next step with a step-specific assertion before the step completes. Blind `continueButton.click()` chains are forbidden: if Continue is disabled, the click silently does nothing and the test can false-pass.

```typescript
// ✅ arrival at the Owner step is verified
When('I complete the About step', async ({ createDomainAboutPage, createDomainOwnerPage }) => {
  await createDomainAboutPage.fillDomainName('E2E Test Domain');
  await createDomainAboutPage.fillCostCenter('1234');
  await createDomainAboutPage.continueButton.click();
  await expect(createDomainOwnerPage.ownersTable).toBeVisible();
});

// ❌ two blind clicks; no arrival assertion
Given('I am on the Target dataset step', async ({ createDomainPage }) => {
  await createDomainPage.continueButton.click();
  await createDomainPage.continueButton.click();
});
```

### CS-02 — Do not use `toHaveURL()` to detect wizard step progress in a scrolling stepper

In a single-URL scrolling stepper, the URL does not change between steps. `toHaveURL(/step-name/)` therefore gives false confidence; assert the step-specific landmark element instead.

```typescript
// ✅ asserts the Owner-step landmark
await expect(createDomainOwnerPage.ownersTable).toBeVisible();

// ❌ URL never changes; assertion always passes
await expect(page).toHaveURL(/owner/i);
```

Once `data-cy` attributes are added to wizard step headers, prefer:
```typescript
await expect(page.getByTestId('step-owner')).toBeVisible();
```

### CS-03 — Do not use `page.goBack()` inside an SPA wizard

`page.goBack()` navigates browser history, not wizard state. In an SPA wizard it usually returns to the *previous page* (for example All Domains), not the previous step. Use the wizard's Back button or the stepper header instead.

```typescript
// ✅ uses the wizard's own back navigation
await createDomainWizardPage.backButton.click();
await expect(createDomainAboutPage.domainNameInput).not.toBeEmpty();

// ❌ navigates away from the wizard
await page.goBack();
await expect(createDomainPage.domainNameInput).not.toBeEmpty();
```

## Out-of-scope routing

| Request | Correct skill |
|---|---|
| Write or review Gherkin scenarios / feature files | `living-doc-scenario-creator` |
| Generate or update PageObject classes | `living-doc-pageobject-scan` |
| Sync `@AC:` traceability tags in feature files | `gherkin-living-doc-sync` |
| Write unit tests | Use your project's test framework directly |
