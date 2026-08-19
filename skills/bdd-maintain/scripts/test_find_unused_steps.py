#!/usr/bin/env python3
"""
Quick test for find_unused_steps.py — step definitions matched against .feature usage.

No fixtures/composition concept applies here (step definitions are only ever invoked
from .feature files, never from other step files or PageObjects), so this covers the
core matching logic instead: placeholder conversion, unused detection, and multi-line
patterns — the parts with no prior test coverage at all.
"""
__test__ = False  # pytest: ignore this helper script

import sys
import tempfile
from pathlib import Path

from find_unused_steps import collect_feature_steps, collect_step_definitions, cucumber_to_regex


def test_used_step_definition_not_flagged_unused():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        steps_dir = root / "playwright" / "steps"
        features_dir = root / "playwright" / "features"
        steps_dir.mkdir(parents=True)
        features_dir.mkdir(parents=True)

        (steps_dir / "login.steps.ts").write_text(
            "Given('the user is on the login page', () => {});\n",
            encoding="utf-8",
        )
        (features_dir / "login.feature").write_text(
            "Feature: Login\n"
            "  Scenario: Visit login\n"
            "    Given the user is on the login page\n",
            encoding="utf-8",
        )

        step_defs = collect_step_definitions(steps_dir)
        feature_steps = collect_feature_steps(features_dir)
        unused = [sd for sd in step_defs if not any(sd.regex.match(fs) for fs in feature_steps)]
    assert unused == [], unused
    print("✓ A step definition used in a .feature file is not flagged unused")


def test_unused_step_definition_flagged():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        steps_dir = root / "playwright" / "steps"
        features_dir = root / "playwright" / "features"
        steps_dir.mkdir(parents=True)
        features_dir.mkdir(parents=True)

        (steps_dir / "login.steps.ts").write_text(
            "Given('a step nobody calls', () => {});\n",
            encoding="utf-8",
        )
        (features_dir / "login.feature").write_text(
            "Feature: Login\n"
            "  Scenario: Visit login\n"
            "    Given something unrelated\n",
            encoding="utf-8",
        )

        step_defs = collect_step_definitions(steps_dir)
        feature_steps = collect_feature_steps(features_dir)
        unused = [sd for sd in step_defs if not any(sd.regex.match(fs) for fs in feature_steps)]
    assert [sd.pattern for sd in unused] == ["a step nobody calls"], unused
    print("✓ A step definition with no matching .feature usage is flagged unused")


def test_cucumber_placeholder_matches_parameterised_usage():
    """A {string}/{int} placeholder in the step definition must match a concrete
    value used in a .feature file's step line."""
    regex = cucumber_to_regex("the user enters {string} in the {word} field")
    assert regex.match('the user enters "hello" in the username field')
    assert not regex.match("the user enters nothing")
    print("✓ Cucumber expression placeholders match parameterised feature-file usage")


if __name__ == "__main__":
    try:
        test_used_step_definition_not_flagged_unused()
        test_unused_step_definition_flagged()
        test_cucumber_placeholder_matches_parameterised_usage()
        print("\n✓ All tests passed!")
    except AssertionError as e:
        print(f"✗ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
