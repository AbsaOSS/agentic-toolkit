"""Unit tests for PaymentService.

Tests cover the public interface only.  All I/O (gateway, logger) is stubbed via
fixtures.  Shared fixtures are defined once; no copy-paste setup.
"""
import pytest
from unittest.mock import MagicMock

from services.payment_service import PaymentService, InsufficientFundsError, PaymentError


# --- fixtures ---


@pytest.fixture
def gateway():
    """Stub for the external payment gateway; returns a canned success response."""
    mock = MagicMock()
    mock.charge.return_value = {"status": "ok", "transaction_id": "txn_001"}
    return mock


@pytest.fixture
def logger():
    """Stub logger so log-call assertions can be made without real I/O."""
    return MagicMock()


@pytest.fixture
def service(gateway, logger):
    """PaymentService wired to stub dependencies."""
    return PaymentService(gateway=gateway, logger=logger)


# --- charge: success path ---


def test_charge_valid_amount_returns_transaction_id(service, gateway):
    """Charging a positive amount returns the transaction ID supplied by the gateway."""
    result = service.charge(amount=100, currency="ZAR", account_id="acc_1")
    assert result == "txn_001"


def test_charge_valid_amount_calls_gateway_once(service, gateway):
    """Exactly one gateway call is made per charge invocation."""
    service.charge(amount=100, currency="ZAR", account_id="acc_1")
    gateway.charge.assert_called_once_with(100, "ZAR", "acc_1")


def test_charge_success_emits_info_log(service, logger):
    """A single info-level log entry is emitted after a successful charge."""
    service.charge(amount=100, currency="ZAR", account_id="acc_1")
    logger.info.assert_called_once()


# --- charge: boundary values ---


def test_charge_minimum_positive_amount_succeeds(service):
    """Charging the minimum positive amount (0.01) completes without error."""
    result = service.charge(amount=0.01, currency="ZAR", account_id="acc_1")
    assert result == "txn_001"


# --- charge: failure paths ---


def test_charge_zero_amount_raises_value_error(service):
    """Charging zero is rejected with ValueError before contacting the gateway."""
    with pytest.raises(ValueError, match="amount must be positive"):
        service.charge(amount=0, currency="ZAR", account_id="acc_1")


def test_charge_negative_amount_raises_value_error(service):
    """Negative amounts are rejected immediately without reaching the gateway."""
    with pytest.raises(ValueError, match="amount must be positive"):
        service.charge(amount=-50, currency="ZAR", account_id="acc_1")


def test_charge_gateway_timeout_raises_payment_error(service, gateway):
    """A gateway timeout is surfaced to the caller as a PaymentError."""
    gateway.charge.side_effect = PaymentError("gateway timeout")
    with pytest.raises(PaymentError):
        service.charge(amount=100, currency="ZAR", account_id="acc_1")


def test_charge_insufficient_funds_raises_insufficient_funds_error(service, gateway):
    """Gateway returning insufficient-funds propagates as InsufficientFundsError."""
    gateway.charge.side_effect = InsufficientFundsError("balance too low")
    with pytest.raises(InsufficientFundsError):
        service.charge(amount=9999, currency="ZAR", account_id="acc_low")


def test_charge_empty_account_id_raises_value_error(service):
    """An empty account_id string is rejected with a descriptive ValueError."""
    with pytest.raises(ValueError, match="account_id"):
        service.charge(amount=100, currency="ZAR", account_id="")
