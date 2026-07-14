#!/usr/bin/env python3
"""
coverage_report.py — AC coverage report: which User Story ACs have linked Gherkin scenarios.

Usage:
    python coverage_report.py <living_doc_dir> <features_dir>

Scans <features_dir> recursively for '@AC:<id>' Cucumber traceability tags on tag lines
above Scenario lines. Loads User Story JSON files from <living_doc_dir> and produces a
coverage table showing which ACs are covered and which are gaps.

Expected User Story JSON structure:
    {
      "id": "US-001",
      "name": "Customer Login",
      "status": "active",
      "acceptance_criteria": [
        {
          "id": "AC:US-001-01",
          "text": "The login screen displays...",
          "state": "Active"
        }
      ]
    }

@AC: tag format (written by living-doc-scenario-creator):
    @AC:US-001-01
    Scenario: ...

Only ACs with state ACTIVE or IN_REVIEW are included in the coverage check.
AC state values are normalized to lowercase with underscores (e.g., "In Review" → "in_review").
Planned and Deprecated ACs are noted but not counted as gaps.

Project Profile schema vocabulary (Title-case with spaces):
  - "Active" → normalized to "active"
  - "In Review" → normalized to "in_review"
  - "Planned" → normalized to "planned"
  - "Deprecated" → normalized to "deprecated"

Code recognizes states: "active", "in_review" (all lowercase with underscores).

Exit code: 0 if all active/in-review ACs are covered, 1 if gaps exist.

Glossary reference: skills/shared/references/living-doc-glossary.md
"""

import json
import re
import sys
from pathlib import Path

# Matches an @AC: Cucumber tag with optional /param:value segments:
#   @AC:US-1-01  or  @AC:US-001-01/aspect:username-input
# Group 1 captures the AC ID only (params are ignored for coverage purposes).
# Both uppercase and lowercase @AC: prefixes are matched; output is always uppercase.
AC_TAG = re.compile(
    r"@(?:AC):((?:US|FEAT|FUNC)-(?:\d+|[a-z0-9]+(?:-[a-z0-9]+)*)-\d{2})(?:/[a-z][\w-]*:[^\s/@]+)*",
    re.IGNORECASE,
)
TAG_LINE = re.compile(r"^\s*@\S+")
SCENARIO_LINE = re.compile(r"^\s*(Scenario:|Scenario Outline:)\s*", re.IGNORECASE)

# AC states that count toward coverage: ACTIVE, IN_REVIEW (normalized to lowercase with underscores).
# Planned and Deprecated ACs are skipped (not counted as gaps).
# State normalization: "In Review" → "in_review", "Active" → "active", etc.
ACTIVE_STATES = {"active", "in_review"}


def canonicalize_numeric_id(parent_type: str, num_str: str) -> str:
    """
    Canonicalize a numeric parent ID to zero-padded 3-digit format.
    E.g., US-1-01 → US-001-01, US-10-01 → US-010-01, US-001-01 → US-001-01
    For non-numeric IDs (e.g., FEAT-checkout-01), return as-is.
    """
    if num_str.isdigit():
        return f"{parent_type}-{num_str.zfill(3)}"
    return f"{parent_type}-{num_str}"


def get_ac_tags_above(lines: list[str], scenario_index: int) -> list[str]:
    """Return all @AC: tag values (canonicalized) from consecutive tag lines immediately above a scenario."""
    ac_ids: list[str] = []
    i = scenario_index - 1
    while i >= 0 and TAG_LINE.match(lines[i]):
        for m in AC_TAG.finditer(lines[i]):
            raw_id = m.group(1).upper()
            canonical_id = _canonicalize_ac_id(raw_id)
            ac_ids.append(canonical_id)
        i -= 1
    return ac_ids


def _canonicalize_ac_id(ac_id: str) -> str:
    """
    Canonicalize AC ID by zero-padding numeric parent IDs.
    E.g., US-1-01 → US-001-01, FEAT-checkout-01 → FEAT-checkout-01 (no change)
    """
    # Match patterns like US-1-01, FEAT-checkout-01, FUNC-2-03
    m = re.match(r"^(US|FEAT|FUNC)-((?:\d+)|(?:[a-z0-9]+(?:-[a-z0-9]+)*))-(\d{2})$", ac_id, re.IGNORECASE)
    if m:
        parent_type = m.group(1).upper()
        parent_id = m.group(2)
        seq = m.group(3)
        canonical_parent = canonicalize_numeric_id(parent_type, parent_id)
        return f"{canonical_parent}-{seq}"
    return ac_id


def collect_covered_ac_ids(features_dir: Path) -> dict[str, list[str]]:
    """Return {ac_id_upper: [feature_filename, ...]} for every @AC: tag above a Scenario."""
    covered: dict[str, list[str]] = {}
    for feature_file in sorted(features_dir.rglob("*.feature")):
        lines = feature_file.read_text(encoding="utf-8").splitlines()
        for i, line in enumerate(lines):
            if not SCENARIO_LINE.match(line):
                continue
            for ac_id in get_ac_tags_above(lines, i):
                covered.setdefault(ac_id, []).append(feature_file.relative_to(features_dir).as_posix())
    return covered


