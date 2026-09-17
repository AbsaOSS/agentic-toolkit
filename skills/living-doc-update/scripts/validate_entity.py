#!/usr/bin/env python3
"""
validate_entity.py — Living Doc Entity Validator

Validates a living doc entity JSON against the canonical schema from the glossary.
Checks required fields, ID formats, status values, AC structure, and (optionally)
referential integrity against the full catalog.

Usage:
    python validate_entity.py entity.json
    python validate_entity.py entity.json --catalog catalog.json
    echo '{...}' | python validate_entity.py -
    python validate_entity.py entity.json --json        # machine-readable output

Exits with code 0 if no errors (warnings are non-blocking).
Exits with code 1 if any errors exist.
"""

import argparse
import json
import re
import sys
from pathlib import Path

# Resolve the shared library path relative to this script
_lib_path = Path(__file__).parent.parent.parent / "shared" / "lib"
sys.path.insert(0, str(_lib_path))

try:
    from ac_tag import AC_ID_PATTERN
except ImportError:
    print(
        f"Error: shared library not found at {_lib_path} — this skill depends on skills/shared/.\n"
        "If you installed this skill standalone, also install the shared library skill:\n"
        "  npx skills add https://github.com/AbsaOSS/agentic-toolkit -g --skill shared\n"
        "(or use a full repo clone instead of a single-skill install).",
        file=sys.stderr,
    )
    sys.exit(1)

# ── Canonical constraints (from living-doc-glossary.md) ───────────────────────

VALID_SURFACE_TYPES = {"UI", "API"}
# Status/AC-state vocabulary — lowercase with underscores per the Project Profile `ac_states`.
# The same vocabulary backs both an authored entity `status` (User Story / Functionality) and
# an AC `state` (see living-doc-bdd-schemas.md) — they are not independent sets. CANONICAL_STATUSES
# never changes; VALID_STATUSES and VALID_AC_STATUSES may both be narrowed together at runtime
# with --profile to a subset of it (see main()) — a profile can restrict, never extend, the canon.
CANONICAL_STATUSES = {"planned", "in_review", "active", "deprecated"}
VALID_STATUSES = set(CANONICAL_STATUSES)
VALID_AC_STATUSES = set(CANONICAL_STATUSES)

# Numeric only, any digit count (US-1 and US-001 are both valid — matches
# living_doc_id.py's ENTITY_TYPE_MAP and scan_ac_links.py). Feature IDs are numeric
# only: living_doc_id.py's next_entity_id() explicitly rejects slug-based Feature IDs
# (e.g. FEAT-checkout-page) at auto-increment time, so a single-entity validator must
# reject them too rather than silently accepting what the ID generator would refuse.
ID_PATTERNS: dict[str, re.Pattern] = {
    "User Story": re.compile(r"^US-\d+$"),
    "Feature": re.compile(r"^FEAT-\d+$"),
    "Functionality": re.compile(r"^FUNC-\d+$"),
}

# AC_ID_PATTERN is imported from the shared lib (skills/shared/lib/ac_tag.py) so this
# validator, scan_ac_links.py, and coverage_report.py cannot disagree on the AC-ID
# grammar again — AC:<US|FUNC>-<n>-<nn>, two-digit suffix, no FEAT parent, no slugs.

REQUIRED_FIELDS: dict[str, list[str]] = {
    "User Story": ["id", "name", "status", "features", "acceptance_criteria"],
    "Feature": [
        "id", "name", "surface_type", "purpose",
        "user_stories", "functionalities", "owners",
    ],
    "Functionality": ["id", "name", "parent_feature", "status", "acceptance_criteria"],
}

# Entity types that carry an authored `status` field. A Feature has none — its state
# is derived from its Functionalities and must never be authored.
STATUSED_ENTITY_TYPES = {"User Story", "Functionality"}

DEPRECATION_FIELDS = ["deprecated_at", "deprecation_reason"]
VERB_PREFIX_RE = re.compile(
    r"^(process|handle|manage|do|perform|run|execute|validate|create|update|delete)\b",
    re.IGNORECASE,
)
ERROR_KEYWORDS_RE = re.compile(
    r"(error|fail|invalid|not|empty|exceed|deny|unauthori|reject|missing|timeout)",
    re.IGNORECASE,
)


