# Source file for test-unit-write eval: parametrized test generation
# This file defines a discount calculator with multiple tiers.
# Tests should use pytest.mark.parametrize to cover all tiers.

class DiscountCalculator:
    def __init__(self, exchange_rate=1.0):
        self.exchange_rate = exchange_rate

    def calculate_discount(self, amount, tier):
        """Calculate discount for given amount and tier.
        
        Args:
            amount: float, the order amount
            tier: str, one of: gold (20%), silver (10%), bronze (5%), standard (0%)
        
        Returns:
            float, the discounted amount
        
        Raises:
            ValueError if amount < 0 or tier not recognised
        """
        if amount < 0:
            raise ValueError("Amount must be non-negative")
        
        rates = {
            "gold": 0.20,
            "silver": 0.10,
            "bronze": 0.05,
            "standard": 0.00,
            None: 0.00
        }
        
        if tier not in rates:
            raise ValueError(f"Unknown tier: {tier}")
        
        discount_rate = rates[tier]
        return amount * (1 - discount_rate) * self.exchange_rate
