#!/usr/bin/env python3
"""
Quick test to verify find_unused_po_methods.py scans fixtures.ts and composition calls.

Regression coverage for the bug flagged in PR #9 review: calls were collected only
from --steps-dir, so a method called from another PageObject (composition, base-class
helpers) or from fixtures.ts read as a false-positive "unused". The docstring claimed
fixtures were scanned — they weren't (the sibling find_unused_po_components.py does
include fixtures.ts correctly).
"""
__test__ = False  # pytest: ignore this helper script

import sys
import tempfile
from pathlib import Path

from find_unused_po_methods import collect_called_methods, collect_po_methods


def test_method_called_only_from_fixtures_is_not_unused():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        pages_dir = root / "playwright" / "pages"
        steps_dir = root / "playwright" / "steps"
        pages_dir.mkdir(parents=True)
        steps_dir.mkdir(parents=True)

        (pages_dir / "LoginPage.ts").write_text(
            "export class LoginPage {\n"
            "  async loginAsAdmin() { /* ... */ }\n"
            "}\n",
            encoding="utf-8",
        )
        (steps_dir.parent / "fixtures.ts").write_text(
            "export const test = base.extend({\n"
            "  loginPage: async ({ page }, use) => {\n"
            "    await new LoginPage(page).loginAsAdmin();\n"
            "    await use(page);\n"
            "  },\n"
            "});\n",
            encoding="utf-8",
        )

        called = collect_called_methods(steps_dir, pages_dir)
    assert "loginAsAdmin" in called, called
    print("✓ A method called only from fixtures.ts is no longer reported unused")


def test_method_called_only_from_another_pageobject_is_not_unused():
    """Composition / base-class helper calls: PageA calls a method on PageB."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        pages_dir = root / "playwright" / "pages"
        steps_dir = root / "playwright" / "steps"
        pages_dir.mkdir(parents=True)
        steps_dir.mkdir(parents=True)

        (pages_dir / "BasePage.ts").write_text(
            "export class BasePage {\n"
            "  async waitForReady() { /* ... */ }\n"
            "}\n",
            encoding="utf-8",
        )
        (pages_dir / "DashboardPage.ts").write_text(
            "export class DashboardPage extends BasePage {\n"
            "  async open() {\n"
            "    await this.waitForReady();\n"
            "  }\n"
            "}\n",
            encoding="utf-8",
        )

        called = collect_called_methods(steps_dir, pages_dir)
    assert "waitForReady" in called, called
    print("✓ A method called only from another PageObject (composition) is no longer reported unused")


def test_genuinely_unused_method_still_flagged():
    """The fix must not swallow real dead code."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        pages_dir = root / "playwright" / "pages"
        steps_dir = root / "playwright" / "steps"
        pages_dir.mkdir(parents=True)
        steps_dir.mkdir(parents=True)

        (pages_dir / "LoginPage.ts").write_text(
            "export class LoginPage {\n"
            "  async neverCalled() { /* ... */ }\n"
            "}\n",
            encoding="utf-8",
        )
        (steps_dir / "login.steps.ts").write_text(
            "Given('nothing happens', () => {});\n",
            encoding="utf-8",
        )

        po_methods = collect_po_methods(pages_dir)
        called = collect_called_methods(steps_dir, pages_dir)
        unused = [m for m in po_methods if m.name not in called]
    assert [m.name for m in unused] == ["neverCalled"], unused
    print("✓ A genuinely unused method is still correctly flagged")


if __name__ == "__main__":
    try:
        test_method_called_only_from_fixtures_is_not_unused()
        test_method_called_only_from_another_pageobject_is_not_unused()
        test_genuinely_unused_method_still_flagged()
        print("\n✓ All tests passed!")
    except AssertionError as e:
        print(f"✗ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