# ── Validation logic ───────────────────────────────────────────────────────────

def load_ac_states_from_profile(profile_path: str) -> set[str] | None:
    """Read `ac_states` from a Project Profile YAML. Returns None if the field is
    omitted (valid — the schema allows omitting it) or the file is genuinely empty.
    Exits nonzero for anything that means the requested profile could not actually be
    consulted — missing/unreadable file, invalid YAML, a non-mapping root, or a
    present-but-schema-invalid `ac_states` — instead of silently falling back to the
    unrestricted canonical set as if `--profile` had never been passed. Also exits
    nonzero if pyyaml itself is unavailable, for the same reason."""
    try:
        import yaml  # noqa: PLC0415 — optional, only needed when --profile is passed
    except ImportError as exc:
        print(
            f"Error: --profile requires pyyaml, which is not installed: {exc}\n"
            "Install it with: pip install pyyaml",
            file=sys.stderr,
        )
        sys.exit(1)

    try:
        with open(profile_path, encoding="utf-8") as f:
            profile = yaml.safe_load(f)
    except (OSError, ValueError) as exc:
        print(f"Error: could not load profile '{profile_path}': {exc}", file=sys.stderr)
        sys.exit(1)
    except yaml.YAMLError as exc:
        print(
            f"Error: profile '{profile_path}' is malformed — invalid YAML: {exc}",
            file=sys.stderr,
        )
        sys.exit(1)
    if profile is None:
        return None
    if not isinstance(profile, dict):
        print(
            f"Error: profile '{profile_path}' is malformed — "
            f"root must be a mapping, got: {type(profile).__name__}",
            file=sys.stderr,
        )
        sys.exit(1)
    if "ac_states" not in profile:
        return None
    states = profile["ac_states"]
    if not isinstance(states, list) or not states:
        print(
            f"Error: profile '{profile_path}' has an invalid `ac_states` — "
            f"must be a non-empty array of strings, got: {states!r}",
            file=sys.stderr,
        )
        sys.exit(1)
    if not all(isinstance(s, str) for s in states):
        print(
            f"Error: profile '{profile_path}' has an invalid `ac_states` — "
            f"all items must be strings, got: {states!r}",
            file=sys.stderr,
        )
        sys.exit(1)
    if len(set(states)) != len(states):
        print(
            f"Error: profile '{profile_path}' has an invalid `ac_states` — "
            f"must not contain duplicates, got: {states!r}",
            file=sys.stderr,
        )
        sys.exit(1)
    return {str(s) for s in states}


