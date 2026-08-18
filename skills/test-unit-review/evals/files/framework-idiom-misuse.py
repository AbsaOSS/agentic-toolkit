# Framework idiom misuse: pytest.raises with wrong parameters
# Problem: match parameter is used with a literal string, not a regex

import pytest
from decimal import Decimal

class PriceValidator:
    def validate(self, price, currency):
        """Validate price and currency. Raise ValueError if invalid."""
        if price < 0:
            raise ValueError("Price must be non-negative")
        if currency not in ["USD", "EUR", "GBP"]:
            raise ValueError(f"Unknown currency: {currency}")
        return True

class TestPriceValidator:
    def test_negative_price_raises_error(self):
        """When validate is called with negative price, ValueError is raised."""
        validator = PriceValidator()
        # VIOLATION: match is a regex pattern, not a literal string.
        # This will fail because match expects a regex, not a literal substring.
        # Correct: use match=r'Price must be non-negative' (regex)
        # or use match='Price must be' (substring of a regex)
        with pytest.raises(ValueError, match="Price must be non-negative"):
            validator.validate(-10, "USD")

    def test_unknown_currency_raises_error(self):
        """When validate is called with unknown currency, ValueError is raised."""
        validator = PriceValidator()
        # This one is correct: match is a substring pattern
        with pytest.raises(ValueError, match="Unknown currency"):
            validator.validate(100, "XYZ")

    def test_valid_price_and_currency(self):
        """When validate is called with valid inputs, return True."""
        validator = PriceValidator()
        result = validator.validate(Decimal('99.99'), "EUR")
        assert result is True
