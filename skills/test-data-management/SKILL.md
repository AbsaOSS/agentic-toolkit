---
name: test-data-management
description: >
  Test data setup and management. Activate when test setup is duplicated, inputs need
  parametrisation, factories/builders are needed, timestamps are non-deterministic, or
  production data rules apply. Triggers on: "test data factory", "fixture builder",
  "parametrize this test", "data-driven tests", "test setup is duplicated",
  "inject fixed timestamp", "can I use production data",
  "clean up after integration tests". Does NOT trigger for: test double selection,
  writing or reviewing tests, debug errors.
license: Proprietary
compatibility: GitHub Copilot
---

# Test Data Management

## Prefer data-driven and parametrised tests

When a behaviour must be tested with multiple input combinations, prefer parametrised tests over
duplicated test methods. One parametrised test with a data table is clearer, easier to extend,
and reduces duplication.

| Language | Tool | Pattern |
|----------|------|---------|
| Python | `pytest.mark.parametrize` | `@pytest.mark.parametrize("input,expected", [...])` |
| Scala | ScalaTest `TableDrivenPropertyChecks` | `forAll(table) { (input, expected) => ... }` |
| .NET | xUnit `[Theory]` + `[InlineData]` / `[MemberData]` | `[Theory] [InlineData(1, 2)]` |
| TypeScript | Jest `test.each` | `test.each([[input, expected]])` |
| Java | JUnit 5 `@ParameterizedTest` | `@ParameterizedTest @MethodSource` |

**Use** parametrised tests when: the same behaviour is tested with ≥ 3 input combinations, or when
combinations form a clear equivalence class table.

**Do not use** parametrised tests when: each case requires fundamentally different setup or
assertions — use separate named tests instead.

## Use factory and builder patterns

- Create factory functions or builder classes that produce valid default objects
- Override only the fields relevant to the specific test case
- Shared hardcoded data causes **cross-test coupling**: a change to a shared dict or object breaks every test that references it — tests should never share mutable data structures
- Place factories in the nearest shared location:
  - Python: `conftest.py` factory fixture or `tests/factories.py`
  - Scala: `TestFactories.scala` object
  - .NET: `TestDataBuilder.cs`
  - TypeScript: `test-factories.ts`
- Document the factory's defaults and what each parameter controls

```python
# ✅ — factory with keyword overrides
def make_order(*, order_id="ORD-1", user_id="u1", sku="SKU-1", quantity=1, status="pending"):
    return Order(order_id=order_id, user_id=user_id, sku=sku, quantity=quantity, status=status)

# test uses only the fields that matter
def test_cancel_order_when_shipped_returns_false():
    order = make_order(status="shipped")
    assert service.cancel(order.order_id) is False
```

### Composable nested factories

Create a factory per level and compose them:

```python
# ✅ — each factory owns one level; override at any depth
def make_address(*, street="1 Test St", city="Cape Town", country="ZA"):
    return Address(street=street, city=city, country=country)

def make_customer(*, customer_id="CUST-1", email="test@example.com", address=None):
    return Customer(customer_id=customer_id, email=email,
                    address=address or make_address())

def make_order(*, order_id="ORD-1", user_id="u1", sku="SKU-1", quantity=1,
               status="pending", customer=None):
    return Order(order_id=order_id, user_id=user_id, sku=sku, quantity=quantity,
                 status=status, customer=customer or make_customer())

# Override at any level without affecting other tests
order = make_order(customer=make_customer(address=make_address(country="UK")))
```

Do not hardcode deeply-nested dict literals — they are impossible to override and cannot be reused.

## Never use production data

- Must never use real production data in tests — not even anonymised exports
- Generate synthetic data that represents the shape and constraints of production data
- If a realistic dataset is needed, write a generator script and commit the generator, not the data

## Keep data deterministic

- No random values without a fixed seed
- Timestamps must be fixed or injected — never call `datetime.now()`, `new Date()`, or
  `LocalDateTime.now()` directly in test setup
- Inject a clock or timestamp provider that can be fixed per test

```python
# ✅ — fixed timestamp injected
FIXED_NOW = datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc)

def test_order_placed_at_is_set(mocker):
    mocker.patch("myapp.services.order_service.datetime")
           .now.return_value = FIXED_NOW
    order = service.place_order("u1", "SKU-1", 1)
    assert order["placed_at"] == FIXED_NOW.isoformat()

# ❌ — non-deterministic; test may pass or fail depending on timing
def test_order_placed_at_is_set():
    order = service.place_order("u1", "SKU-1", 1)
    assert order["placed_at"] is not None   # always passes; proves nothing
```

## Keep data minimal

- Use the smallest dataset that exercises the behaviour under test
- Avoid large data files checked into the repo — generate programmatically
- Prefer inline data for simple cases; external files only for complex domain fixtures with
  many fields (e.g. realistic JSON payloads, XML documents)

## Clean up after integration tests

- Integration tests must clean up created data after each test run
- Strategies: transactions rolled back after each test, temp tables, test containers with
  per-test teardown, or database truncation in `afterEach`
- Use a unique run-scoped prefix or ID for all created records so cleanup is scoped and safe
- Unit tests do not need cleanup — they use no real resources

## Out of scope

- Choosing test doubles (mock, stub, spy, fake) — handle in your project's mocking guide
- Writing test logic and assertions — handled separately
- Reviewing tests for standards compliance — handled separately
