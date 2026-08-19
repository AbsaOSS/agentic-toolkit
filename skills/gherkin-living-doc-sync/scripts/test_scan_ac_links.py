#!/usr/bin/env python3
"""
Quick test to verify scan_ac_links.py's AC_TAG anchoring.

Regression coverage for the bug flagged in PR #9 review: without an end anchor,
@AC:US-1-011 matched as US-1-01 with the trailing digit silently dropped, so a
malformed tag was accepted under the wrong (truncated) ID instead of being
flagged as malformed.
"""
__test__ = False  # pytest: ignore this helper script

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "shared" / "lib"))
from ac_tag import match_ac_tag  # noqa: E402 — path must be set up first

from scan_ac_links import scan_file  # noqa: E402


def test_valid_tag_matches_in_full():
    m = match_ac_tag("@AC:US-1-01")
    assert m is not None, "valid tag should match"
    assert m.group(0) == "@AC:US-1-01", m.group(0)
    print("✓ Valid @AC: tag matches in full")


def test_trailing_extra_digit_does_not_match():
    """@AC:US-1-011 must not silently match as @AC:US-1-01."""
    assert match_ac_tag("@AC:US-1-011") is None
    print("✓ Malformed tag with a trailing extra digit does not match at all")


def test_trailing_garbage_does_not_match():
    assert match_ac_tag("@AC:US-1-01x") is None
    print("✓ Malformed tag with trailing non-digit garbage does not match at all")


def test_aspect_param_still_matches():
    m = match_ac_tag("@AC:US-001-01/aspect:username-input")
    assert m is not None
    assert m.group(1) == "US-001-01", m.group(1)
    print("✓ Aspect-param tags still match correctly")


def test_feat_parent_still_rejected():
    """FEAT is never a valid AC parent — Features own Functionalities, not ACs."""
    assert match_ac_tag("@AC:FEAT-016-01") is None
    print("✓ FEAT-parent tags are still rejected (shared grammar, US|FUNC only)")


def test_scan_file_flags_truncated_tag_as_malformed():
    """End-to-end: a scenario tagged @AC:US-1-011 must be reported malformed,
    not silently accepted as AC:US-1-01."""
    content = (
        "Feature: Example\n"
        "  @AC:US-1-011\n"
        "  Scenario: Something\n"
        "    Given a step\n"
    )
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "features" / "liv_doc_us" / "us-1-example.feature"
        path.parent.mkdir(parents=True)
        path.write_text(content, encoding="utf-8")
        issues = scan_file(path)
    malformed = [i for i in issues if i["issue"] == "malformed_ac_id"]
    assert malformed, f"expected a malformed_ac_id issue, got: {issues}"
    print("✓ scan_file() flags a truncated tag as malformed, not as AC:US-1-01")


if __name__ == "__main__":
    try:
        test_valid_tag_matches_in_full()
        test_trailing_extra_digit_does_not_match()
        test_trailing_garbage_does_not_match()
        test_aspect_param_still_matches()
        test_feat_parent_still_rejected()
        test_scan_file_flags_truncated_tag_as_malformed()
        print("\n✓ All tests passed!")
    except AssertionError as e:
        print(f"✗ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
