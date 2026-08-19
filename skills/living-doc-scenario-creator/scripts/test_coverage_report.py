#!/usr/bin/env python3
"""
Quick test to verify coverage_report.py's AC_TAG anchoring.

Regression coverage for the bug flagged in PR #9 review: without an end anchor
(this file uses finditer, not a whole-line match, so the fix uses a (?!\\d)
lookahead instead), @AC:US-1-011 matched as US-1-01 with the trailing digit
silently dropped — a malformed tag was canonicalized and counted as coverage
for the wrong (truncated) ID instead of being excluded.
"""
__test__ = False  # pytest: ignore this helper script

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "shared" / "lib"))
from ac_tag import iter_ac_tags  # noqa: E402 — path must be set up first

from coverage_report import get_ac_tags_above  # noqa: E402


def test_valid_tag_matches():
    matches = list(iter_ac_tags("@AC:US-1-01"))
    assert len(matches) == 1 and matches[0].group(1) == "US-1-01", matches
    print("✓ Valid @AC: tag matches")


def test_trailing_extra_digit_does_not_match():
    """@AC:US-1-011 must not silently match as @AC:US-1-01."""
    assert list(iter_ac_tags("@AC:US-1-011")) == []
    print("✓ Malformed tag with a trailing extra digit does not match at all")


def test_trailing_extra_digit_ignored_alongside_other_tags_on_same_line():
    """finditer has no line-level $ anchor, so a malformed tag must not swallow or
    corrupt a sibling tag on the same line."""
    matches = list(iter_ac_tags("@AC:US-1-011 @AC:FUNC-002-03 @Regression"))
    ids = [m.group(1) for m in matches]
    assert ids == ["FUNC-002-03"], ids
    print("✓ Malformed tag is skipped without corrupting a valid sibling tag on the same line")


def test_feat_and_slug_parent_tags_no_longer_covered():
    """The bug this fix closes: coverage_report.py used to accept FEAT and
    slug-parent tags that scan_ac_links.py rejected as malformed, so the same tag
    was 'covered' in one tool and 'malformed' in the other. Now both share the same
    US|FUNC-only grammar."""
    lines = ["  @AC:FEAT-checkout-page-01", "  Scenario: Something", "    Given a step"]
    assert get_ac_tags_above(lines, 1) == [], "FEAT/slug-parent tags must not count as coverage"
    print("✓ FEAT and slug-parent tags no longer count toward coverage (matches scan_ac_links.py)")


def test_get_ac_tags_above_excludes_truncated_id():
    lines = [
        "  @AC:US-1-011",
        "  Scenario: Something",
        "    Given a step",
    ]
    ac_ids = get_ac_tags_above(lines, 1)
    assert ac_ids == [], f"malformed tag should not be counted as coverage, got: {ac_ids}"
    print("✓ get_ac_tags_above() excludes a truncated/malformed tag from coverage")


def test_get_ac_tags_above_still_canonicalizes_valid_id():
    lines = [
        "  @AC:US-1-01",
        "  Scenario: Something",
        "    Given a step",
    ]
    ac_ids = get_ac_tags_above(lines, 1)
    assert ac_ids == ["US-001-01"], ac_ids
    print("✓ get_ac_tags_above() still canonicalizes a valid tag")


if __name__ == "__main__":
    try:
        test_valid_tag_matches()
        test_trailing_extra_digit_does_not_match()
        test_trailing_extra_digit_ignored_alongside_other_tags_on_same_line()
        test_get_ac_tags_above_excludes_truncated_id()
        test_get_ac_tags_above_still_canonicalizes_valid_id()
        test_feat_and_slug_parent_tags_no_longer_covered()
        print("\n✓ All tests passed!")
    except AssertionError as e:
        print(f"✗ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
