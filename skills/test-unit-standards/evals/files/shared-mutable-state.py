"""Unit tests for CartService.

VIOLATIONS — isolation (shared mutable state between tests):
  TestCartServiceSequenced._processed is a class-level list mutated across tests.
  test_refund_removes_order depends on test_checkout_records_order running first,
  making the suite order-dependent and breaking independent-execution guarantees.
"""
import pytest
from unittest.mock import MagicMock

from services.cart_service import CartService


class TestCartServiceSequenced:
    _processed: list = []  # class-level mutable state — shared across all test instances

    @pytest.fixture(autouse=True)
    def setup(self):
        """Wire CartService to a payment stub."""
        self.payment = MagicMock()
        self.service = CartService(payment=self.payment)

    def test_checkout_records_order(self):
        """Checkout adds an entry to the shared _processed list."""
        self.service.checkout(cart_id="c1", total=150.0)
        self.__class__._processed.append("c1")   # mutates shared class-level state
        assert "c1" in self.__class__._processed

    def test_refund_removes_order(self):
        """Refund removes an entry — implicitly requires test_checkout_records_order to have run first."""
        self.__class__._processed.remove("c1")   # reads state written by a previous test
        assert "c1" not in self.__class__._processed

    def test_checkout_delegates_charge_to_payment_gateway(self):
        """Checkout total is delegated to the payment gateway."""
        self.service.checkout(cart_id="c2", total=200.0)
        self.payment.charge.assert_called_once_with(200.0)