def validate(entity: dict, catalog: dict | None = None) -> list[dict]:
    """
    Validate a single entity dict.
    Returns a list of issue dicts: {severity: 'error'|'warning', field: str, message: str}.
    """
    issues: list[dict] = []

    def error(field: str, message: str) -> None:
        issues.append({"severity": "error", "field": field, "message": message})

    def warning(field: str, message: str) -> None:
        issues.append({"severity": "warning", "field": field, "message": message})

    # ── entity_type ──────────────────────────────────────────────────────────
    entity_type: str | None = entity.get("entity_type") or entity.get("type")
    if not entity_type:
        error(
            "entity_type",
            "Missing 'entity_type'. Must be one of: User Story, Feature, Functionality",
        )
        return issues
    if entity_type not in REQUIRED_FIELDS:
        error(
            "entity_type",
            f"Unknown entity_type '{entity_type}'. "
            f"Must be one of: {list(REQUIRED_FIELDS)}",
        )
        return issues

    # ── Required fields ──────────────────────────────────────────────────────
    for field in REQUIRED_FIELDS[entity_type]:
        value = entity.get(field)
        if value is None or value == "":
            error(field, f"Required field '{field}' is missing or empty")

    # ── ID format ────────────────────────────────────────────────────────────
    entity_id: str = entity.get("id", "")
    id_pattern = ID_PATTERNS.get(entity_type)
    if entity_id and id_pattern and not id_pattern.match(entity_id):
        example = {"User Story": "US-001", "Feature": "FEAT-001", "Functionality": "FUNC-001"}
        error(
            "id",
            f"ID '{entity_id}' does not match expected format "
            f"(e.g. {example.get(entity_type, 'XXX-001')})",
        )

    # ── Status ───────────────────────────────────────────────────────────────
    status: str = entity.get("status", "")
    if entity_type not in STATUSED_ENTITY_TYPES:
        if "status" in entity:
            error(
                "status",
                f"{entity_type} must not carry a 'status' field — "
                "its state is derived from its Functionalities, never authored",
            )
    elif status and status not in VALID_STATUSES:
        error("status", f"Invalid status '{status}'. Must be one of: {VALID_STATUSES}")

    # ── Deprecation metadata ─────────────────────────────────────────────────
    # A Feature carries no `status`, so it is deprecated when it carries any
    # deprecation marker directly (deprecated_at / deprecation_reason / superseded_by).
    is_deprecated = (
        status == "deprecated"
        if entity_type in STATUSED_ENTITY_TYPES
        else bool(
            entity.get("deprecated_at") or entity.get("deprecation_reason") or entity.get("superseded_by")
        )
    )
    if is_deprecated:
        for dep_field in DEPRECATION_FIELDS:
            if not entity.get(dep_field):
                warning(
                    dep_field,
                    f"Deprecated entity is missing '{dep_field}' — "
                    "deprecation metadata is required for audit trail",
                )

    # ── Feature-specific ─────────────────────────────────────────────────────
    if entity_type == "Feature":
        surface_type: str = entity.get("surface_type", "")
        if surface_type and surface_type not in VALID_SURFACE_TYPES:
            error(
                "surface_type",
                f"Invalid surface_type '{surface_type}'. Must be one of: {VALID_SURFACE_TYPES}",
            )
        if isinstance(entity.get("owners"), list) and not entity["owners"]:
            warning("owners", "Feature has no owners — assign a team or individual")
        no_user_stories = isinstance(entity.get("user_stories"), list) and not entity["user_stories"]
        no_functionalities = isinstance(entity.get("functionalities"), list) and not entity["functionalities"]
        # gap-finder's ORPHAN_FEATURE gap fires on the absence of a linked User Story alone
        # (compute_gaps.py), regardless of Functionality links — so mirror that here rather
        # than requiring both lists to be empty. compute_gaps.py also honours the back-link
        # from a User Story's own `features` list (features_linked_from_us), not just the
        # Feature's forward `user_stories` — mirror that here too so a Feature linked only
        # from the User Story side isn't falsely flagged when --catalog is supplied. gap-finder's
        # EMPTY_FEATURE gap applies the same union-of-forward-and-back-link treatment to
        # Functionality.parent_feature (feature_func_counts) — mirror that here too.
        catalog_inner = catalog.get("catalog", catalog) if catalog is not None else None
        linked_from_catalog_us = False
        if no_user_stories and catalog_inner is not None:
            linked_from_catalog_us = any(
                entity_id in (us.get("features") or [])
                for us in catalog_inner.get("user_stories", [])
            )
        if no_user_stories and not linked_from_catalog_us:
            warning(
                "ORPHAN_FEATURE",
                "Feature has no linked User Stories — "
                "reported as an ORPHAN_FEATURE condition by living-doc-gap-finder",
            )
        linked_from_catalog_func = False
        if no_functionalities and catalog_inner is not None:
            linked_from_catalog_func = any(
                fn.get("parent_feature") == entity_id
                for fn in catalog_inner.get("functionalities", [])
            )
        if no_functionalities and not linked_from_catalog_func:
            warning(
                "functionalities",
                "Feature has no Functionalities — "
                "a Feature should own at least one Functionality",
            )
        purpose: str = entity.get("purpose", "")
        if purpose and len(purpose.split()) < 5:
            warning(
                "purpose",
                "Purpose statement is very short — "
                "describe the business value in 1-2 sentences",
            )
        name: str = entity.get("name", "")
        if name and VERB_PREFIX_RE.match(name):
            warning(
                "name",
                f"Feature name '{name}' looks like a verb phrase — "
                "Feature names should be nouns (e.g. 'Login Page', 'Orders API')",
            )

    # ── User Story-specific ──────────────────────────────────────────────────
    if entity_type == "User Story":
        if isinstance(entity.get("features"), list) and not entity["features"]:
            warning(
                "features",
                "User Story has no linked Features — "
                "orphan User Stories appear in gap-finder reports",
            )
        acs: list[dict] = entity.get("acceptance_criteria") or []
        if not acs:
            error("acceptance_criteria", "User Story must have at least one Acceptance Criterion")
        else:
            has_error_path = any(
                ERROR_KEYWORDS_RE.search(ac.get("description", "")) for ac in acs
            )
            if not has_error_path:
                warning(
                    "acceptance_criteria",
                    "No error-path or alternative-flow AC found — "
                    "add at least one failure case",
                )
            for i, ac in enumerate(acs):
                _validate_ac(ac, entity_id, i, error, warning)

    # ── Functionality-specific ───────────────────────────────────────────────
    if entity_type == "Functionality":
        name = entity.get("name", "")
        if name and " - " not in name:
            warning(
                "name",
                "Functionality name should follow the pattern "
                "'<Feature name> - <behavior phrase>' "
                "(e.g. 'Login Page - Validate Password Strength'). "
                "The canonical separator is a plain hyphen, never an en or em dash.",
            )
        parent: str = entity.get("parent_feature", "")
        if parent and not re.match(r"^FEAT-", parent):
            error(
                "parent_feature",
                f"parent_feature '{parent}' does not look like a valid Feature ID (expected FEAT-nnn)",
            )
        acs = entity.get("acceptance_criteria") or []
        if not acs:
            warning(
                "acceptance_criteria",
                "Functionality has no Acceptance Criteria — "
                "atomic behaviors should define at least one AC",
            )
        for i, ac in enumerate(acs):
            _validate_ac(ac, entity_id, i, error, warning)

    # ── Referential integrity ────────────────────────────────────────────────
    if catalog is not None:
        _validate_references(entity, entity_type, catalog, warning)

    return issues


