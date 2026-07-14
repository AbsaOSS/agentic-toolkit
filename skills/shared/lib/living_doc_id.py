#!/usr/bin/env python3
"""
living_doc_id.py — Living Doc ID Auto-Assigner (shared library)

Scans the living documentation and computes the next available ID for a given entity type.
Used by multiple skills: living-doc-create-user-story, living-doc-create-feature,
living-doc-create-functionality.

ID Convention:
  - US: Numeric only (US-001, US-002, ...)
  - FEAT: Numeric only (FEAT-001, FEAT-002, ...) assigned from catalog via next_id.py
  - FUNC: Numeric only (FUNC-001, FUNC-002, ...)

Functions:
  - load_catalog(path: str) -> dict
  - next_entity_id(catalog: dict, entity_type: str) -> str
    Raises ValueError if FEAT collection contains slug-based IDs.
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
    "FEAT": ("features", re.compile(r"^FEAT-(?:(\d+)|[a-z0-9]+(?:-[a-z0-9]+)*)$")),
    "FUNC": ("functionalities", re.compile(r"^FUNC-(\d+)$")),
}

# Width of the numeric suffix (zero-padded)
ID_WIDTH = 3


def load_catalog(path: str) -> dict:
    """Load and normalize a catalog JSON file.
    
    Raises:
        ValueError: if the JSON is not a dict, or if "catalog" exists but is not a dict.
    """
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)
    
    if not isinstance(raw, dict):
        raise ValueError(
            f"Catalog must be a JSON object (dict), not {type(raw).__name__}. "
            f"Expected format: {{'catalog': {{...}}}} or {{'user_stories': [...], ...}}"
        )
    
    # Support both {"catalog": {...}} and flat {"user_stories": [...]} formats
    if "catalog" in raw:
        catalog = raw["catalog"]
        if not isinstance(catalog, dict):
            raise ValueError(
                f"'catalog' key must be a JSON object (dict), not {type(catalog).__name__}. "
                f"Expected format: {{'catalog': {{'user_stories': [...], ...}}}}"
            )
        return catalog
    
    return raw


def next_entity_id(catalog: dict, entity_type: str) -> str:
    """
    Return the next sequential ID for US, FEAT, or FUNC entities.
    Scans the matching collection for the highest existing numeric suffix.
    
    For FEAT entities:
      - Numeric IDs (FEAT-001) are auto-incrementable.
      - Slug-based IDs (FEAT-checkout) are manual assignments and cannot be auto-incremented.
      - Raises ValueError if the collection contains any slug-based IDs (mixed conventions).
    
    Raises:
        ValueError: If entity_type is unknown, collection is malformed, or FEAT has slug-based IDs.
    """
    if entity_type not in ENTITY_TYPE_MAP:
        raise ValueError(
            f"Unknown entity type '{entity_type}'. "
            f"Must be one of: {sorted(ENTITY_TYPE_MAP)}"
        )
    collection_key, pattern = ENTITY_TYPE_MAP[entity_type]
    entities = catalog.get(collection_key, [])
    
    # Validate collection is a list
    if not isinstance(entities, list):
        raise ValueError(
            f"Catalog['{collection_key}'] must be a list, not {type(entities).__name__}. "
            f"Catalog is malformed; expected format: {{'{collection_key}': [...]}}"
        )
    
    max_num = 0
    slug_ids = []
    
    for i, entity in enumerate(entities):
        # Validate each entity is a dict
        if not isinstance(entity, dict):
            raise ValueError(
                f"Catalog['{collection_key}'][{i}] must be a dict, not {type(entity).__name__}. "
                f"All entities must be JSON objects."
            )
        
        entity_id = entity.get("id", "")
        m = pattern.match(entity_id)
        if m:
            num_part = m.group(1)
            if num_part is not None:
                # Numeric ID: extract and track max
                max_num = max(max_num, int(num_part))
            elif entity_type == "FEAT":
                # Slug-based ID detected for FEAT; collect for error reporting
                slug_ids.append(entity_id)
    
    # FEAT entities with slug-based IDs cannot use auto-increment
    if slug_ids and entity_type == "FEAT":
        raise ValueError(
            f"Cannot auto-generate next {entity_type} ID: catalog contains slug-based IDs {slug_ids}. "
            f"Slug-based Feature IDs (e.g., FEAT-checkout, FEAT-orders-api) must be assigned manually. "
            f"Either use numeric IDs exclusively, or provide the next ID explicitly."
        )

    return f"{entity_type}-{max_num + 1:0{ID_WIDTH}d}"


def next_ac_id(catalog: dict, parent_id: str) -> str:
    """
    Return the next sequential AC ID for a given parent entity (User Story or Functionality).
    AC format: AC:<parent_id>-<nn>  (two-digit zero-padded suffix)

    Scans the parent entity's acceptance_criteria list for the highest existing number.
    
    Raises:
        ValueError: If parent_id prefix is invalid, collection is malformed, or parent not found.
    """
    prefix = parent_id.split("-")[0]
    collection_map = {"US": "user_stories", "FUNC": "functionalities"}
    collection_key = collection_map.get(prefix)
    if not collection_key:
        raise ValueError(
            f"Cannot determine entity collection for parent '{parent_id}'. "
            f"Prefix must be 'US' or 'FUNC'."
        )

    entities = catalog.get(collection_key, [])
    
    # Validate collection is a list
    if not isinstance(entities, list):
        raise ValueError(
            f"Catalog['{collection_key}'] must be a list, not {type(entities).__name__}. "
            f"Catalog is malformed; expected format: {{'{collection_key}': [...]}}"
        )
    
    parent = None
    for i, entity in enumerate(entities):
        # Validate each entity is a dict
        if not isinstance(entity, dict):
            raise ValueError(
                f"Catalog['{collection_key}'][{i}] must be a dict, not {type(entity).__name__}. "
                f"All entities must be JSON objects."
            )
        if entity.get("id") == parent_id:
            parent = entity
            break
    
    if parent is None:
        raise ValueError(f"Entity '{parent_id}' not found in catalog")

    ac_list = parent.get("acceptance_criteria", [])
    
    # Validate acceptance_criteria is a list
    if not isinstance(ac_list, list):
        raise ValueError(
            f"Entity '{parent_id}' has acceptance_criteria of type {type(ac_list).__name__}, "
            f"but it must be a list."
        )
    
    ac_pattern = re.compile(rf"^AC:{re.escape(parent_id)}-(\d+)$")
    max_num = 0
    for i, ac in enumerate(ac_list):
        # Validate each AC is a dict
        if not isinstance(ac, dict):
            raise ValueError(
                f"Entity '{parent_id}' acceptance_criteria[{i}] must be a dict, "
                f"not {type(ac).__name__}. All ACs must be JSON objects."
            )
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
