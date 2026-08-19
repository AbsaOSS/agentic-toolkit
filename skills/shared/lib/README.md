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

from living_doc_id import cli_main

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

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "shared" / "lib"))

from ac_tag import match_ac_tag, get_tag_lines_above
```

There is no separate wrapper file in this case — creating one per imported function
would add indirection without a matching "this file is the CLI entrypoint" delegation
to justify it. Do not duplicate the imported logic locally instead.

**Benefits (both patterns):**
- Single source of truth — updates to shared logic happen in one place
- Clear intent — the `sys.path.insert` + import makes it obvious the logic is shared
- Testable — shared tests live in `skills/shared/lib/` (see `test_living_doc_id.py`)

**Known limitation:** any skill that imports from `skills/shared/lib/` (both patterns)
currently breaks if installed standalone, since `skills/shared/` has no `SKILL.md` and
isn't itself an installable unit — the `sys.path` hack assumes the shared tree exists
alongside it. This is a pre-existing, separately tracked issue (not specific to any one
module here); fixing it is a repo-level call, not something each new shared module
should work around individually.

## Adding New Shared Utilities

1. Create a new module in `skills/shared/lib/` (e.g., `skills/shared/lib/my_utility.py`)
2. Add a `cli_main(argv: list[str] | None = None) -> int` function (if the utility has CLI usage)
3. Update each consuming skill's wrapper script to import and delegate to the shared module
4. Document the module in this README