def _validate_ac(
    ac: dict,
    parent_id: str,
    index: int,
    error_fn,
    warning_fn,
) -> None:
    """Validate a single Acceptance Criterion entry."""
    field_prefix = f"acceptance_criteria[{index}]"
    ac_id: str = ac.get("id", "")
    if not ac_id:
        error_fn(f"{field_prefix}.id", "AC is missing an 'id' field")
    elif not AC_ID_PATTERN.match(ac_id):
        warning_fn(
            f"{field_prefix}.id",
            f"AC ID '{ac_id}' does not match expected format "
            f"AC:{parent_id}-nn (e.g. AC:{parent_id}-01)",
        )
    if not ac.get("description"):
        error_fn(f"{field_prefix}.description", "AC is missing a 'description'")
    ac_status = ac.get("state", "")
    if ac_status and ac_status not in VALID_AC_STATUSES:
        # Error, not warning — an AC `state` and an entity `status` are the same
        # vocabulary (see the VALID_STATUSES/VALID_AC_STATUSES comment above) and must
        # be enforced identically. As a warning this was non-blocking regardless of
        # whether VALID_AC_STATUSES was the full canonical set or a --profile-narrowed
        # subset, so a profile-excluded AC state still produced exit code 0 / valid:
        # true — defeating the entire purpose of `--profile` (restrict, never extend).
        error_fn(
            f"{field_prefix}.state",
            f"Invalid AC state '{ac_status}'. "
            f"Expected one of: {sorted(VALID_AC_STATUSES)}",
        )


