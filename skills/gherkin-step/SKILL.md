---
name: gherkin-step
description: >
  Implementing Gherkin step definitions that are clean, reusable, and maintainable. Activate when
  writing or reviewing step definition code, binding Gherkin text to automation, managing shared
  state between steps, configuring parameter types, parsing DataTable or DocString arguments, or
  setting up Before/After hooks. Covers Python behave, Cucumber for Java and TypeScript, and
  Cucumber-Scala idioms.
  Triggers on: "step definitions", "implement Gherkin steps", "Cucumber step", "behave step",
  "parameter type", "DataTable", "DocString", "Before hook", "After hook", "World object",
  "step context", "step state sharing", "how to share state between steps",
  "register step definition", "hook setup".
  Does NOT trigger for: writing Gherkin scenarios (use gherkin-scenario), writing unit tests
  (use test-unit-write). Pairs with gherkin-scenario.
---

# Gherkin Step Definition Standards

> **Glossary:** Feature, PageObject, Functionality — see [living-doc-glossary](../references/living-doc-glossary.md) ([remote](https://github.com/AbsaOSS/agentic-toolkit/blob/master/skills/references/living-doc-glossary.md)).

## Respect the boundary with Gherkin text

If the user asks to write or review a **Gherkin scenario / feature file**, do not draft the
scenario here. Explain that this skill covers **step definition code** only, then route the user to
`gherkin-scenario` for the Gherkin text itself.

---

## Context initialization — how PageObjects reach steps

Step definitions receive a fresh `context` object each scenario. PageObjects must be attached to
`context` in a `before_scenario` hook (or a preceding `Given` step), not inside the step itself.

```python
# ✅ — Before hook initialises the PageObject once per scenario
@before_scenario
def setup_pages(context):
    context.checkout_page = CheckoutPage(context.browser.new_page())
```

The `When` step then delegates without creating or managing the PageObject:

```python
@when('the customer confirms the order')
def step_confirm_order(context):
    context.checkout_page.confirm_order()   # relies on before_scenario having run
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

---

## Use typed parameters

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
