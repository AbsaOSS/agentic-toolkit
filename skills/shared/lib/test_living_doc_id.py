#!/usr/bin/env python3
"""
Quick test to verify next_entity_id() behavior with slug-based Feature IDs.
"""
__test__ = False  # pytest: ignore this helper script

import sys

from living_doc_id import next_entity_id


def test_numeric_feat_ids():
    """Numeric FEAT IDs should auto-increment as before."""
    catalog = {
        "features": [
            {"id": "FEAT-001", "name": "Feature 1"},
            {"id": "FEAT-002", "name": "Feature 2"},
        ]
    }
    next_id = next_entity_id(catalog, "FEAT")
    assert next_id == "FEAT-003", f"Expected FEAT-003, got {next_id}"
    print("✓ Numeric FEAT IDs auto-increment correctly")


def test_slug_based_feat_ids_raise_error():
    """Slug-based FEAT IDs should raise ValueError."""
    # Contrived slug-based FEAT IDs to stress-test validation.
    # Production catalogs must use numeric IDs only (FEAT-001, FEAT-002, ...)
    catalog = {
        "features": [
            {"id": "FEAT-checkout-page", "name": "Checkout Page"},
            {"id": "FEAT-orders-api", "name": "Orders API"},
        ]
    }
    try:
        next_entity_id(catalog, "FEAT")
        raise AssertionError("Expected ValueError for slug-based FEAT IDs, but none was raised")
    except ValueError as e:
        error_msg = str(e)
        assert "non-numeric" in error_msg, f"Error message missing 'non-numeric': {error_msg}"
        assert "Slug-based Feature IDs" in error_msg, f"Error should mention slug-based IDs: {error_msg}"
        assert "FEAT-checkout-page" in error_msg, f"Error should mention FEAT-checkout-page: {error_msg}"
        print(f"✓ Slug-based FEAT IDs raise clear error (as expected)")
        return True


def test_us_numeric_ids():
    """US numeric IDs should work normally."""
    catalog = {
        "user_stories": [
            {"id": "US-001", "name": "Story 1"},
            {"id": "US-002", "name": "Story 2"},
        ]
    }
    next_id = next_entity_id(catalog, "US")
    assert next_id == "US-003", f"Expected US-003, got {next_id}"
    print("✓ US numeric IDs auto-increment correctly")


def test_func_numeric_ids():
    """FUNC numeric IDs should work normally."""
    catalog = {
        "functionalities": [
            {"id": "FUNC-001", "name": "Functionality 1"},
        ]
    }
    next_id = next_entity_id(catalog, "FUNC")
    assert next_id == "FUNC-002", f"Expected FUNC-002, got {next_id}"
    print("✓ FUNC numeric IDs auto-increment correctly")


def test_empty_collection():
    """Empty collection should return X-001."""
    catalog = {"features": []}
    next_id = next_entity_id(catalog, "FEAT")
    assert next_id == "FEAT-001", f"Expected FEAT-001, got {next_id}"
    print("✓ Empty FEAT collection returns FEAT-001")


if __name__ == "__main__":
    try:
        test_numeric_feat_ids()
        test_us_numeric_ids()
        test_func_numeric_ids()
        test_empty_collection()
        if not test_slug_based_feat_ids_raise_error():
            sys.exit(1)
        print("\n✓ All tests passed!")
    except AssertionError as e:
        print(f"✗ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
