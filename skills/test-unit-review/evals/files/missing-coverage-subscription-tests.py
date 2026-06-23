"""
SubscriptionService tests — missing failure paths and boundary coverage.

Violations present:
  COVERAGE — no failure path when user is already subscribed
  COVERAGE — no failure path when plan is not found
  COVERAGE — no boundary test for empty user_id
  COVERAGE — no boundary test for negative duration_days
  ASSERTIONS — test_upgrade_renews_expiry asserts only that expiry changed, not the new value
"""

import pytest
from unittest.mock import MagicMock
from datetime import datetime, timezone, timedelta


class PlanNotFoundError(Exception):
    pass


class AlreadySubscribedError(Exception):
    pass


class SubscriptionService:
    def __init__(self, plan_repo, user_repo):
        self._plans = plan_repo
        self._users = user_repo

    def subscribe(self, user_id: str, plan_id: str) -> dict:
        if not user_id:
            raise ValueError("user_id must not be empty")
        plan = self._plans.find(plan_id)
        if plan is None:
            raise PlanNotFoundError(f"plan {plan_id!r} not found")
        existing = self._users.get_subscription(user_id)
        if existing is not None:
            raise AlreadySubscribedError(f"user {user_id!r} is already subscribed")
        sub = {"user_id": user_id, "plan_id": plan_id, "status": "active"}
        self._users.save_subscription(sub)
        return sub

    def upgrade(self, user_id: str, new_plan_id: str, duration_days: int) -> dict:
        if duration_days <= 0:
            raise ValueError("duration_days must be positive")
        plan = self._plans.find(new_plan_id)
        if plan is None:
            raise PlanNotFoundError(f"plan {new_plan_id!r} not found")
        expiry = datetime.now(timezone.utc) + timedelta(days=duration_days)
        sub = {"user_id": user_id, "plan_id": new_plan_id, "expiry": expiry.isoformat()}
        self._users.save_subscription(sub)
        return sub


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def plan_repo():
    """Stubbed plan repository returning a standard monthly plan."""
    repo = MagicMock()
    repo.find.return_value = {"id": "plan_monthly", "name": "Monthly", "price": 9.99}
    return repo


@pytest.fixture
def user_repo():
    """Stubbed user repository. No existing subscription by default."""
    repo = MagicMock()
    repo.get_subscription.return_value = None
    return repo


@pytest.fixture
def service(plan_repo, user_repo):
    """SubscriptionService wired with stubbed repositories."""
    return SubscriptionService(plan_repo=plan_repo, user_repo=user_repo)


# ---------------------------------------------------------------------------
# subscribe — happy path only (failure paths missing)
# ---------------------------------------------------------------------------

def test_subscribe_with_valid_inputs_returns_subscription(service):
    """Happy path: valid user and plan returns active subscription dict."""
    result = service.subscribe("user-1", "plan_monthly")
    assert result["user_id"] == "user-1"
    assert result["plan_id"] == "plan_monthly"
    assert result["status"] == "active"


def test_subscribe_saves_subscription_to_repo(service, user_repo):
    """Happy path: successful subscribe calls save_subscription on the user repo."""
    service.subscribe("user-1", "plan_monthly")
    user_repo.save_subscription.assert_called_once()


# ---------------------------------------------------------------------------
# upgrade — happy path only (failure paths and boundary coverage missing)
# ---------------------------------------------------------------------------

def test_upgrade_with_valid_plan_returns_updated_subscription(service):
    """Happy path: valid upgrade returns subscription with new plan id."""
    result = service.upgrade("user-1", "plan_annual", 365)
    assert result["plan_id"] == "plan_annual"
    assert result["user_id"] == "user-1"


def test_upgrade_renews_expiry(service):
    """Happy path: upgrade sets an expiry date on the subscription."""
    result = service.upgrade("user-1", "plan_annual", 365)
    assert result["expiry"] is not None   # ASSERTION: weak — any non-None value passes
