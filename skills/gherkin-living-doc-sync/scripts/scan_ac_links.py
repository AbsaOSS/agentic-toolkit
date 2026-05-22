#!/usr/bin/env python3
"""
scan_ac_links.py — scan .feature files for missing or malformed AC link headers.

Usage:
    python scan_ac_links.py <features_dir>

For every Scenario: / Scenario Outline: line found in .feature files, checks that:
  - A '# AC: <id>' comment appears on the line immediately above it
  - The AC ID follows the canonical format: AC:<parent-id>-<nn>
    e.g. AC:US-001-01, AC:FEAT-003-02, AC:FUNC-001-03
  - No two scenarios in the same file reference the same AC ID (duplicate check)

Exit code: 0 if all checks pass, 1 if any issues are found.

Glossary reference: skills/references/living-doc-glossary.md
"""

import re
import sys
from pathlib import Path

# Matches: # AC: US-001-01 (v1.0.0 – Active) — description
# or simpler: # AC: US-001-01
AC_COMMENT = re.compile(r"^\s*#\s*AC:\s*(\S+)", re.IGNORECASE)
# Canonical AC ID: AC:<parent>-<nn> where parent is US-nnn, FEAT-nnn, or FUNC-nnn
AC_ID_FORMAT = re.compile(r"^AC:(US|FEAT|FUNC)-\d{3}-\d{2}$", re.IGNORECASE)
SCENARIO_LINE = re.compile(r"^\s*(Scenario:|Scenario Outline:)\s*(.+)", re.IGNORECASE)


def scan_file(path: Path) -> list[dict]:
    issues = []
    lines = path.read_text(encoding="utf-8").splitlines()
    seen: dict[str, list[int]] = {}

    for i, line in enumerate(lines):
        if not SCENARIO_LINE.match(line):
            continue

        lineno = i + 1
        scenario_title = SCENARIO_LINE.match(line).group(2).strip()
        prev = lines[i - 1].strip() if i > 0 else ""
        ac_match = AC_COMMENT.match(prev)

        if not ac_match:
            issues.append({
                "file": str(path),
                "line": lineno,
                "scenario": scenario_title,
                "issue": "missing_ac_link",
                "detail": "No '# AC: <id>' comment on the line immediately above this scenario.",
            })
            continue

        ac_ref = ac_match.group(1).rstrip(",;")

        if not AC_ID_FORMAT.match(ac_ref):
            issues.append({
                "file": str(path),
                "line": lineno,
                "scenario": scenario_title,
                "issue": "malformed_ac_id",
                "detail": (
                    f"'{ac_ref}' does not match AC:<parent>-<nn> format "
                    "(e.g. AC:US-001-01, AC:FEAT-003-02)."
                ),
            })
            continue

        seen.setdefault(ac_ref.upper(), []).append(lineno)

    for ac_id, lines_found in seen.items():
        if len(lines_found) > 1:
            issues.append({
                "file": str(path),
                "line": lines_found,
                "scenario": None,
                "issue": "duplicate_ac_link",
                "detail": (
                    f"AC '{ac_id}' is linked from {len(lines_found)} scenarios "
                    f"at lines {lines_found}. Each AC should map to at most one scenario."
                ),
            })

    return issues


def main(features_dir: str) -> None:
    root = Path(features_dir)
    if not root.exists():
        print(f"Error: directory not found: {features_dir}")
        sys.exit(1)

    feature_files = sorted(root.rglob("*.feature"))
    if not feature_files:
        print(f"No .feature files found under {features_dir}")
        return

    all_issues: list[dict] = []
    for f in feature_files:
        all_issues.extend(scan_file(f))

    if not all_issues:
        print(f"✅  All {len(feature_files)} feature file(s) pass AC link checks.")
        return

    by_type: dict[str, list] = {}
    for issue in all_issues:
        by_type.setdefault(issue["issue"], []).append(issue)

    print(f"Found {len(all_issues)} issue(s) in {len(feature_files)} feature file(s):\n")

    labels = {
        "missing_ac_link": "MISSING AC LINK",
        "malformed_ac_id": "MALFORMED AC ID",
        "duplicate_ac_link": "DUPLICATE AC LINK",
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
            print(f"    → {item['detail']}")
            print()

    sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python scan_ac_links.py <features_dir>")
        sys.exit(1)
    main(sys.argv[1])
