"""
TaxCalculator tests — separate test function per variation (parametrize candidate).

Each of the first six test functions tests the same apply_tax() behaviour with a
different rate. They should be collapsed into a single @pytest.mark.parametrize test.
The last two tests (boundary cases) test fundamentally different failure logic and
are fine as standalone named tests.
"""

from decimal import Decimal


def apply_tax(amount: Decimal, rate_pct: float) -> Decimal:
    """Apply a tax rate to an amount. rate_pct is a percentage (e.g. 15 for 15%)."""
    if amount < 0:
        raise ValueError("amount must be non-negative")
    if rate_pct < 0 or rate_pct > 100:
        raise ValueError("rate_pct must be between 0 and 100")
    return round(amount * Decimal(1 + rate_pct / 100), 2)


# --- same logic, six separate functions — should be parametrized ---

def test_apply_tax_with_0_percent_rate():
    assert apply_tax(Decimal("100.00"), 0) == Decimal("100.00")


def test_apply_tax_with_5_percent_rate():
    assert apply_tax(Decimal("100.00"), 5) == Decimal("105.00")


def test_apply_tax_with_10_percent_rate():
    assert apply_tax(Decimal("100.00"), 10) == Decimal("110.00")


def test_apply_tax_with_15_percent_rate():
    assert apply_tax(Decimal("100.00"), 15) == Decimal("115.00")


def test_apply_tax_with_20_percent_rate():
    assert apply_tax(Decimal("100.00"), 20) == Decimal("120.00")


def test_apply_tax_with_100_percent_rate():
    assert apply_tax(Decimal("100.00"), 100) == Decimal("200.00")


# --- different failure logic — fine as standalone named tests ---

def test_apply_tax_with_negative_amount_raises_value_error():
    """Failure path: negative amount raises ValueError."""
    import pytest
    with pytest.raises(ValueError, match="non-negative"):
        apply_tax(Decimal("-1.00"), 10)


def test_apply_tax_with_rate_above_100_raises_value_error():
    """Failure path: rate > 100 raises ValueError."""
    import pytest
    with pytest.raises(ValueError, match="rate_pct"):
        apply_tax(Decimal("100.00"), 101)
