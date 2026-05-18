---
name: python-standards
description: >-
  Python coding standards for CPS projects. Covers repository-first conventions, type annotations, error handling, testing, logging, documentation, async code, and dependency hygiene. Activate this skill whenever the user is editing or creating .py files, working in a Python project, or asks for help writing functions, classes, tests, modules, or fixing code - even if they do not say "Python" explicitly. Also triggers on questions about coding conventions, type hints, pytest, imports, logging setup, or dependency management in a Python context.
---

# Python Coding Standards

These standards define how Python code is written across CPS projects. They focus on code quality, safety, and maintainability. Tooling choices vary by project and are not prescribed here.

## Repository-first workflow

Before applying these standards in an existing repository:

- Inspect the nearby Python files and project configuration first.
- Follow the repository's established formatter, import sorter, linter, type checker, test framework, packaging flow, and docstring style unless the user asks you to change them.
- If conventions differ across the repo, prefer the pattern already used in the same package or service you are editing.
- Only introduce new tools or broad convention changes when the user explicitly asks for them.

## Type Annotations

Python is dynamically typed, which means entire categories of bugs (type mismatches, contract violations, null references) can reach production undetected. Type annotations are the primary defence against this.

### Rules

- Annotate all public function signatures: both parameters and return types.
- Annotate class attributes and instance variables.
- Use built-in generics (`list[str]`, `dict[str, int]`, `tuple[int, ...]`) instead of importing from `typing` (Python 3.9+ supports this natively).
- Use `X | None` instead of `Optional[X]` (Python 3.10+ union syntax).
- Create type aliases for complex types to improve readability.

```python
# Type alias for a complex structure
UserRecord = dict[str, str | int | None]

def fetch_users(org_id: str, *, active_only: bool = True) -> list[UserRecord]:
    ...
```

### `# type: ignore` is a last resort

The correct response to a type error is to fix the code or refactor the types so the checker is satisfied. `# type: ignore` should only be used when the code is genuinely correct but the type system cannot express it. This is rare.

When suppression is truly unavoidable:

1. Always include the specific error code: `# type: ignore[assignment]`
2. Always add a justification explaining why the suppression is necessary: `# type: ignore[override]  # covariant return is safe here`
3. A bare `# type: ignore` without an error code is never acceptable!

If you find yourself reaching for `# type: ignore`, first try these alternatives:
- Add a `cast()` to make the type explicit.
- Introduce a `Protocol` or `TypeVar` to express the constraint properly.
- Refactor the code so the type checker can follow the logic.
- Use `typing.overload` to express different return types for different inputs.

## Code Structure

### Imports

- Prefer imports at the top of the file. Local imports are acceptable when they avoid optional dependencies at import time, break circular imports, or defer expensive startup work.
- Group imports in three blocks separated by a blank line: standard library, third-party, local.
- Prefer absolute imports. Relative imports are acceptable within a package when they improve clarity.
- Never use wildcard imports (`from module import *`).

```python
import json
import logging
from pathlib import Path

import httpx
from pydantic import BaseModel

from core.config import Settings
from core.errors import AppError
```

### Module organisation

- One primary concern per module. If a module has grown beyond ~300 lines, consider splitting it.
- Keep `__init__.py` files minimal. They should re-export public API, not contain logic.
- Separate business logic from infrastructure (I/O, environment variables, network calls). Business logic should be testable without mocking external systems.

### Naming

Follow PEP 8 conventions:
- `snake_case` for functions, methods, variables, and module names.
- `PascalCase` for classes.
- `UPPER_SNAKE_CASE` for module-level constants.
- Prefix private attributes and methods with a single underscore (`_internal_method`).
- Avoid abbreviations unless they are universally understood (`id`, `url`, `http`).

## Error Handling

### Principles

- Catch specific exceptions, never bare `except:` or `except Exception:`.
- Use `raise ... from err` to preserve the exception chain. This makes debugging significantly easier because the full traceback is visible.
- Create custom exception classes for domain-specific errors rather than reusing generic built-ins.
- Fail fast and fail loudly: validate inputs early and raise immediately on invalid state.

```python
class VendorTimeoutError(AppError):
    """Raised when a vendor API call exceeds the configured timeout."""

    def __init__(self, vendor: str, timeout_seconds: float) -> None:
        super().__init__(f"Vendor '{vendor}' did not respond within {timeout_seconds}s")
        self.vendor = vendor
        self.timeout_seconds = timeout_seconds


def call_vendor(vendor: str, payload: dict[str, str]) -> VendorResponse:
    try:
        response = client.post(url, json=payload, timeout=timeout)
    except httpx.TimeoutException as err:
        raise VendorTimeoutError(vendor, timeout) from err
```

