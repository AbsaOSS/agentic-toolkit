"""
Test file with a wrong-patch-target bug — eval fixture for test-mocking-patterns.

The developer is patching `requests.get` at its source module location instead of
at the location where it is imported inside the module under test.
As a result, the real HTTP call is still made and the stub is never used.
"""

import pytest
from unittest.mock import patch, MagicMock

# The source module imports requests directly:
#   import requests as http_lib
# So the correct patch target is:
#   "source_email_notification_service.http_lib.get"
# But the test patches the source module instead — this has no effect.

from source_email_notification_service import EmailNotificationService


def test_notify_returns_true_for_valid_user():
    """Should return True when the preferences API returns 200 and email is sent."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"email": "alice@example.com"}

    # ❌ Wrong patch target — patching requests at its source has no effect
    # on the module under test which has already imported it as http_lib.
    with patch("requests.get", return_value=mock_response):
        smtp_mock = MagicMock()
        metrics_mock = MagicMock()
        service = EmailNotificationService(smtp_client=smtp_mock, metrics=metrics_mock)

        # This will make a real HTTP call because the patch did not intercept http_lib.get
        result = service.notify("user-1", "Hello!")
        assert result is True


def test_notify_returns_false_when_prefs_api_unavailable():
    """Should return False when the preferences API returns a non-200 status."""
    mock_response = MagicMock()
    mock_response.status_code = 503

    # ❌ Same wrong patch target
    with patch("requests.get", return_value=mock_response):
        smtp_mock = MagicMock()
        metrics_mock = MagicMock()
        service = EmailNotificationService(smtp_client=smtp_mock, metrics=metrics_mock)

        result = service.notify("user-1", "Hello!")
        assert result is False
