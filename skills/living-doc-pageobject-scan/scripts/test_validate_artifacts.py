#!/usr/bin/env python3
"""
Quick test to verify validate_artifacts.py's credential-leak regex.

Regression coverage for the bug flagged in PR #9 review: the keyword had to be the
key's exact prefix, so db_password:, aws_secret_access_key:, admin_token: all slipped
through; a YAML list item (- password: hunter2) also escaped the ^\\s* anchor.
"""
__test__ = False  # pytest: ignore this helper script

import sys

from validate_artifacts import CREDENTIAL_LEAK_RE


def _matches(line: str) -> bool:
    return bool(CREDENTIAL_LEAK_RE.match(line))


def test_compound_key_names_now_detected():
    """The keyword no longer has to be the exact key — compound names must be caught."""
    for line in (
        "db_password: hunter2",
        "aws_secret_access_key: AKIAABC123",
        "admin_token: abc123",
    ):
        assert _matches(line), f"expected a credential leak match for: {line!r}"
    print("✓ Compound credential-like key names (db_password, aws_secret_access_key, admin_token) are detected")


def test_yaml_list_item_now_detected():
    """A YAML list item previously escaped the ^\\s* anchor."""
    for line in ("- password: hunter2", "  - client_secret: xyz"):
        assert _matches(line), f"expected a credential leak match for: {line!r}"
    print("✓ YAML list-item credential literals are detected")


def test_plain_key_still_detected():
    """Guard against a regression on the original, already-working case."""
    assert _matches("password: hunter2")
    print("✓ A plain 'password: <literal>' key is still detected")


def test_safe_patterns_still_excluded():
    """env:, ${...}, <...>, ~, null, and empty values must never be flagged."""
    for line in (
        "password: env:MY_VAR",
        "password: ${SECRET}",
        "password: <from-vault>",
        "password: ~",
        "password: null",
        "password:",
        "credentials_source: .env",
    ):
        assert not _matches(line), f"unexpected credential leak match for safe line: {line!r}"
    print("✓ Safe reference patterns (env:, ${...}, <...>, ~, null) are still excluded")


if __name__ == "__main__":
    try:
        test_compound_key_names_now_detected()
        test_yaml_list_item_now_detected()
        test_plain_key_still_detected()
        test_safe_patterns_still_excluded()
        print("\n✓ All tests passed!")
    except AssertionError as e:
        print(f"✗ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