### Resource management

- Always use context managers (`with`) for resources that need cleanup: files, connections, locks.
- Prefer `contextlib.contextmanager` for lightweight resource wrappers.

```python
from collections.abc import Generator
from contextlib import contextmanager

@contextmanager
def db_transaction(conn: Connection) -> Generator[Cursor, None, None]:
    cursor = conn.cursor()
    try:
        yield cursor
        conn.commit()
    except Exception:
        conn.rollback()
        raise
```

## Runtime Validation

Static type checking catches many bugs, but it cannot verify data that crosses system boundaries (user input, API responses, configuration files, environment variables). Validate this data at the boundary where it enters the system.

### Principles

- Validate external data at the point of ingestion, not deep inside business logic.
- Prefer strict validation: reject unknown fields and unexpected types rather than silently coercing.
- Keep validated data immutable after creation when practical. This prevents accidental mutation as data flows through the system.
- For vendor API responses, be lenient about unknown fields (vendors may add them) but strict about expected fields.
- Define data contracts as explicit models or data classes, not raw dicts. Typed structures make the expected shape discoverable and enforceable.

## Testing

### Structure

- Follow the repository's existing test layout. In repos that mirror the source tree, `src/handlers/` maps to `tests/unit/handlers/`.
- Name test files `test_<module>.py` and test functions `test_<behaviour>` unless the repository already uses a different convention.
- Separate unit tests (no I/O, no network) from integration tests (real services, containers).

### Writing tests

- Each test should verify one behaviour. If a test name contains "and", it is probably testing two things.
- Use `assert expected == actual` (not the reverse). Put the known-good value on the left.
- Use fixtures for shared setup. Avoid deep fixture chains that obscure what the test actually needs.
- Mock external dependencies (databases, APIs, file systems) in unit tests. Never make real network calls.
- Always use `pytest-mock`'s `mocker` fixture for mocking. Never import `unittest.mock` directly - it bypasses pytest's fixture lifecycle and teardown guarantees.

```python
import pytest
from pytest_mock import MockerFixture

@pytest.fixture
def sample_config() -> AppConfig:
    return AppConfig(region="eu-west-1", timeout=30)


def test_timeout_raises_after_configured_duration(
    sample_config: AppConfig,
    mocker: MockerFixture,
) -> None:
    mocker.patch.object(HttpClient, "post", side_effect=httpx.TimeoutException("timeout"))
    with pytest.raises(VendorTimeoutError) as exc_info:
        call_vendor("test-vendor", {}, config=sample_config)
    assert exc_info.value.timeout_seconds == 30
```

### Test hygiene

- Tests must not depend on execution order.
- Tests must not share mutable state. Each test starts from a clean slate.
- Keep module-level setup lightweight so each test's inputs and expectations stay obvious.
- Avoid testing implementation details; test observable behaviour. If a refactor doesn't change behaviour, tests shouldn't break.

## Logging

### Principles

- Use `logging.getLogger(__name__)`, never `print()` in production code. Print statements are not structured, cannot be filtered by level, and disappear in containerised environments.
- Use lazy formatting in log calls - pass values as arguments, never use f-strings or `%` formatting inline. This avoids the cost of string formatting when the log level is disabled.
- Match the format specifier to the argument type: `%s` for strings, `%d` for integers, `%f` for floats. Typed specifiers are self-documenting and make type mismatches visible at the call site.

```python
logger.info("Processing %d items out of %d", processed, total)
logger.warning("Retrying request to %s (attempt %d of %d)", url, attempt, max_attempts)
```

- If the repository uses structured logging, keep field names stable and pass important values as structured fields rather than hiding them in free-form strings.
- F-strings are acceptable in exception messages where they are always evaluated: `raise ValueError(f"Invalid ID: {user_id}")`.

### Log levels

Use standard levels consistently:

| Level | Use for |
|-------|---------|
| `DEBUG` | Development detail: variable values, control flow tracing |
| `INFO` | Operational events: request handled, job started, config loaded |
| `WARNING` | Recoverable issues: retry succeeded, deprecated feature used |
| `ERROR` | Failures that need attention: unhandled exception, vendor error |
| `CRITICAL` | Non-recoverable: service cannot start, data corruption detected |

### Security

- **Never log credentials, tokens, API keys, or PII.** The blast radius of a log leak is the same as a credential leak.
- Sanitise or redact sensitive fields before logging.
- Be cautious with `repr()` or `str()` on objects that may contain secrets.

## Documentation

### Docstrings

- Write docstrings for all public modules, classes, and functions.
- Start with a single summary line. This is what tools and humans scan first.
- Follow the repository's existing docstring style (Google, NumPy, reST, or concise single-line forms). If the repository has no clear convention, choose one style and apply it consistently.
- Use single backticks for inline code references in docstrings.

