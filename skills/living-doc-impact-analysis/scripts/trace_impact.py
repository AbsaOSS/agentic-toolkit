#!/usr/bin/env python3
"""
trace_impact.py — Living Doc Impact Tracer

Given a list of changed files (or a unified diff) and a catalog JSON that includes a
feature_registry, traces which Features, Functionalities, and User Stories are affected
and at what impact level. The model uses the output to produce the narrative impact map
rather than performing the entity traversal through reasoning.

Usage:
    python trace_impact.py --files src/payments/PromoService.java --catalog catalog.json
    python trace_impact.py --diff changes.diff --catalog catalog.json
    python trace_impact.py --files src/auth/LoginController.java --catalog catalog.json --summary
    python trace_impact.py --files src/payments/PromoService.java --catalog catalog.json \
                           --output impact.json

The catalog JSON must include a "feature_registry" section:
  {
    "feature_registry": [
      {
        "feature_id": "FEAT-001",
        "paths": ["src/auth/**", "src/security/login*"]
      }
    ],
    "catalog": { ... },
    "known_test_links": { ... }
  }

Path patterns in feature_registry use Unix shell-style wildcards (fnmatch).
"""

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from fnmatch import fnmatch
from pathlib import Path


# ── File classification ────────────────────────────────────────────────────────

_DOMAIN_PATTERNS = [
    r".*[Ss]ervice\.(java|py|ts|scala)$",
    r".*[Rr]epository\.(java|py|ts|scala)$",
    r".*[Dd]omain.*\.(java|py|ts|scala)$",
    r".*[Mm]odel\.(java|py|ts|scala)$",
    r".*[Uu]se[Cc]ase\.(java|py|ts|scala)$",
    r".*[Hh]andler\.(java|py|ts|scala)$",
    r".*[Pp]rocessor\.(java|py|ts|scala)$",
]
_API_PATTERNS = [
    r".*[Cc]ontroller\.(java|ts|scala)$",
    r".*[Rr]outer?\.(java|py|ts|scala)$",
    r".*(openapi|swagger).*\.(yaml|yml|json)$",
    r".*[Ee]ndpoint\.(java|py|ts|scala)$",
    r".*[Rr]oute\.(java|py|ts|scala)$",
    r".*[Rr]esource\.(java|ts|scala)$",
]
_EVENT_PATTERNS = [
    r".*\.(avsc|proto)$",
    r".*[Ss]chema\.(json)$",
    r".*[Ee]vent.*\.(java|py|ts|scala)$",
]
_UI_PATTERNS = [
    r".*\.(tsx|jsx)$",
    r".*[Cc]omponent\.(ts|html)$",
    r".*[Pp]age\.(ts|html)$",
    r".*[Ff]orm\.(ts|html)$",
]
_CONFIG_PATTERNS = [
    r".*(application|bootstrap)\.(yaml|yml|properties)$",
    r".*[Dd]ocker.*",
    r".*\.(tf|hcl)$",
    r".*(build|Build)\.(gradle|maven|sbt)$",
    r".*[Cc]onfig\.(java|py|ts|yaml|yml|json)$",
]
# Word-boundary test/mock detection. A plain substring search on "test"/"spec" would
# misclassify real domain code whose name merely contains the letters (latestOffers,
# Inspector, attestation) as test_or_mock. Instead, split the path into path-segment
# and camelCase/snake_case tokens and require a *whole* token to match one of these
# keywords (e.g. "Test" in OrderServiceTest.java, "tests" as a directory segment).
_TEST_KEYWORDS = frozenset({
    "test", "tests", "spec", "specs", "mock", "mocks",
    "fixture", "fixtures", "stub", "stubs",
})
_CAMEL_TOKEN = re.compile(r"[A-Z]+(?![a-z])|[A-Z]?[a-z0-9]+|[A-Z]+")


def _path_tokens(path: str) -> list[str]:
    """Split a path into path-segment, punctuation, and camelCase-boundary tokens."""
    tokens: list[str] = []
    for segment in re.split(r"[\\/]", path):
        for chunk in re.split(r"[^A-Za-z0-9]+", segment):
            if chunk:
                tokens.extend(_CAMEL_TOKEN.findall(chunk))
    return tokens


def is_test_or_mock_path(path: str) -> bool:
    return any(tok.lower() in _TEST_KEYWORDS for tok in _path_tokens(path))

# Canonical AC-ID grammar (skills/shared/references/living-doc-glossary.md):
# AC:<PARENT>-<nn>, where <PARENT> is US-<n> or FUNC-<nnn>. Captures the parent ID.
_AC_ID_PATTERN = re.compile(r"^AC:(US-\d+|FUNC-\d+)-\d{2}$")


