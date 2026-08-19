#!/usr/bin/env python3
"""
Quick test to verify manifest_diff.py emits forward-slash relative paths.

Regression coverage for the bug flagged in PR #9 review: str(relative_to(...)) yields
backslash paths on Windows while manifest.json paths always use "/", so the set
difference between disk paths and manifest paths flagged every PageObject as
undocumented on Windows.
"""
__test__ = False  # pytest: ignore this helper script

import json
import sys
import tempfile
from pathlib import Path

from manifest_diff import find_pageobject_files, main


def test_find_pageobject_files_uses_forward_slashes():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "playwright" / "pages").mkdir(parents=True)
        (root / "playwright" / "pages" / "LoginPage.ts").write_text("", encoding="utf-8")
        found = find_pageobject_files(root)
    assert found == {"playwright/pages/LoginPage.ts"}, found
    assert all("\\" not in p for p in found), found
    print("✓ find_pageobject_files() returns forward-slash paths, no backslashes")


def test_main_reports_in_sync_when_paths_match():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "playwright" / "pages").mkdir(parents=True)
        (root / "playwright" / "pages" / "LoginPage.ts").write_text("", encoding="utf-8")
        manifest = {
            "routes": [
                {
                    "url": "/login",
                    "pageobject_path": "playwright/pages/LoginPage.ts",
                    "feature_id": "FEAT-001",
                }
            ]
        }
        (root / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

        old_argv = sys.argv
        sys.argv = ["manifest_diff.py", "--manifest", "manifest.json", "--root", str(root)]
        try:
            main()  # must not sys.exit(1) — matching paths, no drift
        finally:
            sys.argv = old_argv
    print("✓ main() reports in sync when disk and manifest paths match (Windows-safe)")


if __name__ == "__main__":
    try:
        test_find_pageobject_files_uses_forward_slashes()
        test_main_reports_in_sync_when_paths_match()
        print("\n✓ All tests passed!")
    except AssertionError as e:
        print(f"✗ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
