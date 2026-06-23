"""Unit tests for DiscountCalculator.

VIOLATIONS — naming conventions and boundary/failure-path coverage:
  test_1                  : no descriptive name at all
  test_discount_works     : vague name — no condition or expected outcome stated
  test_it_returns_price   : missing the 'expected' segment
  test_big_number         : not in test_<what>_<condition>_<expected> format
  (no test)               : missing boundary test for price=0.0
  (no test)               : missing failure test for negative price
  (no test)               : missing failure test for unknown member_tier string
  (no test)               : missing floating-point boundary (e.g. price=0.01)
"""
import pytest

from services.discount_calculator import DiscountCalculator


def test_1():
    """No descriptive name — scenario and expected outcome are unclear."""
    calc = DiscountCalculator()
    result = calc.calculate(price=100.0, member_tier="gold")
    assert result == 80.0


def test_discount_works():
    """Vague name: does not state the condition being tested or the expected result."""
    calc = DiscountCalculator()
    result = calc.calculate(price=200.0, member_tier="silver")
    assert result == 170.0


def test_it_returns_price():
    """Name identifies the subject but is missing the expected-outcome segment."""
    calc = DiscountCalculator()
    result = calc.calculate(price=50.0, member_tier=None)
    assert result == 50.0


def test_big_number():
    """Name is not in test_<what>_<condition>_<expected> format."""
    calc = DiscountCalculator()
    result = calc.calculate(price=1_000_000.0, member_tier="gold")
    assert result == 800_000.0


# Missing: test_calculate_price_zero_no_tier_returns_zero
# Missing: test_calculate_negative_price_raises_value_error
# Missing: test_calculate_unknown_tier_raises_value_error
# Missing: test_calculate_minimum_positive_price_applies_correct_discount
