# Code Examples

On-demand reference patterns. Load when you need a concrete illustration of a rule.

## Type annotations

```python
# Type alias for a complex structure
UserRecord = dict[str, str | int | None]

def fetch_users(org_id: str, *, active_only: bool = True) -> list[UserRecord]:
    ...
```

## Imports

```python
import json
import logging
from pathlib import Path

import httpx
from pydantic import BaseModel

from core.config import Settings
from core.errors import AppError
```

## Error handling - custom exception + chaining

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

## Resource management - context manager

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

## Logging

```python
logger.info("Processing %d items out of %d", processed, total)
logger.warning("Retrying request to %s (attempt %d of %d)", url, attempt, max_attempts)
```

## Mutable default argument

```python
# Wrong
def process_items(items: list[str] = []) -> list[str]: ...

# Right
def process_items(items: list[str] | None = None) -> list[str]:
    if items is None:
        items = []
    ...
```

## Docstring

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
