"""
ShippingCalculator tests — copy-pasted data setup (factory/fixture candidate).

The make_package() call is duplicated across all tests. The weight/dimensions
override pattern is embedded inside each test body instead of using a factory
or parametrize. Also contains a non-deterministic datetime.now() call.
"""

from datetime import datetime, timezone
from dataclasses import dataclass
from decimal import Decimal


@dataclass
class Package:
    weight_kg: float
    length_cm: float
    width_cm: float
    height_cm: float
    destination: str


def calculate_shipping(pkg: Package, express: bool = False) -> Decimal:
    """Calculate shipping cost for a package."""
    volume = pkg.length_cm * pkg.width_cm * pkg.height_cm / 5000
    chargeable = max(pkg.weight_kg, volume)
    base_rate = Decimal("2.50")
    cost = base_rate * Decimal(str(chargeable))
    if express:
        cost *= Decimal("1.5")
    return round(cost, 2)


# --- copy-pasted setup in every test; should use a factory function ---

def test_standard_shipping_for_light_parcel():
    # copy-pasted Package construction
    pkg = Package(
        weight_kg=1.0,
        length_cm=20.0,
        width_cm=15.0,
        height_cm=10.0,
        destination="ZA",
    )
    result = calculate_shipping(pkg, express=False)
    assert result == Decimal("2.50")


def test_express_shipping_adds_50_percent():
    # copy-pasted Package construction (same fields, same defaults)
    pkg = Package(
        weight_kg=1.0,
        length_cm=20.0,
        width_cm=15.0,
        height_cm=10.0,
        destination="ZA",
    )
    result = calculate_shipping(pkg, express=True)
    assert result == Decimal("3.75")


def test_volumetric_weight_used_when_higher():
    # copy-pasted Package construction with only length changed
    pkg = Package(
        weight_kg=0.1,
        length_cm=50.0,   # only this field is different
        width_cm=15.0,
        height_cm=10.0,
        destination="ZA",
    )
    result = calculate_shipping(pkg, express=False)
    assert result > Decimal("2.50")


def test_heavy_package_uses_actual_weight():
    # copy-pasted Package construction with only weight changed
    pkg = Package(
        weight_kg=10.0,   # only this field is different
        length_cm=20.0,
        width_cm=15.0,
        height_cm=10.0,
        destination="ZA",
    )
    result = calculate_shipping(pkg, express=False)
    assert result == Decimal("25.00")


def test_shipping_audit_log_timestamp():
    """Non-deterministic datetime.now() in test setup."""
    pkg = Package(
        weight_kg=1.0,
        length_cm=20.0,
        width_cm=15.0,
        height_cm=10.0,
        destination="ZA",
    )
    cost = calculate_shipping(pkg)
    # ❌ datetime.now() in test assertion — non-deterministic
    logged_at = datetime.now(timezone.utc).isoformat()
    assert cost > Decimal("0")
    assert logged_at is not None   # always passes, proves nothing
