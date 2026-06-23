"""
Compliant unit tests for AuthService — review eval fixture.

All standards are met: isolation, scope, naming, assertions, coverage, fixtures.
"""

import pytest
from unittest.mock import MagicMock
from datetime import datetime, timezone, timedelta


class UnauthorizedError(Exception):
    pass


class AuthService:
    def __init__(self, token_repo, session_store):
        self._token_repo = token_repo
        self._sessions = session_store

    def login(self, username: str, password: str) -> str:
        record = self._token_repo.find_user(username)
        if record is None or record["password_hash"] != _hash(password):
            raise UnauthorizedError("invalid credentials")
        token = self._token_repo.create_token(username)
        self._sessions.store(username, token)
        return token

    def logout(self, token: str) -> None:
        self._sessions.invalidate(token)


def _hash(value: str) -> str:
    return f"hashed:{value}"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def token_repo():
    """Stubbed token repository with a single valid user record."""
    repo = MagicMock()
    repo.find_user.return_value = {
        "username": "alice",
        "password_hash": "hashed:secret",
    }
    repo.create_token.return_value = "tok_abc123"
    return repo


@pytest.fixture
def session_store():
    """Stubbed session store. Side effects are not tested here."""
    return MagicMock()


@pytest.fixture
def auth_service(token_repo, session_store):
    """AuthService wired with stubbed dependencies — no real I/O."""
    return AuthService(token_repo=token_repo, session_store=session_store)


# ---------------------------------------------------------------------------
# login
# ---------------------------------------------------------------------------

def test_login_with_valid_credentials_returns_token(auth_service):
    """Successful login returns the token created by the repository."""
    token = auth_service.login("alice", "secret")
    assert token == "tok_abc123"


def test_login_stores_token_in_session(auth_service, session_store):
    """Successful login stores the issued token in the session store."""
    auth_service.login("alice", "secret")
    session_store.store.assert_called_once_with("alice", "tok_abc123")


def test_login_with_unknown_user_raises_unauthorized(auth_service, token_repo):
    """Login fails with UnauthorizedError when the username is not found."""
    token_repo.find_user.return_value = None
    with pytest.raises(UnauthorizedError):
        auth_service.login("unknown", "secret")


def test_login_with_wrong_password_raises_unauthorized(auth_service):
    """Login fails with UnauthorizedError when the password hash does not match."""
    with pytest.raises(UnauthorizedError):
        auth_service.login("alice", "wrong-password")


# ---------------------------------------------------------------------------
# logout
# ---------------------------------------------------------------------------

def test_logout_invalidates_session_token(auth_service, session_store):
    """Logout calls invalidate on the session store with the given token."""
    auth_service.logout("tok_abc123")
    session_store.invalidate.assert_called_once_with("tok_abc123")