def _validate_references(
    entity: dict, entity_type: str, catalog: dict, warning_fn
) -> None:
    """Check that referenced IDs exist in the catalog (referential integrity)."""
    inner = catalog.get("catalog", catalog)
    feature_ids = {f["id"] for f in inner.get("features", [])}
    us_ids = {us["id"] for us in inner.get("user_stories", [])}
    func_ids = {fn["id"] for fn in inner.get("functionalities", [])}

    if entity_type == "User Story":
        for fid in entity.get("features", []):
            if fid not in feature_ids:
                warning_fn("features", f"Referenced Feature '{fid}' not found in catalog")

    if entity_type == "Feature":
        for us_id in entity.get("user_stories", []):
            if us_id not in us_ids:
                warning_fn("user_stories", f"Referenced User Story '{us_id}' not found in catalog")
        for fid in entity.get("functionalities", []):
            if fid not in func_ids:
                warning_fn("functionalities", f"Referenced Functionality '{fid}' not found in catalog")

    if entity_type == "Functionality":
        parent = entity.get("parent_feature")
        if parent and parent not in feature_ids:
            warning_fn(
                "parent_feature",
                f"Parent Feature '{parent}' not found in catalog",
            )


# ── Output formatting ──────────────────────────────────────────────────────────

def format_report(entity_id: str, issues: list[dict]) -> str:
    if not issues:
        return f"✓ {entity_id} — validation passed (no issues found)"
    error_count = sum(1 for i in issues if i["severity"] == "error")
    warning_count = sum(1 for i in issues if i["severity"] == "warning")
    lines = [
        f"Validation report for {entity_id}:",
        f"  {error_count} error(s)   {warning_count} warning(s)",
        "",
    ]
    for issue in issues:
        prefix = "✗" if issue["severity"] == "error" else "⚠"
        lines.append(f"  {prefix} [{issue['severity'].upper():7s}]  {issue['field']}")
        lines.append(f"             {issue['message']}")
    return "\n".join(lines)


# ── Entry point ────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate a living doc entity against the canonical schema."
    )
    parser.add_argument(
        "entity",
        help="Path to entity JSON file, or '-' to read from stdin",
    )
    parser.add_argument(
        "--catalog", "-c",
        help="Path to catalog JSON — enables referential integrity checks",
    )
    parser.add_argument(
        "--profile", "-p",
        help="Path to .project-profile.yaml — overrides the AC state vocabulary from `ac_states`",
    )
    parser.add_argument(
        "--json", "-j",
        action="store_true",
        help="Output validation results as JSON instead of human-readable text",
    )
    args = parser.parse_args()

    if args.profile:
        profile_states = load_ac_states_from_profile(args.profile)
        if profile_states:
            invalid_states = profile_states - CANONICAL_STATUSES
            if invalid_states:
                print(
                    f"Error: profile ac_states {sorted(invalid_states)} are not a subset of the "
                    f"canonical states {sorted(CANONICAL_STATUSES)}",
                    file=sys.stderr,
                )
                sys.exit(1)
            global VALID_STATUSES, VALID_AC_STATUSES
            VALID_STATUSES = profile_states
            VALID_AC_STATUSES = profile_states

    try:
        if args.entity == "-":
            entity = json.load(sys.stdin)
        else:
            with open(args.entity, encoding="utf-8") as f:
                entity = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        print(f"Error reading entity: {exc}", file=sys.stderr)
        sys.exit(1)

    catalog: dict | None = None
    if args.catalog:
        try:
            with open(args.catalog, encoding="utf-8") as f:
                catalog = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as exc:
            print(f"Error reading catalog: {exc}", file=sys.stderr)
            sys.exit(1)

    issues = validate(entity, catalog)
    entity_id: str = entity.get("id", "unknown")
    has_errors = any(i["severity"] == "error" for i in issues)

    if args.json:
        result = {
            "entity_id": entity_id,
            "valid": not has_errors,
            "error_count": sum(1 for i in issues if i["severity"] == "error"),
            "warning_count": sum(1 for i in issues if i["severity"] == "warning"),
            "issues": issues,
        }
        print(json.dumps(result, indent=2))
    else:
        print(format_report(entity_id, issues))

    sys.exit(1 if has_errors else 0)


if __name__ == "__main__":
    main()
