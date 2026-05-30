#!/usr/bin/env python3
"""
find_unused_po_methods.py — Dead-code detector: PageObject methods never called from step files.

Usage:
    python playwright/scripts/find_unused_po_methods.py [--pages-dir DIR] [--steps-dir DIR]

Exits with code 1 if any unused methods are found (useful in CI).
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

# Public method definitions in TypeScript classes:
#   async methodName(       methodName(
# Exclude: constructor, private/protected (prefixed with modifier word)
# Match only on lines that look like method declarations (not calls)
METHOD_DEF_RE = re.compile(
    r"""
    ^[ \t]*                              # leading indent
    (?!private|protected|readonly|static|get |set )  # not a modifier-only line
    (?:async\s+)?                        # optional async
    ([a-zA-Z_$][a-zA-Z0-9_$]*)          # method name
    \s*\(                                # opening paren
    (?!.*:\s*Promise|\s*\{)             # exclude constructor-like and block-only lines
    """,
    re.VERBOSE | re.MULTILINE,
)

# Simpler fallback: any `async name(` or `name(` at line start with content
# We'll collect both and deduplicate
SIMPLE_METHOD_RE = re.compile(
    r"""^[ \t]+(?:async\s+)([a-zA-Z_$][a-zA-Z0-9_$]*)\s*\(""",
    re.MULTILINE,
)

# TypeScript getter shorthand — these are locators, not callable methods
GETTER_RE = re.compile(r"^[ \t]+get\s+([a-zA-Z_$][a-zA-Z0-9_$]*)\s*\(", re.MULTILINE)

# Method calls from step files: `.methodName(`  or  `fixture.methodName(`
# Capture any `.identifier(` occurrence
CALL_RE = re.compile(r"\.([a-zA-Z_$][a-zA-Z0-9_$]*)\s*\(")

# Excluded names — too generic or framework-level
EXCLUDED_NAMES = frozenset({
    "constructor", "toString", "valueOf", "then", "catch", "finally",
    "nth", "first", "last", "locator", "getByTestId", "getByRole",
    "getByText", "fill", "click", "isVisible", "isDisabled", "isEnabled",
    "waitFor", "expectToBeVisible", "expect", "goto", "reload",
    "setTimeout", "setInputFiles", "hover", "press", "type", "check",
    "uncheck", "selectOption", "evaluate", "dispatchEvent", "focus",
    "blur", "screenshot", "textContent", "innerText", "inputValue",
    "getAttribute", "scrollIntoViewIfNeeded",
    # common Angular/Playwright helpers
    "map", "filter", "forEach", "push", "join", "split", "trim",
    "toLowerCase", "toUpperCase", "replace", "includes", "startsWith",
    "endsWith", "slice", "substring", "indexOf",
})


@dataclass
class MethodDef:
    name: str
    file: Path
    line: int


def collect_po_methods(pages_dir: Path) -> list[MethodDef]:
    """Extract public method names from all PageObject .ts files."""
    methods: list[MethodDef] = []
    seen: set[tuple[Path, str]] = set()

    for ts_file in sorted(pages_dir.glob("*.ts")):
        text = ts_file.read_text(encoding="utf-8")
        lines = text.splitlines()

        # Look for `async methodName(` or method-like declarations
        for m in re.finditer(r"^[ \t]+(?:async\s+)?([a-zA-Z_$][a-zA-Z0-9_$]*)\s*\(", text, re.MULTILINE):
            name = m.group(1)
            if name in EXCLUDED_NAMES:
                continue
            if name == "constructor":
                continue
            line_num = text[: m.start()].count("\n") + 1
            # skip getter declarations
            line_text = lines[line_num - 1] if line_num <= len(lines) else ""
            if re.match(r"^\s*get\s+", line_text):
                continue

            key = (ts_file, name)
            if key not in seen:
                seen.add(key)
                methods.append(MethodDef(name, ts_file, line_num))

    return methods


def collect_called_methods(steps_dir: Path) -> set[str]:
    """Collect all method names called (via `.name(`) in step files and fixtures."""
    called: set[str] = set()
    for ts_file in sorted(steps_dir.rglob("*.ts")):
        text = ts_file.read_text(encoding="utf-8")
        for m in CALL_RE.finditer(text):
            called.add(m.group(1))
    return called


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Find PageObject methods never called from step files."
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

    print(f"Scanning PageObject methods in:  {pages_dir}")
    print(f"Scanning method calls in:        {steps_dir}")
    print()

    po_methods = collect_po_methods(pages_dir)
    called_methods = collect_called_methods(steps_dir)

    print(f"Found {len(po_methods)} public method(s) across {pages_dir}")
    print(f"Found {len(called_methods)} distinct method call(s) across {steps_dir}")
    print()

    unused = [m for m in po_methods if m.name not in called_methods]

    if not unused:
        print("✅  All PageObject methods are used.")
        return 0

    print(f"⚠️  {len(unused)} UNUSED PageObject method(s) found:\n")
    by_file: dict[Path, list[MethodDef]] = {}
    for m in unused:
        by_file.setdefault(m.file, []).append(m)

    for file, methods in sorted(by_file.items()):
        print(f"  {file}")
        for meth in sorted(methods, key=lambda x: x.line):
            print(f"    line {meth.line:4d}  {meth.name}()")
    print()
    return 1


if __name__ == "__main__":
    sys.exit(main())
