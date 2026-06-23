"""Unit tests for NotificationService.

VIOLATIONS — all rule categories present (used for multi-violation audit eval):

  ISOLATION   setup_method opens a real Redis connection instead of using a stub
  SCOPE       test_build_message_template calls private _build_message method
              test_retry_count_after_failure reads private _retry_count attribute
  NAMING      test_send / test_error / test_ok do not follow test_<what>_<condition>_<expected>
  ASSERTIONS  test_send asserts 'is not None' (weak)
              test_ok asserts truthiness only
              test_error has no assertion at all
  FIXTURES    redis_mock + email_client construction is copy-pasted in standalone tests
  BOUNDARIES  no test for empty recipients list
              no test for None subject
              no test for zero-length message body
"""
import redis
import pytest
from unittest.mock import MagicMock

from notifications.notification_service import NotificationService


class TestNotificationService:
    def setup_method(self):
        # real Redis connection — not mocked; violates isolation
        self.redis = redis.Redis(host="localhost", port=6379)
        self.email_client = MagicMock()
        self.service = NotificationService(
            redis=self.redis, email_client=self.email_client
        )

    def test_send(self):
        """Vague name — no condition or expected outcome."""
        result = self.service.send(
            recipients=["a@example.com"], subject="Hello", body="World"
        )
        assert result is not None                   # weak: specific return value not asserted

    def test_error(self):
        """Name gives no information about the scenario being tested."""
        self.email_client.send.side_effect = ConnectionError("SMTP down")
        # missing: no assertion — test body does not verify the outcome

    def test_ok(self):
        """Overly generic pass/fail label."""
        result = self.service.send(
            recipients=["b@example.com"], subject="Hi", body="There"
        )
        assert result                               # weak: truthy check only

    def test_build_message_template(self):
        """Accesses private _build_message method to verify template rendering."""
        msg = self.service._build_message(subject="Hi", body="Body")  # private method — violates scope
        assert "Hi" in msg

    def test_retry_count_after_failure(self):
        """Reads private _retry_count attribute after a simulated gateway failure."""
        self.email_client.send.side_effect = ConnectionError()
        try:
            self.service.send(recipients=["c@example.com"], subject="Retry", body="Test")
        except Exception:
            pass
        assert self.service._retry_count > 0        # private attribute — violates scope


# --- standalone tests with copy-pasted fixture setup ---


def test_send_to_multiple_recipients_calls_email_client_per_recipient():
    """Sending to two recipients results in two email-client calls."""
    email_client = MagicMock()          # duplicated setup — should use a shared fixture
    redis_mock = MagicMock()
    service = NotificationService(redis=redis_mock, email_client=email_client)

    service.send(recipients=["x@e.com", "y@e.com"], subject="Hi", body="Body")
    assert email_client.send.call_count == 2


def test_queue_notification_stores_message_in_redis():
    """Queuing a notification pushes it to Redis."""
    email_client = MagicMock()          # duplicated setup — should use a shared fixture
    redis_mock = MagicMock()
    service = NotificationService(redis=redis_mock, email_client=email_client)

    service.queue("z@e.com", subject="Queued", body="Later")
    redis_mock.lpush.assert_called_once()


# Missing: test_send_empty_recipients_raises_value_error        (boundary)
# Missing: test_send_none_subject_raises_value_error             (boundary / null input)
# Missing: test_send_smtp_failure_raises_notification_error      (failure path with assertion)