```python
def retry_with_backoff(
    func: Callable[[], T],
    max_attempts: int = 3,
    base_delay: float = 1.0,
) -> T:
    """Execute `func` with exponential backoff on failure.

    Args:
        func: Zero-argument callable to retry.
        max_attempts: Maximum number of attempts before giving up.
        base_delay: Initial delay in seconds, doubled after each failure.

    Returns:
        The return value of `func` on success.

    Raises:
        RetryExhaustedError: If all attempts fail.
    """
```

### Comments

- Code should be self-explanatory through good naming. Comment the *why*, not the *what*.
- Do not use separator comments (`# -----------`) to divide sections. Use functions or classes instead.
- Remove commented-out code. Version control preserves history.

## Idiomatic Python

### Prefer modern syntax

- Use f-strings for string formatting (except in log calls; see Logging above).
- Use `pathlib.Path` instead of `os.path` for file system operations.
- Use dataclasses or typed models instead of plain dicts for structured data.
- Use `enum.Enum` for fixed sets of choices rather than string constants.
- Use list/dict/set comprehensions instead of `map()`/`filter()` with lambdas.
- Prefer `tuple` over `list` for sequences that should not change after creation.
- Use `frozenset` for fixed sets that need to be hashable or used as dict keys.
- Use `@dataclass(frozen=True)` for data objects that must not be mutated after construction - frozen dataclasses are hashable and raise `FrozenInstanceError` on accidental assignment.

### Defensive patterns

- Use `if x is None` rather than `if not x` when checking for `None`. Empty strings, zero, and empty collections are falsy but not `None`.
- Prefer `dict.get(key, default)` over catching `KeyError` for optional lookups.
- Use `functools.lru_cache` or `functools.cache` for expensive pure computations.
- Avoid mutable default arguments (`def f(items: list[str] = [])`). Use `None` and create inside the function body.

```python
def process_items(items: list[str] | None = None) -> list[str]:
    if items is None:
        items = []
    ...
```

### Async patterns

When writing async code:

- Use `async with` for async context managers (HTTP sessions, DB connections).
- Use `asyncio.gather()` for concurrent independent tasks rather than sequential `await`.
- Never mix sync and async I/O. A blocking call in an async function starves the event loop.
- Use `asyncio.to_thread()` for blocking sync I/O or lightweight legacy sync helpers. For truly CPU-bound work, prefer a process pool, worker, or dedicated service.

## Dependencies

- Follow the repository's existing dependency-management approach. For new projects, or repos that already use modern packaging, prefer `pyproject.toml` with PEP 621 metadata.
- If the repository uses `requirements.txt`, constraints files, Poetry, uv, or another established workflow, stay consistent unless the user explicitly asks for a migration.
- Use version constraints that match the project type and release strategy: libraries often use compatible ranges, while applications often lock more tightly for reproducible deployments.
- Separate runtime dependencies from dev/test dependencies when the existing tooling supports it.
- When adding or changing a dependency, update the related lockfile or constraints file in the same change if the repository tracks one.

## Database

CPS projects prefer to access databases directly using `aiosql` to keep SQL out of Python string literals.

- Define all queries in `.sql` files. `aiosql` loads them and exposes each named query as a typed callable. SQL stays reviewable, syntax-highlighted, and separated from application logic.
- Name query files by domain: `users.sql`, `payments.sql`. One file per logical area keeps queries discoverable.
- Never inline SQL as string literals in Python. String-embedded SQL cannot be reviewed independently, is not syntax-highlighted, and is a SQL-injection foothold when variables are interpolated carelessly.

```python
import aiosql
import psycopg2

# queries/users.sql contains:
# -- name: get_active^
# SELECT id, email FROM users WHERE active = true;

queries = aiosql.from_path("queries/", "psycopg2")

def get_active_users(conn: psycopg2.extensions.connection) -> list[UserRecord]:
    return queries.users.get_active(conn)
```

Parameterised queries in `.sql` files are safe from injection by construction - `aiosql` passes values through the driver's parameter binding, never string interpolation.

## Security

- Never commit credentials, API keys, or tokens to source code. Load secrets from environment variables or a secrets manager at runtime.
- Use the `secrets` module for generating tokens and random values, not `random` (which is not cryptographically secure).
- Validate and sanitise all user-provided input before using it in queries, commands, or file paths.
- Be explicit about timeouts on all network calls. Hanging connections are a denial-of-service vector.
- Lock or pin dependencies according to the repository's release process, and audit them regularly. Supply-chain attacks through compromised packages are a real and growing threat.
