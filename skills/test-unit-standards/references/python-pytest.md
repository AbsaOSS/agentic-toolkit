# Python + pytest — Language Reference

Loaded by `test-unit-standards`, `test-unit-write`, and `test-unit-review` when Python is detected.
Apply these conventions on top of the language-agnostic rules in `test-unit-standards/SKILL.md`.

---

## Test naming

Convention: `test_<unit>_<condition>_<expected_outcome>`

```python
# ✅
def test_apply_discount_with_gold_tier_returns_20_percent_off(): ...
def test_apply_discount_with_negative_price_raises_value_error(): ...
def test_place_order_with_zero_quantity_raises_value_error(): ...
def test_place_order_when_stock_insufficient_raises_insufficient_stock_error(): ...

# ❌ — vague, missing condition or expected outcome
def test_discount(): ...
def test_it_works(): ...
def test_1(): ...
def test_apply_discount_works(): ...
```

---

## Private member convention

Python marks private members with a leading underscore (`_name`) or name-mangling (`__name`).
Tests must not access either.

```python
# ✅ — test through the public interface
def test_validate_with_expired_token_raises_unauthorized(validator):
    with pytest.raises(UnauthorizedError):
        validator.validate(expired_token)

# ❌ — accessing private method directly
def test_decode_extracts_sub_claim(validator):
    result = validator._decode(token)   # private — not allowed
    assert result["sub"] == "user123"

# ❌ — accessing private attribute directly
def test_cache_is_populated(validator):
    validator.validate(valid_token)
    assert "user123" in validator._cache   # private — not allowed
```

---

## Fixtures and conftest.py

- Place shared fixtures in `conftest.py` at the nearest test directory level
- Use `@pytest.fixture` with explicit `scope` (`"function"` is default; `"session"` for expensive shared setup)
- Document every fixture with a docstring stating its purpose and any side effects

```python
# ✅ tests/unit/conftest.py
import pytest
from unittest.mock import MagicMock

@pytest.fixture
def payment_gateway():
    """Stubbed payment gateway. Returns a fixed successful charge response."""
    gateway = MagicMock()
    gateway.charge.return_value = {"id": "ch_123", "status": "succeeded"}
    return gateway

@pytest.fixture
def order_service(payment_gateway):
    """OrderService wired with the stubbed gateway. No real network calls."""
    return OrderService(gateway=payment_gateway)

# ❌ — setup copy-pasted inside every test
def test_charge_returns_id():
    gateway = MagicMock()
    gateway.charge.return_value = {"id": "ch_123", "status": "succeeded"}
    service = OrderService(gateway=gateway)
    ...

def test_charge_raises_on_decline():
    gateway = MagicMock()                                  # duplicated
    gateway.charge.return_value = {"id": "ch_123", ...}   # duplicated
    service = OrderService(gateway=gateway)                # duplicated
    ...
```

---

## Assertion style

Use pytest's native `assert` statement with specific, exact values.

```python
# ✅
assert result == {"id": "order_1", "status": "placed"}
assert result.discount_amount == pytest.approx(20.0)

with pytest.raises(ValueError, match="quantity must be positive"):
    service.place_order("u1", "SKU-1", 0)

mock_notify.assert_called_once_with("u1", "Order placed for 2x SKU-1")

# ❌ — too weak to prove behaviour
assert result is not None
assert result           # truthy check only
assert mock.called is not None   # always True — proves nothing
assert isinstance(result, dict)  # proves type, not value
self.assertEqual(result, ...)    # unittest style in a pytest file — inconsistent
```

---

## Exception testing

```python
# ✅ — specific type and message match
with pytest.raises(InsufficientStockError, match="Only 2 units of SKU-X available"):
    service.place_order("u1", "SKU-X", 10)

# ✅ — capture and inspect the exception value
with pytest.raises(ValidationError) as exc_info:
    service.place_order("u1", "", 1)
assert "sku" in str(exc_info.value).lower()

# ❌ — catches any exception, hides real failures
try:
    service.place_order("u1", "SKU-X", 10)
except Exception:
    pass

# ❌ — no assertion on type or message
with pytest.raises(Exception):
    service.place_order("u1", "SKU-X", 10)
```

---

## Mocking

Use `pytest-mock` (`mocker` fixture) or `unittest.mock.patch`.

**Rule:** patch the name as it is **imported in the module under test**, not where it is defined.

```python
# ✅ — patch where 'requests' is imported inside myapp.services.user_service
def test_fetch_user_returns_parsed_response(mocker):
    mocker.patch(
        "myapp.services.user_service.requests.get",
        return_value=MagicMock(status_code=200, json=lambda: {"id": "u1"}),
    )
    result = UserService().fetch("u1")
    assert result == {"id": "u1"}

# ❌ — patching the source module has no effect on the module under test
def test_fetch_user_returns_parsed_response(mocker):
    mocker.patch("requests.get", return_value=...)
```

Prefer fixture-based patches over inline `with patch(...)` blocks to keep test bodies clean.

```python
# ✅ — fixture-based patch
@pytest.fixture
def mock_requests_get(mocker):
    """Patches requests.get in user_service; returns the mock for assertion."""
    return mocker.patch("myapp.services.user_service.requests.get")

def test_fetch_user_calls_correct_url(mock_requests_get):
    mock_requests_get.return_value = MagicMock(json=lambda: {"id": "u1"})
    UserService().fetch("u1")
    mock_requests_get.assert_called_once_with("https://api.example.com/users/u1")
```

---

## Parametrize

Use `@pytest.mark.parametrize` for multiple input variations of the same logical case.

```python
# ✅ — one parametrized test instead of four separate functions
@pytest.mark.parametrize("price,tier,expected", [
    (100.0, "gold",   80.0),   # 20% off
    (100.0, "silver", 90.0),   # 10% off
    (100.0, None,    100.0),   # no discount
    (0.0,   "gold",   0.0),    # boundary: zero price
])
def test_apply_discount_returns_correct_price(price, tier, expected):
    assert apply_discount(price, tier) == pytest.approx(expected)

# ❌ — four separate functions testing identical logic
def test_apply_discount_gold():   assert apply_discount(100.0, "gold")   == 80.0
def test_apply_discount_silver(): assert apply_discount(100.0, "silver") == 90.0
def test_apply_discount_no_tier(): assert apply_discount(100.0, None)    == 100.0
def test_apply_discount_zero():   assert apply_discount(0.0,   "gold")   == 0.0
```

---

## Test file placement

```
project/
├── src/
│   └── myapp/
│       └── services/
│           └── payment_service.py
└── tests/
    └── unit/
        ├── conftest.py                        ← shared fixtures for all unit tests
        └── services/
            └── test_payment_service.py        ← mirrors src/ path, prefixed with test_
```

One test file per source module. Prefix test files with `test_`. Collect shared fixtures in `conftest.py`.
