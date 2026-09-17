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

import json
import subprocess
import sys
import tempfile
from pathlib import Path

from validate_entity import ID_PATTERNS, AC_ID_PATTERN, validate, load_ac_states_from_profile, format_report

VALIDATE_ENTITY_PY = Path(__file__).parent / "validate_entity.py"


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
        "user_stories": ["US-1"],
        "functionalities": [],
        "owners": ["Team"],
    }
    issues = validate(feat)
    id_issues = [i for i in issues if i["field"] == "id" and i["severity"] == "error"]
    assert id_issues, f"expected an id error for a slug Feature ID, got: {issues}"
    print("✓ End-to-end: a slug Feature ID is flagged as an error")


def test_feature_with_status_field_rejected():
    """A Feature has no status field — its state is derived from its Functionalities."""
    feat = {
        "entity_type": "Feature",
        "id": "FEAT-1",
        "name": "Checkout Page",
        "surface_type": "UI",
        "purpose": "Lets a customer complete a purchase",
        "status": "active",
        "user_stories": ["US-1"],
        "functionalities": ["FUNC-1"],
        "owners": ["Team"],
    }
    issues = validate(feat)
    status_errors = [i for i in issues if i["field"] == "status" and i["severity"] == "error"]
    assert status_errors, f"expected a status error for a Feature carrying 'status', got: {issues}"
    print("✓ A Feature carrying a 'status' field is flagged as an error")


def test_feature_surface_type_canonical_set_only():
    """VALID_SURFACE_TYPES must match the canonical living-doc-glossary exactly: UI and API
    are the only surface types. Service/Worker/Module/Library are not canon and must be
    rejected, even though an older living-doc-create-feature/SKILL.md draft once documented
    them — that skill has since been realigned to UI/API only."""
    def make_feature(surface_type: str) -> dict:
        return {
            "entity_type": "Feature",
            "id": "FEAT-1",
            "name": "Order Processor",
            "surface_type": surface_type,
            "purpose": "Processes orders in the background",
            "user_stories": ["US-1"],
            "functionalities": [],
            "owners": ["Team"],
        }

    for surface_type in ("UI", "API"):
        issues = validate(make_feature(surface_type))
        surface_errors = [i for i in issues if i["field"] == "surface_type"]
        assert not surface_errors, f"expected no surface_type error for '{surface_type}', got: {surface_errors}"

    for surface_type in ("Service", "Worker", "Module", "Library", "Frontend"):
        issues = validate(make_feature(surface_type))
        surface_errors = [i for i in issues if i["field"] == "surface_type" and i["severity"] == "error"]
        assert surface_errors, f"expected a surface_type error for '{surface_type}', got: {issues}"
    print("✓ Feature surface_type accepts only the canonical UI/API set and rejects everything else")


def test_orphan_feature_reported_distinctly():
    """A Feature with no linked User Stories and no Functionalities is an ORPHAN_FEATURE,
    not a 'candidate' status — there is no status field to tag it with."""
    feat = {
        "entity_type": "Feature",
        "id": "FEAT-2",
        "name": "Exploratory Page",
        "surface_type": "UI",
        "purpose": "An exploratory surface with no confirmed links yet",
        "user_stories": [],
        "functionalities": [],
        "owners": ["Team"],
    }
    issues = validate(feat)
    orphan_issues = [i for i in issues if i["field"] == "ORPHAN_FEATURE"]
    assert orphan_issues, f"expected an ORPHAN_FEATURE warning, got: {issues}"
    print("✓ A Feature with no User Stories and no Functionalities is flagged as ORPHAN_FEATURE")


def test_orphan_feature_with_functionalities_still_reported():
    """gap-finder's ORPHAN_FEATURE gap (compute_gaps.py) fires on a missing User Story link
    alone. A Feature that owns Functionalities but has no User Stories must still be flagged
    as ORPHAN_FEATURE, not downgraded to a generic 'user_stories' warning."""
    feat = {
        "entity_type": "Feature",
        "id": "FEAT-3",
        "name": "Reporting Engine",
        "surface_type": "UI",
        "purpose": "Generates account activity reports for internal review",
        "user_stories": [],
        "functionalities": ["FUNC-1"],
        "owners": ["Team"],
    }
    issues = validate(feat)
    orphan_issues = [i for i in issues if i["field"] == "ORPHAN_FEATURE"]
    assert orphan_issues, f"expected an ORPHAN_FEATURE warning, got: {issues}"
    func_issues = [i for i in issues if i["field"] == "functionalities"]
    assert not func_issues, f"did not expect a functionalities warning, got: {func_issues}"
    print("✓ A Feature with Functionalities but no User Stories is still flagged as ORPHAN_FEATURE")


def test_orphan_feature_suppressed_by_catalog_back_link():
    """A Feature with an empty own `user_stories` list, but referenced via a User
    Story's forward `features` link in the catalog, must not be flagged ORPHAN_FEATURE —
    matches compute_gaps.py's Gap 3, which honours both link directions."""
    feat = {
        "entity_type": "Feature",
        "id": "FEAT-4",
        "name": "Back-linked Surface",
        "surface_type": "UI",
        "purpose": "A surface linked only from the User Story side",
        "user_stories": [],
        "functionalities": ["FUNC-1"],
        "owners": ["Team"],
    }
    catalog = {
        "catalog": {
            "user_stories": [{"id": "US-1", "name": "Do a thing", "features": ["FEAT-4"]}],
            "features": [],
            "functionalities": [],
        },
    }
    issues = validate(feat, catalog)
    orphan_issues = [i for i in issues if i["field"] == "ORPHAN_FEATURE"]
    assert not orphan_issues, f"did not expect ORPHAN_FEATURE for a catalog back-linked Feature, got: {orphan_issues}"
    print("✓ A Feature linked only via a catalog User Story's forward link is not flagged orphan")