def classify_file(path: str) -> str:
    """Return a surface category for the given file path."""
    if is_test_or_mock_path(path):
        return "test_or_mock"
    name = Path(path).name
    for pattern in _API_PATTERNS:
        if re.match(pattern, name) or re.match(pattern, path):
            return "api_contract"
    for pattern in _EVENT_PATTERNS:
        if re.match(pattern, name) or re.match(pattern, path):
            return "event_contract"
    for pattern in _UI_PATTERNS:
        if re.match(pattern, name) or re.match(pattern, path):
            return "ui_component"
    for pattern in _CONFIG_PATTERNS:
        if re.match(pattern, name) or re.match(pattern, path):
            return "configuration"
    for pattern in _DOMAIN_PATTERNS:
        if re.match(pattern, name) or re.match(pattern, path):
            return "domain_logic"
    return "domain_logic"  # safest default for unrecognised source files


_CATEGORY_IMPACT = {
    "domain_logic": "High",
    "api_contract": "High",
    "event_contract": "High",
    "ui_component": "Medium",
    "configuration": "Low",
    "test_or_mock": "None",
}


def default_impact_level(category: str) -> str:
    return _CATEGORY_IMPACT.get(category, "Medium")


# ── Catalog helpers ────────────────────────────────────────────────────────────

def load_catalog(path: str) -> dict:
    with open(path) as f:
        return json.load(f)


def parse_diff_files(diff_path: str) -> list[str]:
    """Extract changed file paths from a unified diff (git diff format)."""
    seen: set[str] = set()
    changed: list[str] = []
    with open(diff_path) as f:
        for line in f:
            if line.startswith("+++ ") or line.startswith("--- "):
                raw = line[4:].strip()
                if raw == "/dev/null":
                    continue
                # Strip git a/ b/ prefixes
                clean = re.sub(r"^[ab]/", "", raw)
                if clean not in seen:
                    seen.add(clean)
                    changed.append(clean)
    return changed


# ── Core logic ─────────────────────────────────────────────────────────────────

def match_features(
    changed_files: list[str], feature_registry: list[dict]
) -> dict[str, list[str]]:
    """Map each changed file to the Feature IDs whose path patterns it matches."""
    result: dict[str, list[str]] = {}
    for file_path in changed_files:
        matched: list[str] = []
        for entry in feature_registry:
            feat_id = entry.get("feature_id", "")
            for pattern in entry.get("paths", []):
                if fnmatch(file_path, pattern) or fnmatch(Path(file_path).name, pattern):
                    if feat_id not in matched:
                        matched.append(feat_id)
                    break
        result[file_path] = matched
    return result


def trace_entities(feature_ids: list[str], catalog_data: dict) -> dict:
    """
    Walk Feature → Functionality → User Story → AC chains for the given Feature IDs.
    Returns lists of affected entities and linked test artefacts.
    """
    inner = catalog_data.get("catalog", catalog_data)
    features = {f["id"]: f for f in inner.get("features", [])}
    functionalities = {fn["id"]: fn for fn in inner.get("functionalities", [])}
    user_stories = {us["id"]: us for us in inner.get("user_stories", [])}
    known_test_links: dict = catalog_data.get("known_test_links", {})

    result: dict = {
        "features": [],
        "functionalities": [],
        "user_stories": [],
        "acs_requiring_review": [],
        "scenarios_requiring_rerun": [],
    }

    visited_features: set[str] = set()
    visited_funcs: set[str] = set()
    visited_us: set[str] = set()

    for feat_id in feature_ids:
        if feat_id in visited_features:
            continue
        visited_features.add(feat_id)
        feat = features.get(feat_id)
        if not feat:
            continue
        result["features"].append({"id": feat_id, "name": feat.get("name", "")})

        # Functionalities
        for func_id in feat.get("functionalities", []):
            if func_id in visited_funcs:
                continue
            visited_funcs.add(func_id)
            fn = functionalities.get(func_id)
            label = fn.get("name", func_id) if fn else func_id
            result["functionalities"].append({"id": func_id, "name": label})

        # User Stories
        for us_id in feat.get("user_stories", []):
            if us_id in visited_us:
                continue
            visited_us.add(us_id)
            us = user_stories.get(us_id)
            if us:
                result["user_stories"].append(
                    {"id": us_id, "title": us.get("title", us.get("name", ""))}
                )

    # Collect ACs and linked scenarios from the matched entities.
    # Canonical AC-ID grammar: AC:<PARENT>-<nn>, where <PARENT> is US-<n> or FUNC-<nnn>
    # (see skills/shared/references/living-doc-glossary.md). Extract the parent and check
    # it against the User Stories / Functionalities actually traced above.
    affected_ids = {e["id"] for e in result["user_stories"]} | {
        e["id"] for e in result["functionalities"]
    }
    reviewed_acs: set[str] = set()
    rerun_scenarios: set[str] = set()
    for ac_id, test_link in known_test_links.items():
        m = _AC_ID_PATTERN.match(ac_id)
        if not m or m.group(1) not in affected_ids:
            continue
        if ac_id not in reviewed_acs:
            reviewed_acs.add(ac_id)
            result["acs_requiring_review"].append(ac_id)
        if test_link and isinstance(test_link, str) and test_link not in rerun_scenarios:
            rerun_scenarios.add(test_link)
            result["scenarios_requiring_rerun"].append(test_link)

    return result


