#!/usr/bin/env python3
"""
Quick test to verify compute_gaps.py's Gap 3 (ORPHAN_FEATURE) honours both link
directions.

Regression coverage for the bug flagged in PR #9 review: Gap 3 only checked a
Feature's own `user_stories` back-link; it ignored `features_linked_from_us`
(already built earlier from the forward `us.features` link), so a Feature linked
only from the User Story side was falsely reported ORPHAN_FEATURE — inconsistent
with Gap 4, which honours both directions.
"""
__test__ = False  # pytest: ignore this helper script

import sys

from compute_gaps import compute_gaps


def _orphan_feature_ids(snapshot: dict) -> list[str]:
    return [g["entity"] for g in compute_gaps(snapshot) if g["type"] == "ORPHAN_FEATURE"]


def test_feature_linked_only_from_us_side_not_orphan():
    """A Feature with an empty own user_stories list, but referenced via a User
    Story's forward `features` link, must not be flagged ORPHAN_FEATURE."""
    snapshot = {
        "catalog": {
            "user_stories": [{"id": "US-001", "title": "Do a thing", "features": ["FEAT-001"]}],
            "features": [{"id": "FEAT-001", "name": "Some Surface", "user_stories": []}],
            "functionalities": [],
        },
        "known_test_links": {},
    }
    assert _orphan_feature_ids(snapshot) == [], "back-linked Feature must not be orphan"
    print("✓ Feature linked only via the User Story's forward link is not flagged orphan")


def test_feature_with_own_forward_link_not_orphan():
    """A Feature whose own user_stories list is non-empty must not be flagged
    (this was already correct — guards against a regression)."""
    snapshot = {
        "catalog": {
            "user_stories": [{"id": "US-001", "title": "Do a thing"}],
            "features": [{"id": "FEAT-001", "name": "Some Surface", "user_stories": ["US-001"]}],
            "functionalities": [],
        },
        "known_test_links": {},
    }
    assert _orphan_feature_ids(snapshot) == [], "Feature with its own forward link must not be orphan"
    print("✓ Feature with its own forward user_stories link is not flagged orphan")


def test_truly_unlinked_feature_still_flagged():
    """A Feature genuinely linked from neither side must still be flagged — the
    fix must not silently suppress real orphans."""
    snapshot = {
        "catalog": {
            "user_stories": [{"id": "US-001", "title": "Unrelated", "features": []}],
            "features": [{"id": "FEAT-001", "name": "Orphan Surface", "user_stories": []}],
            "functionalities": [],
        },
        "known_test_links": {},
    }
    assert _orphan_feature_ids(snapshot) == ["FEAT-001"], "genuinely unlinked Feature must be flagged"
    print("✓ A Feature linked from neither side is still correctly flagged orphan")


if __name__ == "__main__":
    try:
        test_feature_linked_only_from_us_side_not_orphan()
        test_feature_with_own_forward_link_not_orphan()
        test_truly_unlinked_feature_still_flagged()
        print("\n✓ All tests passed!")
    except AssertionError as e:
        print(f"✗ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
