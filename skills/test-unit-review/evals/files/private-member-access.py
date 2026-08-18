"""Unit tests for TokenValidator.

VIOLATIONS — scope (accessing private members):
  test_internal_decode_extracts_sub_claim     : calls _decode (private method)
  test_signature_cache_is_populated           : reads _cache (private attribute)
  test_algorithm_whitelist_contains_hs256     : reads _allowed_algorithms (private attribute)
"""
import pytest

from auth.token_validator import TokenValidator

VALID_TOKEN = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ1c2VyMSJ9.SIG"


@pytest.fixture
def validator():
    """TokenValidator initialised with a test secret."""
    return TokenValidator(secret="test-secret")


# --- compliant tests (public interface only) ---


def test_validate_token_returns_true_for_valid_jwt(validator):
    """Valid JWT passes validation via the public validate() method."""
    assert validator.validate(VALID_TOKEN) is True


def test_validate_token_returns_false_for_expired_jwt(validator):
    """Expired token is rejected and validate() returns False."""
    assert validator.validate("expired.token.sig") is False


# --- violating tests (private member access) ---


def test_internal_decode_extracts_sub_claim(validator):
    """Calls private _decode method to verify claim extraction internals."""
    payload = validator._decode(VALID_TOKEN)        # private method — violates scope
    assert payload["sub"] == "user1"


def test_signature_cache_is_populated_after_validation(validator):
    """Reads private _cache attribute to assert caching side-effect."""
    validator.validate(VALID_TOKEN)
    assert VALID_TOKEN in validator._cache          # private attribute — violates scope


def test_algorithm_whitelist_contains_hs256(validator):
    """Reads private _allowed_algorithms attribute directly."""
    assert "HS256" in validator._allowed_algorithms  # private attribute — violates scope
