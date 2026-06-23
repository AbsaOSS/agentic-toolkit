"""Source module for DiscountCalculator — used by eval 7 (write-tests task).

This is the production code under test.  No test file exists yet; the eval asks
the model to write compliant unit tests for this class from scratch.
"""
from __future__ import annotations


class DiscountCalculator:
    """Calculates a discounted price based on the customer's membership tier.

    Recognised tiers and their discounts:
      "gold"   → 20 % off
      "silver" → 15 % off
      "bronze" → 10 % off
      None     →  0 % off (no discount)

    Raises:
        ValueError: if *price* is negative.
        ValueError: if *member_tier* is not one of the recognised values or None.
    """

    DISCOUNTS: dict[str | None, float] = {
        "gold": 0.20,
        "silver": 0.15,
        "bronze": 0.10,
        None: 0.00,
    }

    def calculate(self, price: float, member_tier: str | None) -> float:
        """Return the discounted price rounded to two decimal places.

        Args:
            price: The original price (must be >= 0).
            member_tier: One of "gold", "silver", "bronze", or None.

        Returns:
            The discounted price as a float.
        """
        if price < 0:
            raise ValueError(f"price must be non-negative, got {price}")
        if member_tier not in self.DISCOUNTS:
            raise ValueError(f"unknown tier: {member_tier!r}")
        discount = self.DISCOUNTS[member_tier]
        return round(price * (1 - discount), 2)
