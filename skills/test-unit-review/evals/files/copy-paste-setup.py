"""Unit tests for UserProfileService.

VIOLATIONS — fixture management:
  All four tests contain an identical setup block (repo, cache, service construction)
  copy-pasted inline.  No shared @pytest.fixture or conftest.py helper is used.
  Fixtures are not documented with their purpose or side effects.
"""
from unittest.mock import MagicMock

import pytest

from services.user_profile_service import UserProfileService


def test_get_profile_returns_display_name():
    """Returns the user's display name when the user exists in the repository."""
    # duplicated setup — should be a shared fixture
    repo = MagicMock()
    cache = MagicMock()
    cache.get.return_value = None
    repo.find_by_id.return_value = {"id": "u1", "display_name": "Alice", "email": "a@example.com"}
    service = UserProfileService(repo=repo, cache=cache)

    profile = service.get_profile("u1")
    assert profile["display_name"] == "Alice"


def test_get_profile_caches_result_after_first_call():
    """Result is cached so the repository is only queried once for repeated calls."""
    # duplicated setup
    repo = MagicMock()
    cache = MagicMock()
    cache.get.return_value = None
    repo.find_by_id.return_value = {"id": "u1", "display_name": "Alice", "email": "a@example.com"}
    service = UserProfileService(repo=repo, cache=cache)

    service.get_profile("u1")
    service.get_profile("u1")
    assert cache.set.call_count == 1
    assert repo.find_by_id.call_count == 1  # second call should hit the cache


def test_get_profile_unknown_user_raises_not_found():
    """Requesting a user that does not exist raises KeyError."""
    # duplicated setup
    repo = MagicMock()
    cache = MagicMock()
    cache.get.return_value = None
    repo.find_by_id.return_value = None
    service = UserProfileService(repo=repo, cache=cache)

    with pytest.raises(KeyError):
        service.get_profile("unknown")


def test_update_email_persists_change():
    """Updating the email address delegates a save call to the repository."""
    # duplicated setup yet again
    repo = MagicMock()
    cache = MagicMock()
    cache.get.return_value = None
    repo.find_by_id.return_value = {"id": "u1", "display_name": "Alice", "email": "old@example.com"}
    service = UserProfileService(repo=repo, cache=cache)

    service.update_email("u1", "new@example.com")
    repo.save.assert_called_once()
