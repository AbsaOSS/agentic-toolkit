#!/usr/bin/env python3
"""
Quick test to verify trace_entities() matches known_test_links correctly.

Regression coverage for the bug flagged in PR #9 review: canonical AC:US-001-01
keys fell through a prefix check that was always false (acs_requiring_review /
scenarios_requiring_rerun always empty), while legacy US-042-AC-1 keys made
`owner` always truthy (every AC flagged regardless of the change) — "the
feature's core output is either empty or everything." No eval exercised
known_test_links, so nothing caught it.
"""
__test__ = False  # pytest: ignore this helper script

import sys

from trace_impact import classify_file, trace_entities


def _catalog(known_test_links):
    return {
        "catalog": {
            "features": [
                {"id": "FEAT-001", "name": "Checkout Page",
                 "functionalities": ["FUNC-001"], "user_stories": ["US-001"]},
            ],
            "functionalities": [
                {"id": "FUNC-001", "name": "Validate Cart"},
            ],
            "user_stories": [
                {"id": "US-001", "title": "Place an online order"},
            ],
        },
        "known_test_links": known_test_links,
    }


def test_canonical_ac_matches_affected_entities():
    """AC:<US|FUNC>-<n>-<nn> keys whose parent is affected are returned."""
    catalog = _catalog({
        "AC:US-001-01": "tests/features/checkout.feature::places an order",
        "AC:FUNC-001-01": "test_validate_cart.py::test_empty_cart",
    })
    result = trace_entities(["FEAT-001"], catalog)
    assert result["acs_requiring_review"] == ["AC:US-001-01", "AC:FUNC-001-01"], result
    assert result["scenarios_requiring_rerun"] == [
        "tests/features/checkout.feature::places an order",
        "test_validate_cart.py::test_empty_cart",
    ], result
    print("✓ Canonical AC IDs under an affected parent are matched")


def test_unrelated_ac_excluded():
    """An AC whose parent isn't reachable from the changed Feature must be excluded —
    guards against the 'everything is flagged' failure mode."""
    catalog = _catalog({
        "AC:US-001-01": "tests/features/checkout.feature::places an order",
        "AC:US-999-01": "tests/unrelated.feature::something else",
    })
    result = trace_entities(["FEAT-001"], catalog)
    assert result["acs_requiring_review"] == ["AC:US-001-01"], result
    assert "AC:US-999-01" not in result["acs_requiring_review"], result
    print("✓ ACs belonging to unaffected entities are excluded")


def test_null_test_link_is_reviewed_but_not_rerun():
    """An AC with no linked scenario (null) still needs review, but contributes
    nothing to scenarios_requiring_rerun."""
    catalog = _catalog({"AC:US-001-01": None})
    result = trace_entities(["FEAT-001"], catalog)
    assert result["acs_requiring_review"] == ["AC:US-001-01"], result
    assert result["scenarios_requiring_rerun"] == [], result
    print("✓ Null test links are reviewed but do not trigger a rerun entry")


def test_legacy_and_malformed_ids_are_ignored_not_crash():
    """Legacy 'US-042-AC-1'-style keys and other malformed IDs no longer match
    anything (the grammar decision rejected that format) and must not raise."""
    catalog = _catalog({
        "US-001-AC-1": "tests/legacy.feature::old style",
        "not-an-ac-id": "tests/garbage.feature::noise",
    })
    result = trace_entities(["FEAT-001"], catalog)
    assert result["acs_requiring_review"] == [], result
    assert result["scenarios_requiring_rerun"] == [], result
    print("✓ Legacy/malformed AC IDs are ignored, not crashed on or over-matched")


def test_empty_known_test_links():
    """No known_test_links section at all must not crash."""
    catalog = _catalog({})
    result = trace_entities(["FEAT-001"], catalog)
    assert result["acs_requiring_review"] == [], result
    assert result["scenarios_requiring_rerun"] == [], result
    print("✓ Empty known_test_links produces no matches, no crash")


def test_real_domain_code_not_misclassified_as_test():
    """Files whose name merely contains 'test'/'spec' as a substring must not be
    classified test_or_mock — that hides real domain changes behind impact 'None'."""
    for path in (
        "src/latestOffers/Service.java",
        "Inspector.ts",
        "attestation/AttestationService.java",
        "Contestant.java",
        "Specification.java",
    ):
        assert classify_file(path) != "test_or_mock", f"{path} misclassified as test_or_mock"
    print("✓ Real domain files with 'test'/'spec' substrings are not misclassified")


def test_actual_test_and_mock_files_still_classified():
    """Real test/mock/spec/fixture/stub files, in any common naming style, must still
    be caught — the word-boundary fix must not lose recall."""
    for path in (
        "src/auth/LoginControllerTest.java",
        "test_validate_cart.py",
        "tests/features/checkout.feature",
        "MockNotificationClient.java",
        "__tests__/foo.test.js",
        "src/payments/PromoService.spec.ts",
        "fixtures/data.json",
        "stub_server.py",
    ):
        assert classify_file(path) == "test_or_mock", f"{path} should classify as test_or_mock"
    print("✓ Real test/mock/spec/fixture/stub files across naming styles are still caught")


if __name__ == "__main__":
    try:
        test_canonical_ac_matches_affected_entities()
        test_unrelated_ac_excluded()
        test_null_test_link_is_reviewed_but_not_rerun()
        test_legacy_and_malformed_ids_are_ignored_not_crash()
        test_empty_known_test_links()
        test_real_domain_code_not_misclassified_as_test()
        test_actual_test_and_mock_files_still_classified()
        print("\n✓ All tests passed!")
    except AssertionError as e:
        print(f"✗ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
