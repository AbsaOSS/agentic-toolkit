"""
Partial tests for OrderService — happy path only.

These tests cover the successful place_order scenario but are missing:
- Failure paths (ValueError for bad inputs, InsufficientStockError)
- Boundary values (quantity=1, empty sku)
- cancel_order coverage entirely
"""

import pytest
from unittest.mock import MagicMock
from source_order_service import OrderService


@pytest.fixture
def inventory():
    repo = MagicMock()
    repo.get_stock.return_value = 10
    return repo


@pytest.fixture
def notifications():
    return MagicMock()


@pytest.fixture
def service(inventory, notifications):
    return OrderService(inventory_repo=inventory, notification_client=notifications)


def test_place_order_with_valid_inputs_returns_order_dict(service):
    """Happy path: valid user, sku, and quantity returns a well-formed order."""
    result = service.place_order("user-1", "SKU-A", 3)

    assert result["user_id"] == "user-1"
    assert result["sku"] == "SKU-A"
    assert result["quantity"] == 3
    assert result["status"] == "placed"


def test_place_order_reserves_stock(service, inventory):
    """Happy path: placing an order calls reserve on the inventory repo."""
    service.place_order("user-1", "SKU-A", 3)
    inventory.reserve.assert_called_once_with("SKU-A", 3)


def test_place_order_sends_notification(service, notifications):
    """Happy path: placing an order sends a notification to the user."""
    service.place_order("user-1", "SKU-A", 3)
    notifications.send.assert_called_once()
