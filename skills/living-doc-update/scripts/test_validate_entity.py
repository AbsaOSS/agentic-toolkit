#!/usr/bin/env python3
"""
Quick test to verify validate_entity.py no longer contradicts the shared lib.

Regression coverage for the bug flagged in PR #9 review: this validator permitted
slug Feature IDs (FEAT-checkout-page) that living_doc_id.py explicitly rejects, its
\\d{3,} rejected US-1 which the shared lib and scan_ac_links.py both accept, and its
own AC_ID_PATTERN rejected the canonical AC:<parent>-<nn> format this skill's own
SKILL.md and evals prescribe (via a stale US-042-AC-1 example that has been fixed
alongside this).
"""
__test__ = False  # pytest: ignore this helper script

import sys

from validate_entity import ID_PATTERNS, AC_ID_PATTERN, validate


def test_single_digit_entity_ids_accepted():
    """US-1 / FEAT-1 / FUNC-1 must be accepted — the shared lib and scan_ac_links.py
    both accept single-digit IDs; a 3+ digit minimum was a validator-only restriction."""
    assert ID_PATTERNS["User Story"].match("US-1")
    assert ID_PATTERNS["Feature"].match("FEAT-1")
    assert ID_PATTERNS["Functionality"].match("FUNC-1")
    print("✓ Single-digit US/FEAT/FUNC IDs are accepted")


def test_slug_feature_id_rejected():
    """FEAT-checkout-page must be rejected — living_doc_id.py's next_entity_id()
    explicitly refuses slug-based Feature IDs at auto-increment time."""
    assert not ID_PATTERNS["Feature"].match("FEAT-checkout-page")
    print("✓ Slug-based Feature IDs are rejected, matching living_doc_id.py")


def test_canonical_ac_id_accepted():
    """AC:<parent>-<nn> is the one canonical grammar — must be accepted."""
    assert AC_ID_PATTERN.match("AC:US-042-01")
    assert AC_ID_PATTERN.match("AC:US-1-01")
    assert AC_ID_PATTERN.match("AC:FUNC-001-01")
    print("✓ Canonical AC:<parent>-<nn> IDs are accepted")


def test_legacy_ac_id_format_rejected():
    """US-042-AC-1 is not the canonical grammar and must be rejected — this
    validator previously used a different, incompatible AC_ID_PATTERN."""
    assert not AC_ID_PATTERN.match("US-042-AC-1")
    print("✓ Legacy US-042-AC-1 format is rejected")


def test_feat_parent_ac_id_rejected():
    """FEAT is never a valid AC parent — Features own Functionalities, not ACs."""
    assert not AC_ID_PATTERN.match("AC:FEAT-016-01")
    print("✓ FEAT-parent AC IDs are rejected")


def test_end_to_end_user_story_with_single_digit_id_validates_clean():
    us = {
        "entity_type": "User Story",
        "id": "US-1",
        "name": "Place an order",
        "status": "active",
        "features": ["FEAT-1"],
        "acceptance_criteria": [
            {"id": "AC:US-1-01", "description": "Order fails when payment is invalid", "state": "active"},
        ],
    }
    issues = validate(us)
    assert issues == [], issues
    print("✓ End-to-end: a US-1 entity with a canonical AC id validates with no issues")


def test_end_to_end_slug_feature_id_flagged():
    feat = {
        "entity_type": "Feature",
        "id": "FEAT-checkout-page",
        "name": "Checkout Page",
        "surface_type": "UI",
        "purpose": "Lets a customer complete a purchase",
        "status": "active",
        "user_stories": ["US-1"],
        "functionalities": [],
        "owners": ["Team"],
    }
    issues = validate(feat)
    id_issues = [i for i in issues if i["field"] == "id" and i["severity"] == "error"]
    assert id_issues, f"expected an id error for a slug Feature ID, got: {issues}"
    print("✓ End-to-end: a slug Feature ID is flagged as an error")


if __name__ == "__main__":
    try:
        test_single_digit_entity_ids_accepted()
        test_slug_feature_id_rejected()
        test_canonical_ac_id_accepted()
        test_legacy_ac_id_format_rejected()
        test_feat_parent_ac_id_rejected()
        test_end_to_end_user_story_with_single_digit_id_validates_clean()
        test_end_to_end_slug_feature_id_flagged()
        print("\n✓ All tests passed!")
    except AssertionError as e:
        print(f"✗ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
