#!/usr/bin/env python3
"""
Quick test for the next_id.py CLI wrapper — the one thing test_living_doc_id.py's
direct function calls don't cover: the actual subprocess/CLI plumbing (sys.path setup,
argument parsing, stdout output).

next_id.py is byte-identical across all three create-* skills (a 3-line delegation to
living_doc_id.cli_main(), already tested at the function level), so one subprocess
smoke test against one copy covers all three rather than maintaining triplicate tests.
"""
__test__ = False  # pytest: ignore this helper script

import json
import subprocess
import sys
import tempfile
from pathlib import Path

NEXT_ID_PY = (
    Path(__file__).parent.parent.parent
    / "living-doc-create-feature"
    / "scripts"
    / "next_id.py"
)


def _run(*args: str, cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(NEXT_ID_PY), *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def test_next_id_cli_returns_expected_id():
    catalog = {"features": [{"id": "FEAT-001"}, {"id": "FEAT-002"}]}
    with tempfile.TemporaryDirectory() as tmp:
        catalog_path = Path(tmp) / "catalog.json"
        catalog_path.write_text(json.dumps(catalog), encoding="utf-8")
        result = _run("--type", "FEAT", "--catalog", str(catalog_path), cwd=Path(tmp))
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "FEAT-003", repr(result.stdout)
    print("✓ next_id.py CLI wrapper returns the expected next ID")


def test_next_id_cli_ac_type_requires_parent():
    with tempfile.TemporaryDirectory() as tmp:
        catalog_path = Path(tmp) / "catalog.json"
        catalog_path.write_text("{}", encoding="utf-8")
        result = _run("--type", "AC", "--catalog", str(catalog_path), cwd=Path(tmp))
    assert result.returncode == 1, result.stdout
    assert "--parent" in result.stderr, result.stderr
    print("✓ next_id.py CLI wrapper enforces --parent for --type AC")


if __name__ == "__main__":
    try:
        test_next_id_cli_returns_expected_id()
        test_next_id_cli_ac_type_requires_parent()
        print("\n✓ All tests passed!")
    except AssertionError as e:
        print(f"✗ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
