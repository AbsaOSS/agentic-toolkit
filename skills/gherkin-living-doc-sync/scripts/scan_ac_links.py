#!/usr/bin/env python3
"""
scan_ac_links.py — scan living-doc .feature files for missing or malformed @AC: traceability.

Usage:
    python scan_ac_links.py <features_dir> [--us-dir <rel>] [--func-dir <rel>]

Only scans files under the living-doc directories (default 'features/liv_doc_us/' and
'features/liv_doc_func/'; override with --us-dir/--func-dir to match the Project Profile
`feature_dirs`). Other feature files (smoke tests, regression suites, exploratory probes) are skipped.

For every Scenario: / Scenario Outline: line found in living-doc files, checks that:
  - At least one '@AC:<id>' Cucumber tag appears on a tag line immediately above it (error)
  - A matching '# AC:<id>' human-readable comment is also present (warning)
  - The AC ID follows the canonical format: AC:<parent-id>-<nn>
    e.g. AC:US-001-01, AC:US-1-01, AC:FUNC-001-01
  - No two scenarios in the same file reference the same AC ID (duplicate check)

Exit code: 0 if all checks pass, 1 if any errors are found (warnings do not fail).

Constraint: Parent IDs in @AC: tags must be numeric only (US-001, FUNC-042).
Slug-based Feature IDs (e.g., FEAT-checkout-page) are not permitted in AC tag references;
see living_doc_id.py for the corresponding catalog-level constraint.

Tag grammar and tag-line-walking are shared with coverage_report.py via
skills/shared/lib/ac_tag.py so the two tools cannot disagree on what a valid @AC: tag is.

Glossary reference: skills/shared/references/living-doc-glossary.md
"""

import re
import sys
from pathlib import Path

# Resolve the shared library path relative to this script
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "shared" / "lib"))

from ac_tag import TAG_LINE, get_tag_lines_above, match_ac_tag

# Matches a # AC: human-readable comment: # AC:US-1-01 or # AC:FUNC-001-01 (...)
AC_COMMENT_LINE = re.compile(r"^\s*#\s*AC:((?:US|FUNC)-\d+-\d{2})", re.IGNORECASE)
COMMENT_LINE = re.compile(r"^\s*#")
SCENARIO_LINE = re.compile(r"^\s*(Scenario:|Scenario Outline:)\s*(.+)", re.IGNORECASE)

# Living-doc path components — only files under these directories are scanned.
# Defaults match the reference project; override via --us-dir / --func-dir.
LIVING_DOC_PATHS = ("features/liv_doc_us/", "features/liv_doc_func/")


def is_living_doc_file(path: Path, living_doc_paths: tuple[str, ...] = LIVING_DOC_PATHS) -> bool:
    """Return True if the file is in a living-doc feature directory."""
    normalised = str(path).replace("\\", "/")
    return any(segment in normalised for segment in living_doc_paths)


def get_tags_above(lines: list[str], scenario_index: int) -> list[str]:
    """Return all Cucumber tag tokens from consecutive tag lines immediately above a scenario."""
    tags: list[str] = []
    for line in get_tag_lines_above(lines, scenario_index):
        tags.extend(re.findall(r"@\S+", line))
    return tags


def get_ac_comments_above(lines: list[str], scenario_index: int) -> set[str]:
    """Return AC IDs mentioned in # AC: comments in the tag/comment block above a scenario."""
    ac_ids: set[str] = set()
    i = scenario_index - 1
    while i >= 0 and (TAG_LINE.match(lines[i]) or COMMENT_LINE.match(lines[i])):
        m = AC_COMMENT_LINE.match(lines[i])
        if m:
            ac_ids.add(m.group(1).upper())
        i -= 1
    return ac_ids


def scan_file(path: Path) -> list[dict]:
    issues = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError as e:
        issues.append({
            "file": str(path),
            "line": 0,
            "scenario": None,
            "issue": "encoding_error",
            "severity": "error",
            "detail": f"File contains invalid UTF-8 encoding: {e}",
        })
        return issues
    seen: dict[str, list[int]] = {}

    for i, line in enumerate(lines):
        if not SCENARIO_LINE.match(line):
            continue

        lineno = i + 1
        scenario_title = SCENARIO_LINE.match(line).group(2).strip()
        tags_above = get_tags_above(lines, i)
        ac_tags = [t for t in tags_above if t.upper().startswith("@AC:")]

        if not ac_tags:
            issues.append({
                "file": str(path),
                "line": lineno,
                "scenario": scenario_title,
                "issue": "missing_ac_tag",
                "severity": "error",
                "detail": "No '@AC:<id>' tag on the tag line(s) immediately above this scenario.",
            })
            continue

        ac_comments = get_ac_comments_above(lines, i)

        for tag in ac_tags:
            # Extract AC ID and optional /param:value segments
            m = match_ac_tag(tag)
            if not m:
                issues.append({
                    "file": str(path),
                    "line": lineno,
                    "scenario": scenario_title,
                    "issue": "malformed_ac_id",
                    "severity": "error",
                    "detail": (
                        f"'{tag}' does not match @AC:<parent>-<nn>[/param:value] format "
                        "(e.g. @AC:US-1-01, @AC:US-001-01/aspect:username-input)."
                    ),
                })
                continue
            ac_id_raw = "AC:" + m.group(1)  # reconstruct full AC ID
            plain_id = m.group(1).upper()  # e.g. US-1-01
            # Include /param:value suffixes in duplicate tracking to allow multi-aspect tagging.
            # Scenarios with @AC:US-1-01/aspect:username-input and @AC:US-1-01/aspect:password-input
            # are distinct and should not be flagged as duplicates.
            full_ac_key = (ac_id_raw + (m.group(2) or "")).upper()
            seen.setdefault(full_ac_key, []).append(lineno)
            # Warn if the human-readable # AC: comment is missing for this tag
            if plain_id not in {c.upper() for c in ac_comments}:
                issues.append({
                    "file": str(path),
                    "line": lineno,
                    "scenario": scenario_title,
                    "issue": "missing_ac_comment",
                    "severity": "warning",
                    "detail": (
                        f"@AC:{plain_id} tag is present but no matching '# AC:{plain_id} ...' "
                        "human-readable comment was found above the scenario."
                    ),
                })

    for ac_id, lines_found in seen.items():
        if len(lines_found) > 1:
            issues.append({
                "file": str(path),
                "line": lines_found,
                "scenario": None,
                "issue": "duplicate_ac_link",
                "severity": "error",
                "detail": (
                    f"AC '{ac_id}' is linked from {len(lines_found)} scenarios "
                    f"at lines {lines_found}. Each AC should map to at most one scenario."
                ),
            })

    return issues


