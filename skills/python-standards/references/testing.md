# Testing Reference
Loaded automatically when working in test files (`tests/`, `test_*.py`, `*_test.py`).

## Structure
- Follow the repository's existing test layout first.
- Name test files `test_<module>.py` and functions `test_<behaviour>` unless the repo already uses a different convention.
- Separate tests with no I/O from tests that use real services or containers.
- `unit/` subdirectory is one common pattern but not required - match what the repo already has.
- Group unit tests under a class decorated with `@pytest.mark.unit`.

```python
@pytest.mark.unit
class TestJobState:
    def test_terminal_states(self) -> None:
        assert JobState.COMPLETED.value == "completed"
        assert JobState.FAILED.value == "failed"

    def test_non_terminal_states(self) -> None:
        assert JobState.ACCEPTED.value == "accepted"
        assert JobState.PROCESSING.value == "processing"
```

## Writing tests
- One behaviour per test. If the name contains "and", it is probably two tests.
- `assert expected == actual` - known-good value on the left.
- Fixtures for shared setup. Avoid deep fixture chains that obscure what the test actually needs.
- Importing inside a test function is acceptable when testing a fresh import (e.g. singleton initialisation).
- Mock external dependencies (databases, APIs, file systems) in unit tests. No real network calls.
- Use `pytest-mock`'s `mocker` fixture - never import `unittest.mock` directly.

```python
import pytest
from pytest_mock import MockerFixture

@pytest.fixture
def sample_config() -> AppConfig:
    return AppConfig(region="eu-west-1", timeout=30)


@pytest.mark.unit
class TestVendorClient:
    def test_timeout_raises_after_configured_duration(self, sample_config: AppConfig, mocker: MockerFixture) -> None:
        mocker.patch.object(HttpClient, "post", side_effect=httpx.TimeoutException("timeout"))
        with pytest.raises(VendorTimeoutError) as exc_info:
            call_vendor("test-vendor", {}, config=sample_config)
        assert exc_info.value.timeout_seconds == 30
```

## Test hygiene
- Tests must not depend on execution order.
- Tests must not share mutable state - each test starts from a clean slate.
- Test observable behaviour, not implementation details. A refactor that doesn't change behaviour shouldn't break tests.
