# Shared Library for Agentic Skills

This directory contains shared utilities used by multiple skills to prevent code duplication and enable centralized updates.

## Modules

- **`living_doc_id.py`** — Living Doc ID auto-assignment logic
  - Used by: `living-doc-create-user-story`, `living-doc-create-feature`, `living-doc-create-functionality`
  - Exports: `load_catalog()`, `next_entity_id()`, `next_ac_id()`, `cli_main()`
  - Each skill's `scripts/next_id.py` is a thin wrapper that imports and delegates to `cli_main()`

- **`ac_tag.py`** — Canonical AC-ID grammar (`AC:<US|FUNC>-<n>-<nn>`): both the `@AC:`
  Cucumber tag form and the bare `AC:...` form, plus tag-line-walking helpers
  - Used by: `gherkin-living-doc-sync` (`scripts/scan_ac_links.py`), `living-doc-scenario-creator`
    (`scripts/coverage_report.py`), `living-doc-update` (`scripts/validate_entity.py`)
  - Exports: `AC_TAG_PATTERN`, `AC_ID_PATTERN`, `match_ac_tag()`, `iter_ac_tags()`,
    `TAG_LINE`, `get_tag_lines_above()`, `canonicalize_ac_id()`
  - No `cli_main()` — this is a pure function library, not a CLI tool, so each consumer
    imports the specific functions/constants it needs directly (see Pattern B below)
    rather than delegating a whole command to it
  - Extracted after a review found the consuming scripts had silently forked on what
    counts as a valid AC ID: `coverage_report.py` accepted `FEAT`/slug-parent tags that
    `scan_ac_links.py` rejected as malformed, and `validate_entity.py` had its own
    third, incompatible `AC_ID_PATTERN` that rejected the canonical format entirely

## Pattern

Two import styles exist, depending on what the shared module offers.

**Pattern A — CLI delegation.** When the shared module exposes a `cli_main()` and a
skill's script *is* that CLI tool (e.g. `next_id.py`), the script is a thin wrapper:

```python
import sys
from pathlib import Path

lib_path = Path(__file__).parent.parent.parent / "shared" / "lib"
sys.path.insert(0, str(lib_path))

try:
    from living_doc_id import cli_main
except ImportError:
    print(
        f"Error: shared library not found at {lib_path} — this skill depends on skills/shared/.\n"
        "If you installed this skill standalone, also install the shared library skill:\n"
        "  npx skills add https://github.com/AbsaOSS/agentic-toolkit -g --skill shared\n"
        "(or use a full repo clone instead of a single-skill install).",
        file=sys.stderr,
    )
    sys.exit(1)

if __name__ == "__main__":
    sys.exit(cli_main())
```

**Pattern B — direct function import.** When the shared module is a plain function
library (no `cli_main()`) and the consumer is a larger script with its own logic
(e.g. `scan_ac_links.py`, `coverage_report.py`), import the needed functions directly
near the top of the file, after the same `sys.path.insert`:

```python
import sys
from pathlib import Path

lib_path = Path(__file__).parent.parent.parent / "shared" / "lib"
sys.path.insert(0, str(lib_path))

try:
    from ac_tag import match_ac_tag, get_tag_lines_above
except ImportError:
    print(
        f"Error: shared library not found at {lib_path} — this skill depends on skills/shared/.\n"
        "If you installed this skill standalone, also install the shared library skill:\n"
        "  npx skills add https://github.com/AbsaOSS/agentic-toolkit -g --skill shared\n"
        "(or use a full repo clone instead of a single-skill install).",
        file=sys.stderr,
    )
    sys.exit(1)
```

There is no separate wrapper file in this case — creating one per imported function
would add indirection without a matching "this file is the CLI entrypoint" delegation
to justify it. Do not duplicate the imported logic locally instead.

**The `try`/`except ImportError` is required in both patterns**, not optional — without
it, a standalone single-skill install fails with a raw `ModuleNotFoundError` traceback
instead of a message that tells the user what to do about it.

**Benefits (both patterns):**
- Single source of truth — updates to shared logic happen in one place
- Clear intent — the `sys.path.insert` + import makes it obvious the logic is shared
- Testable — shared tests live in `skills/shared/lib/` (see `test_living_doc_id.py`)

**Standalone installs:** `skills/shared/` has its own `SKILL.md` ([shared/SKILL.md](../SKILL.md))
specifically so it can be installed as a normal, name-matching skill unit — a sibling
directory alongside any dependent skill. A single-skill install of, say,
`living-doc-create-feature` still needs a second, explicit install of `shared`:

```bash
npx skills add https://github.com/AbsaOSS/agentic-toolkit -g --skill living-doc-create-feature
npx skills add https://github.com/AbsaOSS/agentic-toolkit -g --skill shared
```

There's no dependency graph in the install tooling, so this has to be a documented
manual step, not something the CLI resolves automatically. The full install-command
list for every skill that needs `shared` is kept centrally in
[.github/agents/living-doc-bdd-copilot.agent.md](../../../.github/agents/living-doc-bdd-copilot.agent.md)
rather than repeated in each dependent skill's own `SKILL.md` — one place to keep in
sync as new shared-lib consumers are added. The `try`/`except` above is the fallback
for when a user installs a skill without following that list.

## Adding New Shared Utilities

1. Create a new module in `skills/shared/lib/` (e.g., `skills/shared/lib/my_utility.py`)
2. Add a `cli_main(argv: list[str] | None = None) -> int` function (if the utility has CLI usage)
3. Update each consuming skill's wrapper script to import and delegate to the shared module
4. Document the module in this README
