#!/usr/bin/env python3
"""
Regression coverage for project-profile.schema.json's ac_states / pageobject_statuses
constraints (living-doc canon: ac_states is a subset of the four canonical states;
there is no PageObject status vocabulary at all).
"""
__test__ = False  # pytest: ignore this helper script

import json
import sys
from pathlib import Path

try:
    import jsonschema
except ImportError:
    print(
        "Error: the 'jsonschema' package is required to run this test.\n"
        "Install it with: pip install jsonschema",
        file=sys.stderr,
    )
    sys.exit(1)

SCHEMA_PATH = Path(__file__).parent / "project-profile.schema.json"
SCHEMA = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

BASE_PROFILE = {
    "test_id_attribute": "data-cy",
    "feature_dirs": {"user_story": "features/liv_doc_us", "functionality": "features/liv_doc_func"},
    "paths": {"bdd_artifacts": ".copilot/bdd", "pageobjects": "playwright/pages", "steps": "playwright/steps"},
}


def is_valid(profile: dict) -> bool:
    try:
        jsonschema.validate(profile, SCHEMA)
        return True
    except jsonschema.ValidationError:
        return False


def test_canonical_ac_states_accepted():
    profile = {**BASE_PROFILE, "ac_states": ["planned", "in_review", "active", "deprecated"]}
    assert is_valid(profile), "canonical ac_states must be accepted"
    print("✓ Canonical ac_states list is accepted")


def test_ac_states_field_omission_allowed():
    assert is_valid(dict(BASE_PROFILE)), "omitting ac_states must be allowed"
    print("✓ Omitting ac_states is allowed")


def test_ac_states_title_case_rejected():
    profile = {**BASE_PROFILE, "ac_states": ["In Review"]}
    assert not is_valid(profile), "ac_states: [In Review] must be rejected"
    print("✓ ac_states: [In Review] is rejected")


def test_ac_states_unknown_value_rejected():
    profile = {**BASE_PROFILE, "ac_states": ["done"]}
    assert not is_valid(profile), "ac_states: [done] must be rejected"
    print("✓ ac_states: [done] is rejected")


def test_ac_states_duplicate_rejected():
    profile = {**BASE_PROFILE, "ac_states": ["active", "active"]}
    assert not is_valid(profile), "ac_states: [active, active] must be rejected"
    print("✓ ac_states: [active, active] is rejected")


def test_pageobject_statuses_key_rejected():
    profile = {**BASE_PROFILE, "pageobject_statuses": ["planned", "candidate", "active", "deprecated"]}
    assert not is_valid(profile), "a pageobject_statuses key must be rejected"
    print("✓ A pageobject_statuses key is rejected")


if __name__ == "__main__":
    try:
        test_canonical_ac_states_accepted()
        test_ac_states_field_omission_allowed()
        test_ac_states_title_case_rejected()
        test_ac_states_unknown_value_rejected()
        test_ac_states_duplicate_rejected()
        test_pageobject_statuses_key_rejected()
        print("\n✓ All tests passed!")
    except AssertionError as e:
        print(f"✗ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