def load_user_stories(living_doc_dir: Path) -> list[dict]:
    """Load all User Story JSON files from living_doc_dir or living_doc_dir/user-stories/."""
    search_dirs = [living_doc_dir / "user-stories", living_doc_dir]
    stories = []
    for d in search_dirs:
        if d.exists():
            for f in sorted(d.glob("*.json")):
                try:
                    data = json.loads(f.read_text(encoding="utf-8"))
                    # Accept a single US object or a list of US objects
                    if isinstance(data, list):
                        stories.extend(data)
                    elif isinstance(data, dict) and data.get("id", "").startswith("US-"):
                        stories.append(data)
                except (json.JSONDecodeError, OSError) as e:
                    print(f"Warning: could not parse {f}: {e}", file=sys.stderr)
            if stories:
                break  # stop at the first directory that yields results
    return stories


def normalise_ac_id(us_id: str, raw_id: str) -> str:
    """Normalise and canonicalize AC IDs that may be stored as '01' or 'US-001-01' or 'US-1-01' or 'FEAT-checkout-01'."""
    raw = str(raw_id).strip()
    # Strip 'AC:' prefix if present (case-insensitive); catalog fixtures may store with prefix
    if raw.startswith("AC:") or raw.startswith("ac:"):
        raw = raw[3:]
    raw = raw.upper()
    
    # Full AC ID format: canonicalize it
    if re.match(r"^(US|FEAT|FUNC)-(?:\d+|[a-z0-9]+(?:-[a-z0-9]+)*)-\d{2}$", raw, re.IGNORECASE):
        return _canonicalize_ac_id(raw)
    
    # Stored as just the suffix: '01' → 'US-001-01' (with parent ID canonicalized)
    if re.match(r"^\d{2}$", raw):
        # Extract parent type and ID from us_id, then canonicalize the numeric part
        m = re.match(r"^(US|FEAT|FUNC)-(.+)$", us_id, re.IGNORECASE)
        if m:
            parent_type = m.group(1).upper()
            parent_id = m.group(2)
            canonical_parent = canonicalize_numeric_id(parent_type, parent_id)
            return f"{canonical_parent}-{raw}"
        else:
            # us_id doesn't have the expected format, just use it as-is
            return f"{us_id.upper()}-{raw}"
    
    return raw


def main(living_doc_dir: str, features_dir: str) -> None:
    ld = Path(living_doc_dir)
    fd = Path(features_dir)

    for p, label in [(ld, "living_doc_dir"), (fd, "features_dir")]:
        if not p.exists():
            print(f"Error: {label} not found: {p}")
            sys.exit(1)

    covered = collect_covered_ac_ids(fd)
    stories = load_user_stories(ld)

    if not stories:
        print(f"No User Story JSON files found under {living_doc_dir}")
        sys.exit(1)

    total_active = 0
    total_covered = 0
    total_gaps = 0

    for us in sorted(stories, key=lambda s: s.get("id", "")):
        us_id = us.get("id", "?")
        title = us.get("name") or us.get("title", "?")
        us_status = us.get("status", "active").lower()
        acs = us.get("acceptance_criteria", [])

        if not acs:
            continue

        print(f"\n{'─' * 60}")
        print(f"  {us_id} — {title}  [{us_status}]")
        print(f"{'─' * 60}")

        for ac in acs:
            raw_id = ac.get("id", "?")
            ac_text = (ac.get("text") or ac.get("description", "?"))[:70]
            # Normalize AC state: convert to lowercase and replace spaces with underscores
            # (e.g., "In Review" → "in_review")
            ac_state = ac.get("state", "Active").lower().replace(" ", "_")

            ac_id = normalise_ac_id(us_id, raw_id)

            if ac_state not in ACTIVE_STATES:
                print(f"  ⏭  {ac_id}  [{ac_state}]  — {ac_text}")
                continue

            total_active += 1
            files = covered.get(ac_id, [])

            if files:
                total_covered += 1
                short = ", ".join(files[:3])
                suffix = f" (+{len(files) - 3} more)" if len(files) > 3 else ""
                print(f"  ✅ {ac_id}  [{ac_state}]  — {ac_text}")
                print(f"       ↳ covered by: {short}{suffix}")
            else:
                total_gaps += 1
                print(f"  ❌ {ac_id}  [{ac_state}]  — {ac_text}")
                print(f"       ↳ NOT COVERED — add to scenario generation queue")

    pct = (total_covered * 100 // total_active) if total_active else 0

    print(f"\n{'=' * 60}")
    print(f"  COVERAGE SUMMARY")
    print(f"{'=' * 60}")
    print(f"  ACTIVE / IN_REVIEW ACs : {total_active}")
    print(f"  Covered by scenarios                : {total_covered}  ({pct}%)")
    print(f"  Gaps (no scenario)                  : {total_gaps}")

    sys.exit(0 if total_gaps == 0 else 1)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python coverage_report.py <living_doc_dir> <features_dir>")
        sys.exit(1)
    main(sys.argv[1], sys.argv[2])
