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

from living_doc_id import cli_main

if __name__ == "__main__":
    sys.exit(cli_main())
