"""
PriceCalculator — source under test (JavaScript/TypeScript equivalent in Python for eval purposes).

Calculates the final price for a cart item applying member tier discounts and
promotional codes fetched from an external promotions API.
"""

import os
import requests


TIER_DISCOUNTS = {
    "gold": 0.20,
    "silver": 0.10,
    "bronze": 0.05,
}


class PromotionError(Exception):
    """Raised when the promotions API returns an unexpected response."""


class PriceCalculator:
    def __init__(self, promotions_client=None):
        self._promotions = promotions_client or requests

    def calculate(self, base_price: float, tier: str | None, promo_code: str | None) -> float:
        """Calculate the final price after tier discount and optional promo code.

        Args:
            base_price: Original item price. Must be >= 0.
            tier: Member tier ('gold', 'silver', 'bronze') or None for no tier discount.
            promo_code: Optional promotional code to look up additional % off.

        Returns:
            Final price (float, >= 0).

        Raises:
            ValueError: if base_price < 0 or tier is not a recognised value.
            PromotionError: if the promotions API returns a non-200 response.
        """
        if base_price < 0:
            raise ValueError(f"base_price must be non-negative, got {base_price}")
        if tier is not None and tier not in TIER_DISCOUNTS:
            raise ValueError(f"unrecognised tier: {tier!r}")

        price = base_price
        if tier:
            price *= 1.0 - TIER_DISCOUNTS[tier]

        if promo_code:
            api_url = os.environ.get("PROMOTIONS_API_URL", "https://promos.example.com")
            response = self._promotions.get(f"{api_url}/codes/{promo_code}")
            if response.status_code != 200:
                raise PromotionError(
                    f"promotions API returned {response.status_code} for code {promo_code!r}"
                )
            extra_discount = response.json().get("discount_pct", 0) / 100
            price *= 1.0 - extra_discount

        return round(price, 2)
