# Flaky test suite: shared mock state causes order-dependent failures
# Problem: _mock_user is a module-level variable shared across all tests
# When run in one order, tests pass; in another order (or parallel), they fail

import pytest
from unittest.mock import MagicMock

_mock_user = None  # Shared mock state — VIOLATION of isolation rule

class TestUserService:
    def test_create_user_sets_id(self):
        """When create_user is called, the returned user has a non-None ID."""
        global _mock_user
        service = UserService()
        _mock_user = MagicMock(id=123, name="Alice")
        result = service.get_user(_mock_user.id)
        assert result.id == _mock_user.id

    def test_delete_user_clears_cache(self):
        """When delete_user is called, the user is removed from the service."""
        global _mock_user
        # This test depends on test_create_user_sets_id having run first.
        # If it runs first, _mock_user is None, and the test fails.
        assert _mock_user is not None
        service = UserService()
        service.delete_user(_mock_user.id)
        result = service.get_user(_mock_user.id)
        assert result is None

    def test_get_nonexistent_user_returns_none(self):
        """When get_user is called with an unknown ID, None is returned."""
        service = UserService()
        # This test should be independent, but if test_delete_user_clears_cache
        # ran first and modified _mock_user, this test may see stale state.
        result = service.get_user(999)
        assert result is None
