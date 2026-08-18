"""
OrderService — source under test.

Handles placing and cancelling orders. Depends on an InventoryRepository
and a NotificationClient injected at construction time.
"""

from datetime import datetime, timezone


class InsufficientStockError(Exception):
    """Raised when the requested quantity exceeds available stock."""


class OrderService:
    def __init__(self, inventory_repo, notification_client):
        self._inventory = inventory_repo
        self._notifications = notification_client

    def place_order(self, user_id: str, sku: str, quantity: int) -> dict:
        """Place an order for the given SKU and quantity.

        Returns:
            dict with keys: user_id, sku, quantity, status, placed_at

        Raises:
            ValueError: if quantity <= 0 or sku is empty
            InsufficientStockError: if available stock < quantity
        """
        if not sku:
            raise ValueError("sku must not be empty")
        if quantity <= 0:
            raise ValueError("quantity must be positive")

        stock = self._inventory.get_stock(sku)
        if stock < quantity:
            raise InsufficientStockError(
                f"Only {stock} units of {sku} available"
            )

        self._inventory.reserve(sku, quantity)
        order = {
            "user_id": user_id,
            "sku": sku,
            "quantity": quantity,
            "status": "placed",
            "placed_at": datetime.now(timezone.utc).isoformat(),
        }
        self._notifications.send(user_id, f"Order placed for {quantity}x {sku}")
        return order

    def cancel_order(self, order_id: str) -> bool:
        """Cancel an existing order.

        Returns:
            True if cancelled successfully.
            False if the order has already shipped and cannot be cancelled.

        Raises:
            ValueError: if order_id is empty
        """
        if not order_id:
            raise ValueError("order_id must not be empty")

        status = self._inventory.get_order_status(order_id)
        if status == "shipped":
            return False

        self._inventory.release_order(order_id)
        return True
