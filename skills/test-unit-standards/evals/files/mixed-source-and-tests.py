"""Mixed request fixture: source code + tests side by side.

Used by eval 13 (scope-note adherence): the user asks for a source-code
refactor, not a test review.  The skill must complete the refactor without
citing or enforcing unit test standards on the test file.
"""

# ── source under refactor ─────────────────────────────────────────────────────


class ShippingCalculator:
    """Calculates shipping cost based on weight and destination zone."""

    ZONE_RATES = {"domestic": 15.0, "regional": 35.0, "international": 80.0}

    def calculate(self, weight_kg: float, zone: str) -> float:
        if weight_kg <= 0:
            raise ValueError("weight_kg must be positive")
        if zone not in self.ZONE_RATES:
            raise ValueError(f"unknown zone: {zone!r}")
        if weight_kg <= 1:
            base = self.ZONE_RATES[zone]
        elif weight_kg <= 5:
            base = self.ZONE_RATES[zone] * 1.5
        elif weight_kg <= 20:
            base = self.ZONE_RATES[zone] * 2.5
        else:
            base = self.ZONE_RATES[zone] * 4.0
        return round(base, 2)


# ── existing tests (compliant — should not be touched or flagged) ─────────────

import pytest


@pytest.fixture
def calc():
    """ShippingCalculator instance for all tests."""
    return ShippingCalculator()


def test_calculate_domestic_under_1kg_returns_base_rate(calc):
    """Shipments up to 1 kg domestic use the flat base rate."""
    assert calc.calculate(weight_kg=0.5, zone="domestic") == 15.0


def test_calculate_international_over_20kg_applies_max_multiplier(calc):
    """Shipments over 20 kg international use the 4× multiplier."""
    assert calc.calculate(weight_kg=25.0, zone="international") == 320.0


def test_calculate_zero_weight_raises_value_error(calc):
    """Zero weight is rejected with a descriptive ValueError."""
    with pytest.raises(ValueError, match="weight_kg must be positive"):
        calc.calculate(weight_kg=0, zone="domestic")


def test_calculate_unknown_zone_raises_value_error(calc):
    """An unrecognised zone string raises ValueError."""
    with pytest.raises(ValueError, match="unknown zone"):
        calc.calculate(weight_kg=1.0, zone="orbit")