def main(
    features_dir: str,
    living_doc_paths: tuple[str, ...] = LIVING_DOC_PATHS,
    allow_empty: bool = False,
) -> None:
    root = Path(features_dir)
    if not root.exists():
        print(f"Error: directory not found: {features_dir}")
        sys.exit(1)

    all_files = sorted(root.rglob("*.feature"))
    feature_files = [f for f in all_files if is_living_doc_file(f, living_doc_paths)]
    skipped = len(all_files) - len(feature_files)

    if skipped:
        print(f"Skipped {skipped} non-living-doc feature file(s) (smoke, regression, exploratory).")

    if not feature_files:
        print(f"No living-doc .feature files found under {features_dir}")
        print(f"Expected files under {' or '.join(repr(p) for p in living_doc_paths)}")
        if allow_empty:
            print("--allow-empty set: treating this as pass (exit 0).")
            return
        print(
            "Exit code 1: zero feature files usually means a wrong --us-dir/--func-dir "
            "or a different repo layout, not an intentionally empty project. "
            "Pass --allow-empty to treat this as a pass instead."
        )
        sys.exit(1)

    all_issues: list[dict] = []
    for f in feature_files:
        all_issues.extend(scan_file(f))

    if not all_issues:
        print(f"\u2705  All {len(feature_files)} living-doc feature file(s) pass AC link checks.")
        return

    errors = [i for i in all_issues if i.get("severity") == "error"]
    warnings = [i for i in all_issues if i.get("severity") == "warning"]

    by_type: dict[str, list] = {}
    for issue in all_issues:
        by_type.setdefault(issue["issue"], []).append(issue)

    plural_e = "error" if len(errors) == 1 else "errors"
    plural_w = "warning" if len(warnings) == 1 else "warnings"
    print(f"Found {len(errors)} {plural_e} and {len(warnings)} {plural_w} in {len(feature_files)} living-doc feature file(s).")
    if errors:
        print(f"Exit code 1: {len(errors)} {plural_e} must be fixed.\n")
    else:
        print()

    labels = {
        "missing_ac_tag": "[ERROR] MISSING @AC: TAG",
        "malformed_ac_id": "[ERROR] MALFORMED AC ID",
        "duplicate_ac_link": "[ERROR] DUPLICATE AC LINK",
        "missing_ac_comment": "[WARN]  MISSING # AC: COMMENT",
    }

    for issue_type, items in sorted(by_type.items()):
        print(f"{'=' * 60}")
        print(f"  {labels.get(issue_type, issue_type)} ({len(items)})")
        print(f"{'=' * 60}")
        for item in items:
            loc = item["line"] if isinstance(item["line"], int) else item["line"][0]
            print(f"  {item['file']}:{loc}")
            if item.get("scenario"):
                print(f"    Scenario: {item['scenario']}")
            print(f"    {item['detail']}")
            print()

    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Scan living-doc .feature files for missing or malformed @AC: traceability."
    )
    parser.add_argument("features_dir", help="Root directory to scan recursively for .feature files.")
    parser.add_argument(
        "--us-dir",
        default="features/liv_doc_us/",
        help="Living-doc User Story directory fragment (Project Profile feature_dirs.user_story).",
    )
    parser.add_argument(
        "--func-dir",
        default="features/liv_doc_func/",
        help="Living-doc Functionality directory fragment (Project Profile feature_dirs.functionality).",
    )
    parser.add_argument(
        "--allow-empty",
        action="store_true",
        help="Exit 0 when zero living-doc feature files are found, instead of the default exit 1. "
        "Use only when the project intentionally has no living-doc feature files yet.",
    )
    args = parser.parse_args()

    def _norm(fragment: str) -> str:
        fragment = fragment.replace("\\", "/").strip("/")
        return f"{fragment}/"

    main(args.features_dir, (_norm(args.us_dir), _norm(args.func_dir)), args.allow_empty)