def build_impact_map(
    changed_files: list[str],
    file_to_features: dict[str, list[str]],
    catalog: dict,
) -> dict:
    unmatched = [f for f, feats in file_to_features.items() if not feats]
    matched = {f: feats for f, feats in file_to_features.items() if feats}

    all_feature_ids: list[str] = []
    for feats in matched.values():
        for fid in feats:
            if fid not in all_feature_ids:
                all_feature_ids.append(fid)

    entities = trace_entities(all_feature_ids, catalog)

    surface_area = []
    for file_path in changed_files:
        category = classify_file(file_path)
        impact_level = default_impact_level(category)
        surface_area.append(
            {
                "file": file_path,
                "category": category,
                "impact_level": impact_level,
                "matched_features": file_to_features.get(file_path, []),
            }
        )

    recommended_actions: list[str] = []
    if entities["acs_requiring_review"]:
        recommended_actions.append(
            "Review and update affected ACs → invoke living-doc-update"
        )
    if entities["scenarios_requiring_rerun"]:
        recommended_actions.append(
            "Re-run linked Gherkin scenarios → invoke test-e2e-standards"
        )
    if any(e["category"] in ("domain_logic", "api_contract") for e in surface_area):
        recommended_actions.append(
            "Sync drifted Gherkin step text → invoke gherkin-living-doc-sync"
        )
    if unmatched:
        recommended_actions.append(
            f"{len(unmatched)} file(s) have no feature_registry entry — flag as High-impact gap "
            "and document missing coverage using living-doc-create-functionality"
        )

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "surface_area": surface_area,
        "affected_entities": entities,
        "unmatched_files": unmatched,
        "recommended_actions": recommended_actions,
    }


# ── Output helpers ─────────────────────────────────────────────────────────────

def print_summary(impact_map: dict) -> None:
    print(f"\n=== Living Doc Impact Map — {impact_map['generated_at']} ===")
    print("\nSurface area:")
    for entry in impact_map["surface_area"]:
        feats = ", ".join(entry["matched_features"]) or "UNMATCHED"
        print(
            f"  [{entry['impact_level']:6s}]  {entry['file']}"
            f"  ({entry['category']})  → {feats}"
        )
    ent = impact_map["affected_entities"]
    if ent["features"]:
        print(f"\nAffected Features:         {', '.join(f['id'] for f in ent['features'])}")
    if ent["functionalities"]:
        print(f"Affected Functionalities:  {', '.join(f['id'] for f in ent['functionalities'])}")
    if ent["user_stories"]:
        print(f"Affected User Stories:     {', '.join(u['id'] for u in ent['user_stories'])}")
    if ent["acs_requiring_review"]:
        print(f"\nACs requiring review ({len(ent['acs_requiring_review'])}):")
        for ac in ent["acs_requiring_review"]:
            print(f"  {ac}")
    if ent["scenarios_requiring_rerun"]:
        print(f"\nScenarios requiring re-run ({len(ent['scenarios_requiring_rerun'])}):")
        for s in ent["scenarios_requiring_rerun"]:
            print(f"  {s}")
    if impact_map["unmatched_files"]:
        print("\nFiles NOT in feature registry (documentation gaps):")
        for f in impact_map["unmatched_files"]:
            print(f"  ! {f}")
    if impact_map["recommended_actions"]:
        print("\nRecommended actions:")
        for action in impact_map["recommended_actions"]:
            print(f"  → {action}")


# ── Entry point ────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Trace living doc impact from a set of changed files."
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--files", "-f", nargs="+", help="Explicit list of changed file paths")
    source.add_argument("--diff", "-d", help="Path to a unified diff file")
    parser.add_argument(
        "--catalog", "-c", required=True,
        help="Path to catalog JSON (must include 'feature_registry')"
    )
    parser.add_argument("--output", "-o", help="Write JSON impact map to this file")
    parser.add_argument("--summary", "-s", action="store_true", help="Print human-readable summary")
    args = parser.parse_args()

    catalog = load_catalog(args.catalog)
    changed_files = args.files if args.files else parse_diff_files(args.diff)
    feature_registry: list[dict] = catalog.get("feature_registry", [])

    file_to_features = match_features(changed_files, feature_registry)
    impact_map = build_impact_map(changed_files, file_to_features, catalog)

    if args.summary:
        print_summary(impact_map)
    elif args.output:
        with open(args.output, "w") as f:
            json.dump(impact_map, f, indent=2)
        print(f"Impact map written to {args.output}", file=sys.stderr)
    else:
        print(json.dumps(impact_map, indent=2))


if __name__ == "__main__":
    main()
