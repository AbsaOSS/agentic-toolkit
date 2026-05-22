#!/usr/bin/env python3
"""
manifest_diff.py — diff .copilot/bdd/manifest.json against PageObject files on disk.

Usage:
    python manifest_diff.py [--manifest PATH] [--root PROJECT_ROOT]

Checks:
  1. Manifest entries whose pageobject_path does not exist on disk  (stale manifest)
  2. PageObject files on disk not referenced in any manifest entry  (undocumented POs)

Defaults:
  --manifest   .copilot/bdd/manifest.json
  --root       . (current working directory)

Exit code: 0 if manifest and disk are in sync, 1 if drift is detected.

Glossary reference: skills/references/living-doc-glossary.md
"""

import argparse
import json
import sys
from pathlib import Path

# Filename patterns that identify PageObject classes
PO_PATTERNS = [
    "**/*Page.py",
    "**/*Page.ts",
    "**/*Page.tsx",
    "**/*Page.java",
    "**/*Page.scala",
    "**/*PageObject.py",
    "**/*PageObject.ts",
]


def load_manifest(path: Path) -> list[dict]:
    if not path.exists():
        print(f"Error: manifest not found at {path}")
        print("  → Run a scan via @living-doc-bdd-copilot to generate the manifest.")
        sys.exit(1)
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        print(f"Error: manifest must be a JSON array. Found: {type(data).__name__}")
        sys.exit(1)
    return data


def find_pageobject_files(root: Path) -> set[str]:
    """Return relative paths of all PageObject files under root."""
    found: set[str] = set()
    for pattern in PO_PATTERNS:
        for p in root.glob(pattern):
            # Skip anything under node_modules, .venv, __pycache__
            parts = p.parts
            if any(skip in parts for skip in ("node_modules", ".venv", "__pycache__", ".git")):
                continue
            found.add(str(p.relative_to(root)))
    return found


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Diff .copilot/bdd/manifest.json against PageObject files on disk."
    )
    parser.add_argument(
        "--manifest",
        default=".copilot/bdd/manifest.json",
        help="Path to manifest.json (default: .copilot/bdd/manifest.json)",
    )
    parser.add_argument(
        "--root",
        default=".",
        help="Project root directory (default: current directory)",
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()
    manifest_path = root / args.manifest
    entries = load_manifest(manifest_path)

    disk_pos = find_pageobject_files(root)
    manifest_paths = {
        e["pageobject_path"]
        for e in entries
        if e.get("pageobject_path")
    }

    stale = sorted(p for p in manifest_paths if not (root / p).exists())
    undocumented = sorted(disk_pos - manifest_paths)

    if not stale and not undocumented:
        print(
            f"✅  manifest.json is in sync — "
            f"{len(entries)} entries, {len(disk_pos)} PageObject file(s) on disk."
        )
        return

    # Build a lookup from path → entry for richer stale output
    path_to_entry = {e.get("pageobject_path"): e for e in entries if e.get("pageobject_path")}

    if stale:
        print(f"{'=' * 60}")
        print(f"  STALE MANIFEST ENTRIES ({len(stale)})")
        print(f"  Path in manifest but not found on disk")
        print(f"{'=' * 60}")
        for po_path in stale:
            entry = path_to_entry.get(po_path, {})
            print(f"  Feature : {entry.get('feature', '(unknown)')}")
            print(f"  URL     : {entry.get('url', '(unknown)')}")
            print(f"  PO path : {po_path}")
            print(f"  → Action: update path in manifest.json, or run RE-SCAN mode")
            print()

    if undocumented:
        print(f"{'=' * 60}")
        print(f"  UNDOCUMENTED PAGE OBJECTS ({len(undocumented)})")
        print(f"  File on disk but not referenced in manifest.json")
        print(f"{'=' * 60}")
        for po_path in undocumented:
            print(f"  {po_path}")
            print(f"  → Action: add an entry to manifest.json, or delete if the file is obsolete")
            print()

    sys.exit(1)


if __name__ == "__main__":
    main()
