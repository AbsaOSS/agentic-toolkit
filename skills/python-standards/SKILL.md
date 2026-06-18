---
name: python-standards
description: >-
  Python coding standards, that covers repository-first conventions, type annotations, error handling, testing, logging, documentation, async code, and dependency hygiene. Activate this skill whenever the user is editing or creating .py files, working in a Python project, or asks for help writing functions, classes, tests, modules, or fixing code - even if they do not say "Python" explicitly. Also triggers on questions about coding conventions, type hints, pytest, imports, logging setup, or dependency management in a Python context.
---

# Python Coding Standards

## Initial phase - Context probe

**Repo conventions first.** Check for `pyproject.toml`, `setup.cfg`, `.pre-commit-config.yaml`, `CONTRIBUTING.md`. If found: read and follow them. Skip any rule below that conflicts. Don't introduce new tools unless the user explicitly asks.

**Infer mode and extras from file path:**

| Signal | Mode | Load extras |
|--------|------|-------------|
| Path contains `tests/`, or filename matches `test_*.py` / `*_test.py` | strict | load `references/testing.md` |
| Path in `src/`, `app/`, or a named service package | strict | don't load extras |
| Path in `scripts/`, `tools/`, `notebooks/`, or a one-off utility | relaxed | don't load extras |
| Ambiguous - none of the above match | **ask the user**: "strict (production) or relaxed (script)?" | based on answer |

**Relaxed mode:** annotate public API only; `print()` allowed; docstrings recommended but not required.

---

## Type Annotations

- Annotate all public function signatures (params + return). Relaxed: public API only.
- Annotate class attributes and instance variables.
- Use built-in generics: `list[str]`, `dict[str, int]`, `tuple[int, ...]` (Python 3.9+).
- Use `X | None` not `Optional[X]` (Python 3.10+).
- Create type aliases for complex types to improve readability.
- `# type: ignore` only when the type system genuinely can't express correct code. Always include the error code and a justification: `# type: ignore[assignment]  # covariant return is safe here`. A bare `# type: ignore` is never acceptable.

## Code Structure

**Imports:** top of file; three blocks (stdlib / third-party / local) separated by blank lines; never `from x import *`. Local imports acceptable to break circular deps or defer startup cost.

**Module:** one primary concern per module; `__init__.py` re-exports only, no logic; separate business logic from I/O so it's testable without mocking infrastructure.

**Naming (PEP 8):** `snake_case` functions/variables, `PascalCase` classes, `UPPER_SNAKE_CASE` constants, `_prefix` for private. No abbreviations unless universally understood (`id`, `url`, `http`).

## Error Handling

- Catch specific exceptions. Broad `except Exception:` is acceptable only at top-level boundaries (e.g., request handlers, background workers) to log and re-raise or convert to a safe response - never silently swallow.
- Use `raise ... from err` to preserve the chain.
- Create domain-specific exception classes instead of reusing generic built-ins.
- Fail fast: validate inputs early, raise immediately on invalid state.
- Use `with` for all resources needing cleanup (files, connections, locks).

## Runtime Validation

- Validate external data (user input, API responses, env vars) at the ingestion boundary, not deep in logic.
- Strict by default: reject unknown fields and unexpected types; don't silently coerce.
- Keep validated data immutable after creation when practical.
- For vendor responses: lenient on unknown fields, strict on expected fields.

## Logging

- Use `logging.getLogger(__name__)` - never `print()` in production code.
- Lazy format: pass values as args - `logger.info("Processing %d items", count)` - not f-strings in log calls.
- f-strings are fine in exception messages (always evaluated): `raise ValueError(f"Invalid ID: {user_id}")`.
- Never log credentials, tokens, API keys, or PII. Sanitise or redact sensitive fields before logging.

| Level | Use for |
|-------|---------|
| `DEBUG` | Dev detail: variable values, control flow |
| `INFO` | Operational events: request handled, job started |
| `WARNING` | Recoverable issues: retry succeeded, deprecated feature used |
| `ERROR` | Failures needing attention |
| `CRITICAL` | Non-recoverable: service can't start, data corruption |

## Documentation

- Docstring on every public module, class, and function. First line: single summary sentence.
- Follow the repo's existing docstring style (Google, NumPy, reST). No convention → pick one and be consistent.
- Comment the *why*, not the *what*. Remove commented-out code.

## Idiomatic Python

- f-strings for formatting (except log calls - see above).
- `pathlib.Path` over `os.path`.
- Dataclasses or typed models over plain dicts. `enum.Enum` for fixed sets.
- `@dataclass(frozen=True)` for immutable value objects.
- List/dict/set comprehensions over `map()`/`filter()` with lambdas.
- `if x is None` not `if not x` for None checks.
- `dict.get(key, default)` for optional lookups. Use assignment expressions (`:=`) to combine fetch and check: `if value := d.get("key"):` avoids a redundant double-lookup.
- No mutable default arguments - use `None` + conditional creation in body.
- `asyncio.gather()` for concurrent independent tasks. Never block the event loop with sync I/O.
- `asyncio.to_thread()` for blocking sync helpers; process pool for CPU-bound work.

## Dependencies

- Follow the repo's existing dependency-management approach.
- For new projects or repos already using modern packaging, prefer `pyproject.toml` with PEP 621.
- Match version constraints to project type: libraries → compatible ranges; applications → tighter lockfiles.
- Separate runtime from dev/test dependencies when tooling supports it.
- When adding or changing a dependency, update the related lockfile in the same change.

## Database

- Never inline SQL as string literals in Python.
- Define queries in `.sql` files. Consider `aiosql` to load them as typed callables. Not mandated; follow what the repo already uses.
- Always pass query parameters through the driver's binding - never string interpolation.

## Security

- Never commit credentials, API keys, or tokens. Load secrets from env vars or a secrets manager at runtime.
- Use the `secrets` module for tokens and random values - `random` is not cryptographically secure.
- Validate and sanitise all user-provided input before using it in queries, commands, or file paths.
- Set explicit timeouts on all network calls - hanging connections are a denial-of-service vector.
- Keep dependencies locked per the repo's process and audit them regularly.

For code patterns and examples, see `references/examples.md`.
