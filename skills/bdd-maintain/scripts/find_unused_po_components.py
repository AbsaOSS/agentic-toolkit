#!/usr/bin/env python3
"""
find_unused_po_components.py — Dead-code detector: PageObject classes never imported in step files.

Usage:
    python playwright/scripts/find_unused_po_components.py [--pages-dir DIR] [--steps-dir DIR]

Exits with code 1 if any unused PageObject classes are found (useful in CI).
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from dataclasses import dataclass


# ---------------------------------------------------------------------------
# Patterns
# ---------------------------------------------------------------------------

# Match class declarations in TypeScript: `export class FooPage {`
CLASS_DEF_RE = re.compile(r"export\s+class\s+([A-Z][a-zA-Z0-9_$]*)")

# Match import statements: `import { Foo, Bar } from './...'`
IMPORT_BRACE_RE = re.compile(r"import\s*\{([^}]+)\}\s*from")
# Match default imports: `import Foo from './...'`
IMPORT_DEFAULT_RE = re.compile(r"import\s+([A-Z][a-zA-Z0-9_$]*)\s+from")



@dataclass
class PageObjectClass:
    name: str
    file: Path


def collect_po_classes(pages_dir: Path) -> list[PageObjectClass]:
    """Extract exported class names from all PageObject .ts files."""
    classes: list[PageObjectClass] = []
    for ts_file in sorted(pages_dir.glob("*.ts")):
        text = ts_file.read_text(encoding="utf-8")
        for m in CLASS_DEF_RE.finditer(text):
            classes.append(PageObjectClass(m.group(1), ts_file))
    return classes


def collect_imported_names(steps_dir: Path) -> set[str]:
    """Collect all identifiers imported or used in step files and fixtures."""
    names: set[str] = set()
    # Also scan fixtures.ts at the parent of steps_dir or sibling file
    fixtures_file = steps_dir.parent / "fixtures.ts"
    extra_files: list[Path] = []
    if fixtures_file.exists():
        extra_files.append(fixtures_file)

    for ts_file in list(sorted(steps_dir.rglob("*.ts"))) + extra_files:
        text = ts_file.read_text(encoding="utf-8")
        # Named imports: import { Foo, Bar } from ...
        for m in IMPORT_BRACE_RE.finditer(text):
            for identifier in m.group(1).split(","):
                stripped = identifier.strip()
                # Handle `Foo as F` aliasing
                actual = stripped.split(" as ")[0].strip()
                names.add(actual)
        # Default imports
        for m in IMPORT_DEFAULT_RE.finditer(text):
            names.add(m.group(1))

    return names


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Find PageObject classes never imported in step files or fixtures."
    )
    parser.add_argument(
        "--pages-dir",
        default="playwright/pages",
        help="Directory containing PageObject *.ts files (default: playwright/pages)",
    )
    parser.add_argument(
        "--steps-dir",
        default="playwright/steps",
        help="Directory containing *.steps.ts files (default: playwright/steps)",
    )
    args = parser.parse_args()

    pages_dir = Path(args.pages_dir)
    steps_dir = Path(args.steps_dir)

    if not pages_dir.is_dir():
        print(f"ERROR: pages-dir not found: {pages_dir}", file=sys.stderr)
        return 2
    if not steps_dir.is_dir():
        print(f"ERROR: steps-dir not found: {steps_dir}", file=sys.stderr)
        return 2

    print(f"Scanning PageObject classes in:  {pages_dir}")
    print(f"Scanning imports in:             {steps_dir}")

    # Also look for fixtures.ts
    fixtures_path = steps_dir.parent / "fixtures.ts"
    if fixtures_path.exists():
        print(f"Also scanning:                   {fixtures_path}")
    print()

    po_classes = collect_po_classes(pages_dir)
    imported_names = collect_imported_names(steps_dir)

    print(f"Found {len(po_classes)} PageObject class(es) in {pages_dir}")
    print(f"Found {len(imported_names)} imported name(s) across step files")
    print()

    unused = [c for c in po_classes if c.name not in imported_names]

    if not unused:
        print("✅  All PageObject classes are imported/used.")
        return 0

    print(f"⚠️  {len(unused)} UNUSED PageObject class(es) found:\n")
    for cls in sorted(unused, key=lambda c: c.name):
        print(f"  {cls.name:<40}  {cls.file}")
    print()
    print("Action: either import and use these classes in step files, or remove the PageObject files.")
    print()
    return 1


if __name__ == "__main__":
    sys.exit(main())
