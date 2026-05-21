"""
NotificationClient — changed method signature.

Used by: living-doc-impact-analysis file-based eval

The send() method previously accepted (user_id, message).
It now accepts (user_id, message, channel) where channel is
one of: 'email', 'sms', 'push'. The channel parameter is required
(not optional) to force explicit intent at every call site.

This file shows:
- The OLD signature (commented out)
- The NEW signature
- An example caller (OrderService) that uses the old signature
"""


class NotificationClient:
    # OLD signature — no longer valid:
    # def send(self, user_id: str, message: str) -> None:

    def send(self, user_id: str, message: str, channel: str) -> None:
        """Send a notification to the user via the specified channel.

        Args:
            user_id: The unique identifier of the recipient.
            message: The notification message text.
            channel: Delivery channel — one of: 'email', 'sms', 'push'.

        Raises:
            ValueError: If channel is not one of the allowed values.
        """
        allowed = {"email", "sms", "push"}
        if channel not in allowed:
            raise ValueError(f"channel must be one of {allowed}, got '{channel}'")
        # ... actual delivery logic omitted


class OrderService:
    """Uses the OLD NotificationClient.send() signature — needs updating."""

    def __init__(self, notification_client: NotificationClient):
        self._notifications = notification_client

    def place_order(self, user_id: str, sku: str, quantity: int) -> dict:
        order = {"user_id": user_id, "sku": sku, "quantity": quantity, "status": "placed"}
        # BUG: old signature — missing 'channel' argument
        self._notifications.send(user_id, f"Order placed for {quantity}x {sku}")
        return order

    def cancel_order(self, order_id: str, user_id: str) -> bool:
        # BUG: old signature — missing 'channel' argument
        self._notifications.send(user_id, f"Order {order_id} has been cancelled")
        return True