def test_functionality_warning_suppressed_by_catalog_back_link():
    """A Feature with an empty own `functionalities` list, but referenced via a
    Functionality's `parent_feature` back-link in the catalog, must not get the
    'functionalities' warning — matches compute_gaps.py's EMPTY_FEATURE gap, which unions
    a Feature's forward `functionalities` list with the catalog back-link
    (feature_func_counts), the same treatment ORPHAN_FEATURE already gets for user_stories."""
    feat = {
        "entity_type": "Feature",
        "id": "FEAT-5",
        "name": "Back-linked Surface",
        "surface_type": "UI",
        "purpose": "A surface whose Functionality is linked only from the Functionality side",
        "user_stories": ["US-1"],
        "functionalities": [],
        "owners": ["Team"],
    }
    catalog = {
        "catalog": {
            "user_stories": [],
            "features": [],
            "functionalities": [{"id": "FUNC-1", "parent_feature": "FEAT-5"}],
        },
    }
    issues = validate(feat, catalog)
    func_issues = [i for i in issues if i["field"] == "functionalities"]
    assert not func_issues, f"did not expect a functionalities warning for a catalog back-linked Feature, got: {func_issues}"
    print("✓ A Feature linked only via a catalog Functionality's parent_feature back-link is not flagged")


def test_functionality_warning_still_reported_without_back_link():
    """The catalog back-link suppression must not swallow a genuine gap — a Feature with
    an empty `functionalities` list and no matching catalog back-link still warns."""
    feat = {
        "entity_type": "Feature",
        "id": "FEAT-6",
        "name": "Genuinely Empty Surface",
        "surface_type": "UI",
        "purpose": "A surface with no Functionalities anywhere in the catalog",
        "user_stories": ["US-1"],
        "functionalities": [],
        "owners": ["Team"],
    }
    catalog = {
        "catalog": {
            "user_stories": [],
            "features": [],
            "functionalities": [{"id": "FUNC-1", "parent_feature": "FEAT-OTHER"}],
        },
    }
    issues = validate(feat, catalog)
    func_issues = [i for i in issues if i["field"] == "functionalities"]
    assert func_issues, f"expected a functionalities warning when no catalog back-link matches, got: {issues}"
    print("✓ A Feature with no Functionalities and no matching catalog back-link is still flagged")


def test_profile_missing_pyyaml_hard_fails():
    """Missing pyyaml must hard-fail with a clear message, not silently fall back to
    unrestricted canonical validation as if --profile had been omitted. Regression: a
    prior version caught ImportError in the same except clause as 'profile file not
    found' and returned None with just a stderr warning, so a profile narrowing
    ac_states would be silently ignored in any environment without pyyaml installed."""
    original = sys.modules.get("yaml", "__absent__")
    sys.modules["yaml"] = None  # forces `import yaml` to raise ImportError
    try:
        try:
            load_ac_states_from_profile("irrelevant-path.yaml")
        except SystemExit as exc:
            assert exc.code == 1, f"expected exit code 1, got: {exc.code}"
        else:
            raise AssertionError(
                "expected load_ac_states_from_profile to exit(1) when pyyaml is unavailable"
            )
    finally:
        if original == "__absent__":
            del sys.modules["yaml"]
        else:
            sys.modules["yaml"] = original
    print("✓ Missing pyyaml hard-fails instead of silently falling back to unrestricted validation")


