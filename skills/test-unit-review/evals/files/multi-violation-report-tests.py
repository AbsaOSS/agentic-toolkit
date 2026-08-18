"""
ReportService tests — multiple violations across all six standard categories.

Violations present:
  ISOLATION  — setup_method opens a real Redis connection
  SCOPE      — _build_subject (private method) and _retry_count (private attribute) accessed
  NAMING     — test_send, test_error, test_ok do not follow naming convention
  ASSERTIONS — test_send uses 'is not None'; test_ok uses truthy check; test_error has no assert
  COVERAGE   — no failure-path or boundary tests (empty recipient list, None subject, 0-length body)
  FIXTURES   — redis_mock + smtp_client setup copy-pasted across standalone test functions
"""

import pytest
import redis
from unittest.mock import MagicMock


class ReportService:
    def __init__(self, smtp_client, cache):
        self._smtp = smtp_client
        self._cache = cache
        self._retry_count = 0

    def send_report(self, recipient: str, subject: str, body: str) -> bool:
        self._retry_count += 1
        subject_line = self._build_subject(subject)
        self._smtp.send(recipient, subject_line, body)
        self._cache.set(f"last_report:{recipient}", subject)
        return True

    def _build_subject(self, subject: str) -> str:
        return f"[REPORT] {subject}"


# ---------------------------------------------------------------------------
# Class-based tests — ISOLATION VIOLATION: real Redis in setup_method
# ---------------------------------------------------------------------------

class TestReportServiceIntegrated:
    def setup_method(self):
        self.cache = redis.Redis(host="localhost", port=6379)   # real Redis — isolation violated
        self.smtp = MagicMock()
        self.service = ReportService(smtp_client=self.smtp, cache=self.cache)

    def test_send(self):   # NAMING: vague — no condition or expected outcome
        result = self.service.send_report("a@b.com", "Q1", "body text")
        assert result is not None   # ASSERTION: is-not-None is always True for True

    def test_error(self):   # NAMING: vague
        self.smtp.send.side_effect = Exception("SMTP failure")
        try:
            self.service.send_report("a@b.com", "Q1", "body")
        except Exception:
            pass
        # no assertion — test passes regardless of behaviour

    def test_ok(self):   # NAMING: vague
        result = self.service.send_report("a@b.com", "Q1", "body")
        assert result   # ASSERTION: truthy only — True, 1, "ok" would all pass


# ---------------------------------------------------------------------------
# Standalone tests — FIXTURES: copy-pasted setup; SCOPE: private member access
# ---------------------------------------------------------------------------

def test_build_subject_template():
    # SCOPE: calling private method _build_subject directly
    smtp_mock = MagicMock()
    cache_mock = MagicMock()
    service = ReportService(smtp_client=smtp_mock, cache=cache_mock)
    result = service._build_subject("Sales Update")   # private — not allowed
    assert result == "[REPORT] Sales Update"


def test_retry_count_after_send():
    # SCOPE: reading private attribute _retry_count directly
    smtp_mock = MagicMock()       # FIXTURES: setup copy-pasted — identical to next test
    cache_mock = MagicMock()
    service = ReportService(smtp_client=smtp_mock, cache=cache_mock)
    service.send_report("a@b.com", "Q1", "body")
    assert service._retry_count == 1   # private attribute — not allowed


def test_cache_updated_after_send():
    smtp_mock = MagicMock()       # FIXTURES: copy-pasted setup (same as above)
    cache_mock = MagicMock()
    service = ReportService(smtp_client=smtp_mock, cache=cache_mock)
    service.send_report("a@b.com", "Q1", "body")
    cache_mock.set.assert_called_once()   # ASSERTION: no check on key or value arguments
