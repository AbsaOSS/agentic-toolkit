#!/usr/bin/env python3
"""
next_id.py — Wrapper for living_doc_id library (shared)

Forwards CLI invocations to skills/shared/lib/living_doc_id.cli_main().

Usage:
    python next_id.py --type US   --catalog catalog.json   → US-005
    python next_id.py --type FEAT --catalog catalog.json   → FEAT-012
    python next_id.py --type FUNC --catalog catalog.json   → FUNC-003
    python next_id.py --type AC   --parent US-007 --catalog catalog.json  → AC:US-007-05
"""

import sys
from pathlib import Path

# Resolve the shared library path relative to this script
lib_path = Path(__file__).parent.parent.parent / "shared" / "lib"
sys.path.insert(0, str(lib_path))

try:
    from living_doc_id import cli_main
except ImportError:
    print(
        "Error: shared library not found at "
        f"{lib_path} — this skill depends on skills/shared/.\n"
        "If you installed this skill standalone, also install the shared library skill:\n"
        "  npx skills add https://github.com/AbsaOSS/agentic-toolkit -g --skill shared\n"
        "(or use a full repo clone instead of a single-skill install).",
        file=sys.stderr,
    )
    sys.exit(1)

if __name__ == "__main__":
    sys.exit(cli_main())
