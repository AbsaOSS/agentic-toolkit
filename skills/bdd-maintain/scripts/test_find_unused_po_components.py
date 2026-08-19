#!/usr/bin/env python3
"""
Quick test to verify find_unused_po_components.py scans fixtures.ts and composition
imports (a PageObject class imported by another PageObject, not by a step file).

Same bug class as find_unused_po_methods.py: scanning only --steps-dir misses real
call/import sites, producing false-positive "unused" reports.
"""
__test__ = False  # pytest: ignore this helper script

import sys
import tempfile
from pathlib import Path

from find_unused_po_components import collect_imported_names, collect_po_classes


def test_class_imported_only_from_fixtures_is_not_unused():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        pages_dir = root / "playwright" / "pages"
        steps_dir = root / "playwright" / "steps"
        pages_dir.mkdir(parents=True)
        steps_dir.mkdir(parents=True)

        (pages_dir / "LoginPage.ts").write_text(
            "export class LoginPage {}\n", encoding="utf-8"
        )
        (steps_dir.parent / "fixtures.ts").write_text(
            "import { LoginPage } from './pages/LoginPage';\n"
            "export const test = base.extend({});\n",
            encoding="utf-8",
        )

        imported = collect_imported_names(steps_dir, pages_dir)
    assert "LoginPage" in imported, imported
    print("✓ A class imported only from fixtures.ts is no longer reported unused")


def test_class_imported_only_by_another_pageobject_is_not_unused():
    """Composition: a wizard's primary page imports its step sub-page."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        pages_dir = root / "playwright" / "pages"
        steps_dir = root / "playwright" / "steps"
        pages_dir.mkdir(parents=True)
        steps_dir.mkdir(parents=True)

        (pages_dir / "WizardProfileStepPage.ts").write_text(
            "export class WizardProfileStepPage {}\n", encoding="utf-8"
        )
        (pages_dir / "AccountSetupWizardPage.ts").write_text(
            "import { WizardProfileStepPage } from './WizardProfileStepPage';\n"
            "export class AccountSetupWizardPage {}\n",
            encoding="utf-8",
        )

        imported = collect_imported_names(steps_dir, pages_dir)
    assert "WizardProfileStepPage" in imported, imported
    print("✓ A class imported only by another PageObject (composition) is no longer reported unused")


def test_genuinely_unused_class_still_flagged():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        pages_dir = root / "playwright" / "pages"
        steps_dir = root / "playwright" / "steps"
        pages_dir.mkdir(parents=True)
        steps_dir.mkdir(parents=True)

        (pages_dir / "OrphanPage.ts").write_text(
            "export class OrphanPage {}\n", encoding="utf-8"
        )
        (steps_dir / "login.steps.ts").write_text(
            "Given('nothing happens', () => {});\n", encoding="utf-8"
        )

        po_classes = collect_po_classes(pages_dir)
        imported = collect_imported_names(steps_dir, pages_dir)
        unused = [c for c in po_classes if c.name not in imported]
    assert [c.name for c in unused] == ["OrphanPage"], unused
    print("✓ A genuinely unused PageObject class is still correctly flagged")


if __name__ == "__main__":
    try:
        test_class_imported_only_from_fixtures_is_not_unused()
        test_class_imported_only_by_another_pageobject_is_not_unused()
        test_genuinely_unused_class_still_flagged()
        print("\n✓ All tests passed!")
    except AssertionError as e:
        print(f"✗ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
