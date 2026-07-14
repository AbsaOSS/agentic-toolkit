#!/usr/bin/env python3
"""
living_doc_id.py — Living Doc ID Auto-Assigner (shared library)

Scans the living documentation and computes the next available ID for a given entity type.
Used by multiple skills: living-doc-create-user-story, living-doc-create-feature,
living-doc-create-functionality.

Functions:
  - load_catalog(path: str) -> dict
  - next_entity_id(catalog: dict, entity_type: str) -> str
  - next_ac_id(catalog: dict, parent_id: str) -> str
  - cli_main(argv: list[str] | None = None) -> int

Catalog JSON must contain one of:
  - Top-level keys: "user_stories", "features", "functionalities"
  - Or nested under a "catalog" key: {"catalog": {"user_stories": [...], ...}}
"""

import argparse
import json
import re
import sys

# Maps entity type token → (catalog collection key, ID regex with capture group for the number)
ENTITY_TYPE_MAP: dict[str, tuple[str, re.Pattern]] = {
    "US": ("user_stories", re.compile(r"^US-(\d+)$")),
    "FEAT": ("features", re.compile(r"^FEAT-(\d+)$")),
    "FUNC": ("functionalities", re.compile(r"^FUNC-(\d+)$")),
}

# Width of the numeric suffix (zero-padded)
ID_WIDTH = 3


def load_catalog(path: str) -> dict:
    """Load and normalize a catalog JSON file."""
    with open(path) as f:
        raw = json.load(f)
    # Support both {"catalog": {...}} and flat {"user_stories": [...]} formats
    return raw.get("catalog", raw)


def next_entity_id(catalog: dict, entity_type: str) -> str:
    """
    Return the next sequential ID for US, FEAT, or FUNC entities.
    Scans the matching collection for the highest existing numeric suffix.
    """
    if entity_type not in ENTITY_TYPE_MAP:
        raise ValueError(
            f"Unknown entity type '{entity_type}'. "
            f"Must be one of: {sorted(ENTITY_TYPE_MAP)}"
        )
    collection_key, pattern = ENTITY_TYPE_MAP[entity_type]
    entities: list[dict] = catalog.get(collection_key, [])

    max_num = 0
    for entity in entities:
        m = pattern.match(entity.get("id", ""))
        if m:
            max_num = max(max_num, int(m.group(1)))

    return f"{entity_type}-{max_num + 1:0{ID_WIDTH}d}"


def next_ac_id(catalog: dict, parent_id: str) -> str:
    """
    Return the next sequential AC ID for a given parent entity (User Story or Functionality).
    AC format: AC:<parent_id>-<nn>  (two-digit zero-padded suffix)

    Scans the parent entity's acceptance_criteria list for the highest existing number.
    """
    prefix = parent_id.split("-")[0]
    collection_map = {"US": "user_stories", "FUNC": "functionalities"}
    collection_key = collection_map.get(prefix)
    if not collection_key:
        raise ValueError(
            f"Cannot determine entity collection for parent '{parent_id}'. "
            f"Prefix must be 'US' or 'FUNC'."
        )

    entities: list[dict] = catalog.get(collection_key, [])
    parent = next((e for e in entities if e.get("id") == parent_id), None)
    if parent is None:
        raise ValueError(f"Entity '{parent_id}' not found in catalog")

    ac_pattern = re.compile(rf"^AC:{re.escape(parent_id)}-(\d+)$")
    max_num = 0
    for ac in parent.get("acceptance_criteria", []):
        m = ac_pattern.match(ac.get("id", ""))
        if m:
            max_num = max(max_num, int(m.group(1)))

    return f"AC:{parent_id}-{max_num + 1:02d}"


def cli_main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for ID generation."""
    parser = argparse.ArgumentParser(
        description="Return the next available living doc entity ID."
    )
    parser.add_argument(
        "--type", "-t",
        required=True,
        choices=["US", "FEAT", "FUNC", "AC"],
        help="Entity type to generate an ID for",
    )
    parser.add_argument(
        "--parent", "-p",
        help="Parent entity ID — required when --type is AC (e.g. US-007 or FUNC-002)",
    )
    parser.add_argument(
        "--catalog", "-c",
        required=True,
        help="Path to the catalog JSON file",
    )
    args = parser.parse_args(argv)

    if args.type == "AC" and not args.parent:
        print("Error: --parent is required when --type is AC", file=sys.stderr)
        return 1

    try:
        catalog = load_catalog(args.catalog)
        if args.type == "AC":
            result = next_ac_id(catalog, args.parent)
        else:
            result = next_entity_id(catalog, args.type)
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        print(f"Error reading catalog: {exc}", file=sys.stderr)
        return 1
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(result)
    return 0


if __name__ == "__main__":
    sys.exit(cli_main())
