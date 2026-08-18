"""Unit tests for OrderProcessor.

VIOLATIONS — assertion completeness:
  test_process_order_returns_something : asserts 'is not None' instead of a specific value
  test_process_order_completes         : asserts truthiness only (assert result)
  test_reserve_stock_called            : '.called is not None' is always True — not a real assertion
  (no test)                            : missing failure path for out-of-stock inventory
  (no test)                            : missing failure path for unknown SKU
  (no test)                            : missing boundary test for quantity=0
  (no test)                            : missing boundary test for quantity=1 (lower success boundary)
"""
import pytest
from unittest.mock import MagicMock

from orders.order_processor import OrderProcessor


@pytest.fixture
def processor():
    """OrderProcessor with stubbed inventory and notifier."""
    inv = MagicMock()
    inv.reserve.return_value = True
    notifier = MagicMock()
    return OrderProcessor(inventory=inv, notifier=notifier)


def test_process_order_returns_something(processor):
    """Processing a valid order returns a result."""
    result = processor.process(order_id="o1", quantity=2, sku="SKU-100")
    assert result is not None                         # weak: no specific value asserted


def test_process_order_completes(processor):
    """Processing a valid order completes without error."""
    result = processor.process(order_id="o2", quantity=1, sku="SKU-200")
    assert result                                     # weak: truthy check only


def test_reserve_stock_called(processor):
    """Processing an order triggers inventory reservation."""
    processor.process(order_id="o3", quantity=5, sku="SKU-300")
    assert processor.inventory.reserve.called is not None  # always True — not a real assertion


# Missing: test for out-of-stock — what exception is raised?
# Missing: test for unknown SKU — what exception is raised?
# Missing: test for quantity=0 (boundary — should this raise or return empty order?)
# Missing: test for quantity=1 (lower boundary success case)
