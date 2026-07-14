# Shared Library for Agentic Skills

This directory contains shared utilities used by multiple skills to prevent code duplication and enable centralized updates.

## Modules

- **`living_doc_id.py`** — Living Doc ID auto-assignment logic
  - Used by: `living-doc-create-user-story`, `living-doc-create-feature`, `living-doc-create-functionality`
  - Exports: `load_catalog()`, `next_entity_id()`, `next_ac_id()`, `cli_main()`
  - Each skill's `scripts/next_id.py` is a thin wrapper that imports and delegates to `cli_main()`

## Pattern

Each skill that uses a shared utility maintains a wrapper script in its `scripts/` directory:

```python
import sys
from pathlib import Path

lib_path = Path(__file__).parent.parent.parent / "shared" / "lib"
sys.path.insert(0, str(lib_path))

from living_doc_id import cli_main

if __name__ == "__main__":
    sys.exit(cli_main())
```

**Benefits:**
- Single source of truth — updates to shared logic happen in one place
- Skills remain independently deployable — each still has its own `scripts/next_id.py`
- Clear intent — the wrapper makes it obvious that logic is shared
- Testable — shared tests live in `skills/shared/lib/` or in the test suite

## Adding New Shared Utilities

1. Create a new module in `skills/shared/lib/` (e.g., `skills/shared/lib/my_utility.py`)
2. Add a `cli_main(argv: list[str] | None = None) -> int` function (if the utility has CLI usage)
3. Update each consuming skill's wrapper script to import and delegate to the shared module
4. Document the module in this README
