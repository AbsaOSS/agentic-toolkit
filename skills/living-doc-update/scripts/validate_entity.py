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

# ── Canonical constraints (from living-doc-glossary.md) ───────────────────────

VALID_STATUSES = {"planned", "active", "deprecated"}
VALID_SURFACE_TYPES = {"UI", "API"}
# AC state vocabulary — all lowercase with underscores (matches JSON vocabulary).
# Override at runtime with --profile to read the project's own ac_states list.
VALID_AC_STATUSES = {"planned", "in_review", "active", "deprecated"}

ID_PATTERNS: dict[str, re.Pattern] = {
    "User Story": re.compile(r"^US-\d{3,}$"),
    "Feature": re.compile(r"^FEAT-(\d{3,}|[a-z0-9]+(?:-[a-z0-9]+)*)$"),
    "Functionality": re.compile(r"^FUNC-\d{3,}$"),
}

AC_ID_PATTERN = re.compile(r"^AC:(US|FUNC)-\d+-\d+$")

REQUIRED_FIELDS: dict[str, list[str]] = {
    "User Story": ["id", "name", "status", "features", "acceptance_criteria"],
    "Feature": [
        "id", "name", "surface_type", "purpose", "status",
        "user_stories", "functionalities", "owners",
    ],
    "Functionality": ["id", "name", "parent_feature", "status", "acceptance_criteria"],
}

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
    """Read `ac_states` from a Project Profile YAML. Returns None if unavailable."""
    try:
        import yaml  # noqa: PLC0415 — optional, only needed when --profile is passed

        with open(profile_path) as f:
            profile = yaml.safe_load(f) or {}
    except (FileNotFoundError, ImportError, ValueError) as exc:
        print(f"Warning: could not load profile '{profile_path}': {exc}", file=sys.stderr)
        return None
    states = profile.get("ac_states")
    if isinstance(states, list) and states:
        return {str(s) for s in states}
    return None


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
    if status and status not in VALID_STATUSES:
        error("status", f"Invalid status '{status}'. Must be one of: {VALID_STATUSES}")

    # ── Deprecation metadata ─────────────────────────────────────────────────
    if status == "deprecated":
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
        if isinstance(entity.get("user_stories"), list) and not entity["user_stories"]:
            warning(
                "user_stories",
                "Feature has no linked User Stories — "
                "orphan Features appear in gap-finder reports",
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
        if name and " – " not in name and " - " not in name:
            warning(
                "name",
                "Functionality name should follow the pattern "
                "'<Feature name> – <behavior phrase>' "
                "(e.g. 'Login Page – Validate Password Strength')",
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
    ac_status = ac.get("status", "")
    if ac_status and ac_status not in VALID_AC_STATUSES:
        warning_fn(
            f"{field_prefix}.status",
            f"Unrecognised AC status '{ac_status}'. "
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
            global VALID_AC_STATUSES
            VALID_AC_STATUSES = profile_states

    try:
        if args.entity == "-":
            entity = json.load(sys.stdin)
        else:
            with open(args.entity) as f:
                entity = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        print(f"Error reading entity: {exc}", file=sys.stderr)
        sys.exit(1)

    catalog: dict | None = None
    if args.catalog:
        try:
            with open(args.catalog) as f:
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