def _run_validate_entity(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(VALIDATE_ENTITY_PY), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def test_profile_ac_states_subset_accepted():
    """A profile's ac_states that is a subset of the canonical set narrows validation —
    an AC state inside that narrower subset validates clean, and a state that is still
    canonical but excluded by the profile must be flagged AND must actually block:
    `valid: false` and a nonzero exit code, not just an advisory issue entry. Regression
    for a bug where the excluded-state check was a warning, not an error, so it produced
    a state issue but still returned exit code 0 / valid: true — silently failing to
    enforce the configured vocabulary (PR #40 review 5234392828)."""
    def make_us(state: str) -> dict:
        return {
            "entity_type": "User Story",
            "id": "US-1",
            "name": "Place an order",
            "status": "active",
            "features": ["FEAT-1"],
            "acceptance_criteria": [
                {"id": "AC:US-1-01", "description": "Order fails when payment is invalid", "state": state},
            ],
        }

    with tempfile.TemporaryDirectory() as tmp:
        profile_path = Path(tmp) / ".project-profile.yaml"
        profile_path.write_text("ac_states: [planned, active]\n", encoding="utf-8")

        in_subset_path = Path(tmp) / "entity-in-subset.json"
        in_subset_path.write_text(json.dumps(make_us("active")), encoding="utf-8")
        result = _run_validate_entity(str(in_subset_path), "--profile", str(profile_path), "--json")
        assert result.returncode == 0, result.stderr
        payload = json.loads(result.stdout)
        assert payload["valid"], payload
        state_issues = [i for i in payload["issues"] if i["field"].endswith(".state")]
        assert not state_issues, f"did not expect a state issue for 'active' inside the narrowed profile, got: {state_issues}"

        excluded_path = Path(tmp) / "entity-excluded.json"
        excluded_path.write_text(json.dumps(make_us("in_review")), encoding="utf-8")
        result = _run_validate_entity(str(excluded_path), "--profile", str(profile_path), "--json")
        payload = json.loads(result.stdout)
        state_issues = [i for i in payload["issues"] if i["field"].endswith(".state")]
        assert state_issues, f"expected a state issue for 'in_review' excluded by the narrowed profile, got: {payload}"
        assert not payload["valid"], (
            f"a profile-excluded AC state must make the entity invalid, got valid=True: {payload}"
        )
        assert result.returncode == 1, (
            f"a profile-excluded AC state must exit nonzero, got {result.returncode}: {payload}"
        )
        assert state_issues[0]["severity"] == "error", (
            f"a profile-excluded AC state must be an error, not a warning, got: {state_issues}"
        )

    print("✓ --profile ac_states that is a canonical subset narrows validation as expected, and actually blocks")


def test_profile_narrows_entity_status_too():
    """--profile must narrow the authored entity `status` field (User Story / Functionality),
    not just AC `state` — both are the same canonical vocabulary (living-doc-bdd-schemas.md).
    Regression for a bug where --profile reassigned only VALID_AC_STATUSES, so a profile with
    ac_states: [planned, active] still accepted an entity with status: in_review."""

    def make_us(status: str) -> dict:
        return {
            "entity_type": "User Story",
            "id": "US-1",
            "name": "Place an order",
            "status": status,
            "features": ["FEAT-1"],
            "acceptance_criteria": [
                {"id": "AC:US-1-01", "description": "Order fails when payment is invalid", "state": "active"},
            ],
        }

    with tempfile.TemporaryDirectory() as tmp:
        profile_path = Path(tmp) / ".project-profile.yaml"
        profile_path.write_text("ac_states: [planned, active]\n", encoding="utf-8")

        in_subset_path = Path(tmp) / "entity-in-subset.json"
        in_subset_path.write_text(json.dumps(make_us("active")), encoding="utf-8")
        result = _run_validate_entity(str(in_subset_path), "--profile", str(profile_path), "--json")
        assert result.returncode == 0, result.stderr
        payload = json.loads(result.stdout)
        status_issues = [i for i in payload["issues"] if i["field"] == "status"]
        assert not status_issues, f"did not expect a status issue for 'active' inside the narrowed profile, got: {status_issues}"

        excluded_path = Path(tmp) / "entity-excluded.json"
        excluded_path.write_text(json.dumps(make_us("in_review")), encoding="utf-8")
        result = _run_validate_entity(str(excluded_path), "--profile", str(profile_path), "--json")
        payload = json.loads(result.stdout)
        status_issues = [i for i in payload["issues"] if i["field"] == "status"]
        assert status_issues, f"expected a status issue for 'in_review' excluded by the narrowed profile, got: {payload}"

    print("✓ --profile ac_states narrows the entity 'status' field, not just AC 'state'")


def test_profile_ac_states_outside_canon_rejected():
    """A profile's ac_states containing a value outside the canonical four states must be
    rejected up front, not silently substituted for the canonical set — otherwise an AC in
    a made-up state (e.g. 'done') would validate successfully."""
    with tempfile.TemporaryDirectory() as tmp:
        entity_path = Path(tmp) / "entity.json"
        entity_path.write_text(json.dumps({"entity_type": "User Story"}), encoding="utf-8")
        profile_path = Path(tmp) / ".project-profile.yaml"
        profile_path.write_text("ac_states: [done]\n", encoding="utf-8")
        result = _run_validate_entity(str(entity_path), "--profile", str(profile_path))
    assert result.returncode == 1, result.stdout
    assert "not a subset of the canonical" in result.stderr, result.stderr
    print("✓ --profile ac_states outside the canonical set is rejected instead of applied")


def test_profile_ac_states_empty_list_rejected():
    """A profile's `ac_states: []` is schema-invalid (minItems: 1) — it must be rejected
    up front, not treated the same as an omitted field. Regression for a bug where
    load_ac_states_from_profile() returned None for both cases, so --profile silently
    fell back to the canonical defaults instead of enforcing the configured vocabulary."""
    with tempfile.TemporaryDirectory() as tmp:
        entity_path = Path(tmp) / "entity.json"
        entity_path.write_text(json.dumps({"entity_type": "User Story"}), encoding="utf-8")
        profile_path = Path(tmp) / ".project-profile.yaml"
        profile_path.write_text("ac_states: []\n", encoding="utf-8")
        result = _run_validate_entity(str(entity_path), "--profile", str(profile_path))
    assert result.returncode == 1, result.stdout
    assert "invalid `ac_states`" in result.stderr, result.stderr
    print("✓ --profile ac_states: [] is rejected instead of silently falling back to canonical defaults")


def test_profile_ac_states_wrong_type_rejected():
    """A profile's `ac_states` that isn't an array (e.g. a string) is schema-invalid —
    it must be rejected up front rather than silently ignored like an omitted field."""
    with tempfile.TemporaryDirectory() as tmp:
        entity_path = Path(tmp) / "entity.json"
        entity_path.write_text(json.dumps({"entity_type": "User Story"}), encoding="utf-8")
        profile_path = Path(tmp) / ".project-profile.yaml"
        profile_path.write_text("ac_states: active\n", encoding="utf-8")
        result = _run_validate_entity(str(entity_path), "--profile", str(profile_path))
    assert result.returncode == 1, result.stdout
    assert "invalid `ac_states`" in result.stderr, result.stderr
    print("✓ --profile ac_states of the wrong type is rejected instead of silently applied")


def test_profile_ac_states_non_string_item_rejected():
    """A profile's `ac_states` list containing a non-string item (e.g. a YAML mapping) is
    schema-invalid — it must be rejected up front with a diagnostic, not reach `set(states)`
    and crash with an unhandled TypeError on the unhashable item."""
    with tempfile.TemporaryDirectory() as tmp:
        entity_path = Path(tmp) / "entity.json"
        entity_path.write_text(json.dumps({"entity_type": "User Story"}), encoding="utf-8")
        profile_path = Path(tmp) / ".project-profile.yaml"
        profile_path.write_text("ac_states: [{foo: bar}, active]\n", encoding="utf-8")
        result = _run_validate_entity(str(entity_path), "--profile", str(profile_path))
    assert result.returncode == 1, result.stdout
    assert "invalid `ac_states`" in result.stderr, result.stderr
    assert "Traceback" not in result.stderr, result.stderr
    print("✓ --profile ac_states with a non-string item is rejected instead of crashing")


def test_profile_ac_states_duplicate_rejected():
    """A profile's `ac_states` list containing a duplicate value is schema-invalid — it must
    be rejected up front through the CLI, not just through the separate JSON Schema check, so
    a regression in load_ac_states_from_profile()'s own duplicate check would fail this test
    even if the schema-level test still passed."""
    with tempfile.TemporaryDirectory() as tmp:
        entity_path = Path(tmp) / "entity.json"
        entity_path.write_text(json.dumps({"entity_type": "User Story"}), encoding="utf-8")
        profile_path = Path(tmp) / ".project-profile.yaml"
        profile_path.write_text("ac_states: [active, active]\n", encoding="utf-8")
        result = _run_validate_entity(str(entity_path), "--profile", str(profile_path))
    assert result.returncode == 1, result.stdout
    assert "invalid `ac_states`" in result.stderr, result.stderr
    assert "duplicates" in result.stderr, result.stderr
    print("✓ --profile ac_states: [active, active] is rejected instead of silently applied")


def test_profile_scalar_root_rejected():
    """A profile whose YAML root is a scalar (e.g. `42`) is schema-invalid — it must be
    rejected up front with a diagnostic, not reach the `"ac_states" not in profile`
    membership test and crash with an unhandled TypeError."""
    with tempfile.TemporaryDirectory() as tmp:
        entity_path = Path(tmp) / "entity.json"
        entity_path.write_text(json.dumps({"entity_type": "User Story"}), encoding="utf-8")
        profile_path = Path(tmp) / ".project-profile.yaml"
        profile_path.write_text("42\n", encoding="utf-8")
        result = _run_validate_entity(str(entity_path), "--profile", str(profile_path))
    assert result.returncode == 1, result.stdout
    assert "must be a mapping" in result.stderr, result.stderr
    assert "Traceback" not in result.stderr, result.stderr
    print("✓ --profile with a scalar YAML root is rejected instead of crashing")


def test_profile_list_root_rejected():
    """A profile whose YAML root is a list is schema-invalid — it must be rejected up
    front, not silently treated as though `ac_states` were omitted (the `in` membership
    test on a list checks its elements, not mapping keys, so it never matches)."""
    with tempfile.TemporaryDirectory() as tmp:
        entity_path = Path(tmp) / "entity.json"
        entity_path.write_text(json.dumps({"entity_type": "User Story"}), encoding="utf-8")
        profile_path = Path(tmp) / ".project-profile.yaml"
        profile_path.write_text("- active\n- planned\n", encoding="utf-8")
        result = _run_validate_entity(str(entity_path), "--profile", str(profile_path))
    assert result.returncode == 1, result.stdout
    assert "must be a mapping" in result.stderr, result.stderr
    print("✓ --profile with a list YAML root is rejected instead of silently ignored")


def test_profile_missing_file_hard_fails():
    """A --profile path that doesn't exist must hard-fail with a clear diagnostic, not
    fall back to unrestricted canonical validation as though --profile were omitted.
    Regression for the bug the FileNotFoundError/ValueError except clause used to hide:
    it printed a warning and returned None, which main() cannot distinguish from a
    validly-omitted `ac_states`."""
    with tempfile.TemporaryDirectory() as tmp:
        entity_path = Path(tmp) / "entity.json"
        entity_path.write_text(json.dumps({"entity_type": "User Story"}), encoding="utf-8")
        missing_profile = Path(tmp) / "does-not-exist.yaml"
        result = _run_validate_entity(str(entity_path), "--profile", str(missing_profile))
    assert result.returncode == 1, result.stdout
    assert "could not load profile" in result.stderr, result.stderr
    assert "Traceback" not in result.stderr, result.stderr
    print("✓ A missing --profile file hard-fails instead of silently validating unrestricted")


def test_profile_directory_path_hard_fails():
    """A --profile path that points at a directory raises PermissionError on Windows
    (IsADirectoryError on POSIX) — neither is a FileNotFoundError, so the except clause
    must catch OSError broadly, not just FileNotFoundError, or this crashes with a raw
    traceback instead of a clean exit(1)."""
    with tempfile.TemporaryDirectory() as tmp:
        entity_path = Path(tmp) / "entity.json"
        entity_path.write_text(json.dumps({"entity_type": "User Story"}), encoding="utf-8")
        profile_dir = Path(tmp) / "a-directory.yaml"
        profile_dir.mkdir()
        result = _run_validate_entity(str(entity_path), "--profile", str(profile_dir))
    assert result.returncode == 1, result.stdout
    assert "could not load profile" in result.stderr, result.stderr
    assert "Traceback" not in result.stderr, result.stderr
    print("✓ A --profile path pointing at a directory hard-fails instead of crashing")


def test_profile_invalid_encoding_hard_fails():
    """A profile file that isn't valid UTF-8 raises UnicodeDecodeError (a ValueError
    subclass) while reading, before yaml.safe_load ever runs — must hard-fail cleanly,
    not crash with a raw traceback."""
    with tempfile.TemporaryDirectory() as tmp:
        entity_path = Path(tmp) / "entity.json"
        entity_path.write_text(json.dumps({"entity_type": "User Story"}), encoding="utf-8")
        profile_path = Path(tmp) / ".project-profile.yaml"
        profile_path.write_bytes(b"ac_states: [\xff\xfe]")
        result = _run_validate_entity(str(entity_path), "--profile", str(profile_path))
    assert result.returncode == 1, result.stdout
    assert "could not load profile" in result.stderr, result.stderr
    assert "Traceback" not in result.stderr, result.stderr
    print("✓ A non-UTF-8 --profile file hard-fails instead of crashing")


def test_profile_invalid_yaml_syntax_hard_fails():
    """A profile with a YAML syntax error (as opposed to a wrong-typed but syntactically
    valid root) must hit the yaml.YAMLError branch and hard-fail cleanly. This branch
    was added in commit 748b767 with no dedicated test, so a regression here would have
    gone unnoticed."""
    with tempfile.TemporaryDirectory() as tmp:
        entity_path = Path(tmp) / "entity.json"
        entity_path.write_text(json.dumps({"entity_type": "User Story"}), encoding="utf-8")
        profile_path = Path(tmp) / ".project-profile.yaml"
        profile_path.write_text("ac_states: [planned\n  active\n", encoding="utf-8")
        result = _run_validate_entity(str(entity_path), "--profile", str(profile_path))
    assert result.returncode == 1, result.stdout
    assert "invalid YAML" in result.stderr, result.stderr
    assert "Traceback" not in result.stderr, result.stderr
    print("✓ A profile with a YAML syntax error hard-fails instead of crashing")


def test_profile_empty_file_treated_as_omitted():
    """A genuinely empty profile file (yaml.safe_load returns None) is not malformed —
    it must be treated the same as an omitted `ac_states`, i.e. unrestricted canonical
    validation, not rejected as a non-mapping root."""
    with tempfile.TemporaryDirectory() as tmp:
        entity_path = Path(tmp) / "entity.json"
        entity_path.write_text(
            json.dumps({
                "entity_type": "User Story",
                "id": "US-1",
                "name": "Place an order",
                "status": "in_review",
                "features": ["FEAT-1"],
                "acceptance_criteria": [
                    {"id": "AC:US-1-01", "description": "Order fails when payment is invalid", "state": "in_review"},
                ],
            }),
            encoding="utf-8",
        )
        profile_path = Path(tmp) / ".project-profile.yaml"
        profile_path.write_text("", encoding="utf-8")
        result = _run_validate_entity(str(entity_path), "--profile", str(profile_path), "--json")
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["valid"], payload
    print("✓ An empty --profile file is treated as an omitted ac_states, not a malformed root")


def test_profile_falsey_non_mapping_roots_rejected():
    """A profile YAML root that is falsey but not a mapping (false, 0, an empty string,
    an empty list) must still be rejected as malformed. Regression for the bug in
    `yaml.safe_load(f) or {}`: any falsey root — not just None — was silently coerced
    into an empty dict, bypassing the 'root must be a mapping' check entirely. An empty
    list is the sharpest case: `test_profile_list_root_rejected` above only covers a
    *non-empty* list, which is truthy and was never affected by the `or {}` bug."""
    for content in ["false\n", "0\n", '""\n', "[]\n"]:
        with tempfile.TemporaryDirectory() as tmp:
            entity_path = Path(tmp) / "entity.json"
            entity_path.write_text(json.dumps({"entity_type": "User Story"}), encoding="utf-8")
            profile_path = Path(tmp) / ".project-profile.yaml"
            profile_path.write_text(content, encoding="utf-8")
            result = _run_validate_entity(str(entity_path), "--profile", str(profile_path))
        assert result.returncode == 1, f"content={content!r}, stdout={result.stdout}"
        assert "must be a mapping" in result.stderr, f"content={content!r}, stderr={result.stderr}"
    print("✓ Falsey non-mapping --profile roots (false/0/\"\"/[]) are rejected, not silently treated as {}")


def test_profile_null_ac_states_rejected():
    """`ac_states: null` is present but not a list — it must be rejected the same way
    as any other wrong-typed `ac_states`, not treated as 'omitted' since the key is
    present in the mapping."""
    with tempfile.TemporaryDirectory() as tmp:
        entity_path = Path(tmp) / "entity.json"
        entity_path.write_text(json.dumps({"entity_type": "User Story"}), encoding="utf-8")
        profile_path = Path(tmp) / ".project-profile.yaml"
        profile_path.write_text("ac_states: null\n", encoding="utf-8")
        result = _run_validate_entity(str(entity_path), "--profile", str(profile_path))
    assert result.returncode == 1, result.stdout
    assert "invalid `ac_states`" in result.stderr, result.stderr
    print("✓ --profile ac_states: null is rejected instead of treated as omitted")


# ── validate(): entity_type handling ────────────────────────────────────────────


def test_missing_entity_type_flagged():
    """An entity with neither 'entity_type' nor 'type' must be rejected up front with a
    single, specific error — and must short-circuit rather than fall through into field
    checks that assume a known entity shape."""
    issues = validate({"id": "US-1", "name": "Nothing"})
    assert len(issues) == 1, f"expected exactly one issue for a missing entity_type, got: {issues}"
    assert issues[0]["field"] == "entity_type" and issues[0]["severity"] == "error"
    print("✓ An entity with no entity_type/type is flagged and short-circuits further checks")


def test_unknown_entity_type_flagged():
    """An entity_type outside {User Story, Feature, Functionality} must be rejected —
    REQUIRED_FIELDS[entity_type] would otherwise KeyError deeper in validate()."""
    issues = validate({"entity_type": "Bug", "id": "BUG-1"})
    assert len(issues) == 1, f"expected exactly one issue for an unknown entity_type, got: {issues}"
    assert issues[0]["field"] == "entity_type"
    print("✓ An unrecognised entity_type is flagged instead of crashing")


def test_type_alias_accepted():
    """The 'type' key is accepted as an alias for 'entity_type' via
    `entity.get("entity_type") or entity.get("type")`."""
    us = {
        "type": "User Story",
        "id": "US-1",
        "name": "Place an order",
        "status": "active",
        "features": ["FEAT-1"],
        "acceptance_criteria": [
            {"id": "AC:US-1-01", "description": "Order fails when payment is invalid", "state": "active"},
        ],
    }
    issues = validate(us)
    assert not [i for i in issues if i["field"] == "entity_type"], issues
    print("✓ The 'type' key is accepted as an alias for 'entity_type'")


# ── validate(): required fields, deprecation, AC and per-type checks ───────────


def test_required_field_missing_flagged():
    """Each entity type's REQUIRED_FIELDS must actually be enforced when a field is
    entirely omitted (not just left empty) — mirrors the existing empty-string case."""
    us = {
        "entity_type": "User Story",
        "id": "US-1",
        "status": "active",
        "features": ["FEAT-1"],
        "acceptance_criteria": [{"id": "AC:US-1-01", "description": "fails on invalid input"}],
    }  # missing 'name'
    assert any(i["field"] == "name" and i["severity"] == "error" for i in validate(us)), validate(us)

    feat = {
        "entity_type": "Feature",
        "id": "FEAT-1",
        "name": "Checkout Page",
        "surface_type": "UI",
        "user_stories": ["US-1"],
        "functionalities": ["FUNC-1"],
        "owners": ["Team"],
    }  # missing 'purpose'
    assert any(i["field"] == "purpose" and i["severity"] == "error" for i in validate(feat)), validate(feat)

    func = {
        "entity_type": "Functionality",
        "id": "FUNC-1",
        "name": "Login Page - Validate Password",
        "parent_feature": "FEAT-1",
        "acceptance_criteria": [{"id": "AC:FUNC-1-01", "description": "fails on invalid input"}],
    }  # missing 'status'
    assert any(i["field"] == "status" and i["severity"] == "error" for i in validate(func)), validate(func)
    print("✓ A missing (not just empty) required field is flagged for every entity type")


def test_deprecated_user_story_missing_metadata_warns():
    """A User Story with status: deprecated but no deprecated_at/deprecation_reason must
    warn for both — deprecation metadata is required for the audit trail."""
    us = {
        "entity_type": "User Story",
        "id": "US-1",
        "name": "Place an order",
        "status": "deprecated",
        "features": ["FEAT-1"],
        "acceptance_criteria": [
            {"id": "AC:US-1-01", "description": "Order fails when payment is invalid", "state": "deprecated"},
        ],
    }
    dep_fields = {i["field"] for i in validate(us) if i["field"] in ("deprecated_at", "deprecation_reason")}
    assert dep_fields == {"deprecated_at", "deprecation_reason"}, f"expected both deprecation warnings, got: {dep_fields}"
    print("✓ A deprecated User Story missing deprecation metadata warns for both fields")


def test_deprecated_feature_via_markers_warns():
    """A Feature carries no 'status' field, so deprecation is detected from its markers
    directly (is_deprecated's else-branch). One marker present (deprecated_at) but not
    the other must still warn only for the missing one."""
    feat = {
        "entity_type": "Feature",
        "id": "FEAT-1",
        "name": "Legacy Reports",
        "surface_type": "UI",
        "purpose": "Generates legacy account reports, replaced by the new dashboard",
        "user_stories": ["US-1"],
        "functionalities": ["FUNC-1"],
        "owners": ["Team"],
        "deprecated_at": "2026-01-01",
    }
    issues = validate(feat)
    assert any(i["field"] == "deprecation_reason" for i in issues), issues
    assert not [i for i in issues if i["field"] == "deprecated_at"], issues
    print("✓ A Feature deprecated via markers (no status field) is still checked for deprecation metadata")


def test_ac_missing_id_and_description_flagged():
    """An AC missing 'id' or 'description' must each raise their own error —
    _validate_ac() checks them independently."""
    us = {
        "entity_type": "User Story",
        "id": "US-1",
        "name": "Place an order",
        "status": "active",
        "features": ["FEAT-1"],
        "acceptance_criteria": [{}],
    }
    fields = {i["field"] for i in validate(us)}
    assert "acceptance_criteria[0].id" in fields, fields
    assert "acceptance_criteria[0].description" in fields, fields
    print("✓ An AC missing 'id' and 'description' is flagged for both, independently")


def test_ac_unrecognized_state_errors():
    """An AC 'state' outside the canonical vocabulary must be an error, not a warning —
    it is the same vocabulary as the entity-level `status` field (already an error), and
    only an error actually blocks validation for a --profile-narrowed subset."""
    us = {
        "entity_type": "User Story",
        "id": "US-1",
        "name": "Place an order",
        "status": "active",
        "features": ["FEAT-1"],
        "acceptance_criteria": [
            {"id": "AC:US-1-01", "description": "Order fails when payment is invalid", "state": "done"},
        ],
    }
    issues = validate(us)
    state_issues = [i for i in issues if i["field"] == "acceptance_criteria[0].state"]
    assert state_issues, issues
    assert state_issues[0]["severity"] == "error", f"expected an error, got: {state_issues}"
    print("✓ An AC with an unrecognised state is flagged as an error")


def test_functionality_name_missing_separator_warns():
    """A Functionality name without the canonical ' - ' separator must warn — that
    pattern is how a Functionality stays traceable to its parent Feature by name."""
    func = {
        "entity_type": "Functionality",
        "id": "FUNC-1",
        "name": "ValidatePasswordStrength",
        "parent_feature": "FEAT-1",
        "status": "active",
        "acceptance_criteria": [
            {"id": "AC:FUNC-1-01", "description": "Fails when the password is too short", "state": "active"},
        ],
    }
    issues = validate(func)
    assert any(i["field"] == "name" for i in issues), issues
    print("✓ A Functionality name without the canonical ' - ' separator is flagged")


def test_functionality_parent_feature_bad_format_flagged():
    """A Functionality's parent_feature must look like a Feature ID (FEAT-nnn) — anything
    else is an error, since it breaks the Feature -> Functionality link."""
    func = {
        "entity_type": "Functionality",
        "id": "FUNC-1",
        "name": "Login Page - Validate Password Strength",
        "parent_feature": "US-1",
        "status": "active",
        "acceptance_criteria": [
            {"id": "AC:FUNC-1-01", "description": "Fails when the password is too short", "state": "active"},
        ],
    }
    issues = validate(func)
    assert any(i["field"] == "parent_feature" and i["severity"] == "error" for i in issues), issues
    print("✓ A Functionality parent_feature that isn't a FEAT- id is flagged as an error")


def test_user_story_no_features_warns():
    """A User Story with an empty 'features' list must warn — orphan User Stories are
    reported by gap-finder."""
    us = {
        "entity_type": "User Story",
        "id": "US-1",
        "name": "Place an order",
        "status": "active",
        "features": [],
        "acceptance_criteria": [
            {"id": "AC:US-1-01", "description": "Order fails when payment is invalid", "state": "active"},
        ],
    }
    issues = validate(us)
    assert any(i["field"] == "features" for i in issues), issues
    print("✓ A User Story with no linked Features is flagged")


def test_user_story_no_acceptance_criteria_errors():
    """A User Story with zero ACs must error — it cannot be validated or implemented
    without at least one."""
    us = {
        "entity_type": "User Story",
        "id": "US-1",
        "name": "Place an order",
        "status": "active",
        "features": ["FEAT-1"],
        "acceptance_criteria": [],
    }
    issues = validate(us)
    assert any(i["field"] == "acceptance_criteria" and i["severity"] == "error" for i in issues), issues
    print("✓ A User Story with no Acceptance Criteria is flagged as an error")


def test_user_story_missing_error_path_warns():
    """A User Story whose ACs are all happy-path (no error/failure keywords) must warn —
    at least one failure case is required."""
    us = {
        "entity_type": "User Story",
        "id": "US-1",
        "name": "Place an order",
        "status": "active",
        "features": ["FEAT-1"],
        "acceptance_criteria": [
            {"id": "AC:US-1-01", "description": "Order succeeds when payment is valid", "state": "active"},
        ],
    }
    issues = validate(us)
    assert any(i["field"] == "acceptance_criteria" and i["severity"] == "warning" for i in issues), issues
    print("✓ A User Story with only happy-path ACs is flagged for a missing error path")


# ── validate(): referential integrity against a --catalog ──────────────────────


def test_reference_missing_feature_for_user_story_warns():
    """A User Story referencing a Feature ID absent from the catalog must warn — this
    exercises _validate_references(), which no prior test invoked directly (the existing
    catalog-based tests all target the ORPHAN_FEATURE/functionalities back-link logic,
    not this function)."""
    us = {
        "entity_type": "User Story",
        "id": "US-1",
        "name": "Place an order",
        "status": "active",
        "features": ["FEAT-999"],
        "acceptance_criteria": [
            {"id": "AC:US-1-01", "description": "Order fails when payment is invalid", "state": "active"},
        ],
    }
    catalog = {"catalog": {"features": [], "user_stories": [], "functionalities": []}}
    issues = validate(us, catalog)
    assert any(
        i["field"] == "features" and "not found in catalog" in i["message"] for i in issues
    ), issues
    print("✓ A User Story referencing a Feature missing from the catalog is flagged")


def test_reference_missing_links_for_feature_warns():
    """A Feature referencing User Story / Functionality IDs absent from the catalog must
    warn for each, independently."""
    feat = {
        "entity_type": "Feature",
        "id": "FEAT-1",
        "name": "Checkout Page",
        "surface_type": "UI",
        "purpose": "Lets a customer complete a purchase",
        "user_stories": ["US-999"],
        "functionalities": ["FUNC-999"],
        "owners": ["Team"],
    }
    catalog = {"catalog": {"features": [], "user_stories": [], "functionalities": []}}
    issues = validate(feat, catalog)
    assert any(
        i["field"] == "user_stories" and "not found in catalog" in i["message"] for i in issues
    ), issues
    assert any(
        i["field"] == "functionalities" and "not found in catalog" in i["message"] for i in issues
    ), issues
    print("✓ A Feature referencing a User Story and Functionality missing from the catalog is flagged for both")


def test_reference_missing_parent_feature_for_functionality_warns():
    """A Functionality whose parent_feature isn't in the catalog must warn — distinct
    from the FEAT- format check, which only validates the ID's shape, not its existence."""
    func = {
        "entity_type": "Functionality",
        "id": "FUNC-1",
        "name": "Login Page - Validate Password Strength",
        "parent_feature": "FEAT-999",
        "status": "active",
        "acceptance_criteria": [
            {"id": "AC:FUNC-1-01", "description": "Fails when the password is too short", "state": "active"},
        ],
    }
    catalog = {"catalog": {"features": [], "user_stories": [], "functionalities": []}}
    issues = validate(func, catalog)
    assert any(
        i["field"] == "parent_feature" and "not found in catalog" in i["message"] for i in issues
    ), issues
    print("✓ A Functionality whose parent_feature is missing from the catalog is flagged")


# ── format_report() ─────────────────────────────────────────────────────────────


def test_format_report_no_issues_and_with_issues():
    """format_report() must produce a clean pass message with zero issues, and an
    accurate error/warning count with a line per issue when there are some."""
    clean = format_report("US-1", [])
    assert "US-1" in clean and "no issues found" in clean, clean

    issues = [
        {"severity": "error", "field": "name", "message": "Required field 'name' is missing or empty"},
        {"severity": "warning", "field": "owners", "message": "Feature has no owners"},
    ]
    report = format_report("FEAT-1", issues)
    assert "1 error(s)" in report and "1 warning(s)" in report, report
    assert "name" in report and "owners" in report, report
    print("✓ format_report() reports a clean pass and an accurate error/warning breakdown")


# ── main() / CLI-level error handling ───────────────────────────────────────────


def test_cli_entity_file_not_found():
    """A nonexistent entity path must fail cleanly through the CLI, not with a raw
    traceback."""
    with tempfile.TemporaryDirectory() as tmp:
        missing_path = Path(tmp) / "does-not-exist.json"
        result = _run_validate_entity(str(missing_path))
    assert result.returncode == 1, result.stdout
    assert "Error reading entity" in result.stderr, result.stderr
    assert "Traceback" not in result.stderr, result.stderr
    print("✓ A missing entity file fails cleanly through the CLI")


def test_cli_entity_invalid_json():
    """Malformed JSON in the entity file must fail cleanly, not with a raw traceback."""
    with tempfile.TemporaryDirectory() as tmp:
        entity_path = Path(tmp) / "entity.json"
        entity_path.write_text("{not valid json", encoding="utf-8")
        result = _run_validate_entity(str(entity_path))
    assert result.returncode == 1, result.stdout
    assert "Error reading entity" in result.stderr, result.stderr
    assert "Traceback" not in result.stderr, result.stderr
    print("✓ Malformed entity JSON fails cleanly through the CLI")


def test_cli_catalog_file_not_found():
    """A nonexistent --catalog path must fail cleanly, independent of the entity file
    being valid."""
    with tempfile.TemporaryDirectory() as tmp:
        entity_path = Path(tmp) / "entity.json"
        entity_path.write_text(json.dumps({"entity_type": "User Story"}), encoding="utf-8")
        missing_catalog = Path(tmp) / "does-not-exist.json"
        result = _run_validate_entity(str(entity_path), "--catalog", str(missing_catalog))
    assert result.returncode == 1, result.stdout
    assert "Error reading catalog" in result.stderr, result.stderr
    assert "Traceback" not in result.stderr, result.stderr
    print("✓ A missing catalog file fails cleanly through the CLI")


def test_cli_stdin_input():
    """Passing '-' as the entity argument must read the entity from stdin instead of
    treating '-' as a file path."""
    entity = {
        "entity_type": "User Story",
        "id": "US-1",
        "name": "Place an order",
        "status": "active",
        "features": ["FEAT-1"],
        "acceptance_criteria": [
            {"id": "AC:US-1-01", "description": "Order fails when payment is invalid", "state": "active"},
        ],
    }
    result = subprocess.run(
        [sys.executable, str(VALIDATE_ENTITY_PY), "-", "--json"],
        input=json.dumps(entity),
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["valid"], payload
    print("✓ '-' reads the entity from stdin")


if __name__ == "__main__":
    try:
        test_single_digit_entity_ids_accepted()
        test_slug_feature_id_rejected()
        test_canonical_ac_id_accepted()
        test_legacy_ac_id_format_rejected()
        test_feat_parent_ac_id_rejected()
        test_end_to_end_user_story_with_single_digit_id_validates_clean()
        test_end_to_end_slug_feature_id_flagged()
        test_feature_with_status_field_rejected()
        test_feature_surface_type_canonical_set_only()
        test_orphan_feature_reported_distinctly()
        test_orphan_feature_with_functionalities_still_reported()
        test_orphan_feature_suppressed_by_catalog_back_link()
        test_functionality_warning_suppressed_by_catalog_back_link()
        test_functionality_warning_still_reported_without_back_link()
        test_profile_missing_pyyaml_hard_fails()
        test_profile_ac_states_subset_accepted()
        test_profile_narrows_entity_status_too()
        test_profile_ac_states_outside_canon_rejected()
        test_profile_ac_states_empty_list_rejected()
        test_profile_ac_states_wrong_type_rejected()
        test_profile_ac_states_non_string_item_rejected()
        test_profile_ac_states_duplicate_rejected()
        test_profile_scalar_root_rejected()
        test_profile_list_root_rejected()
        test_profile_missing_file_hard_fails()
        test_profile_directory_path_hard_fails()
        test_profile_invalid_encoding_hard_fails()
        test_profile_invalid_yaml_syntax_hard_fails()
        test_profile_empty_file_treated_as_omitted()
        test_profile_falsey_non_mapping_roots_rejected()
        test_profile_null_ac_states_rejected()
        test_missing_entity_type_flagged()
        test_unknown_entity_type_flagged()
        test_type_alias_accepted()
        test_required_field_missing_flagged()
        test_deprecated_user_story_missing_metadata_warns()
        test_deprecated_feature_via_markers_warns()
        test_ac_missing_id_and_description_flagged()
        test_ac_unrecognized_state_errors()
        test_functionality_name_missing_separator_warns()
        test_functionality_parent_feature_bad_format_flagged()
        test_user_story_no_features_warns()
        test_user_story_no_acceptance_criteria_errors()
        test_user_story_missing_error_path_warns()
        test_reference_missing_feature_for_user_story_warns()
        test_reference_missing_links_for_feature_warns()
        test_reference_missing_parent_feature_for_functionality_warns()
        test_format_report_no_issues_and_with_issues()
        test_cli_entity_file_not_found()
        test_cli_entity_invalid_json()
        test_cli_catalog_file_not_found()
        test_cli_stdin_input()
        print("\n✓ All tests passed!")
    except AssertionError as e:
        print(f"✗ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
