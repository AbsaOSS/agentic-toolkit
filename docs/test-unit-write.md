# Unit Test Writer

This skill generates complete unit tests from scratch or extends coverage for functions, classes, and modules.

## Quick Start

Ask the agent to write tests:
- "Write unit tests for this function"
- "Add tests covering the failure paths"
- "Generate test cases for this class"
- "Help me test this service"

Provide the source code, and the agent will:

1. Analyze the public API and I/O boundaries
2. Select appropriate mock strategies (stub/patch/inject)
3. Generate test cases covering happy paths, failures, and edge cases
4. Output tests in language-idiomatic format (pytest, Jest, MUnit)

## What This Skill Does

**test-unit-write** follows a 7-step workflow:

1. **Load language reference** — Detect language/framework and load conventions
2. **Analyse source** — Identify public API, dependencies, I/O boundaries, failure conditions
3. **Choose mock strategy** — Decide how to isolate HTTP, DB, files, clock, randomness
4. **Scaffold test file** — Setup imports, fixtures, mocking infrastructure
5. **Write test cases** — Happy path, failure paths (≥1 per behaviour), edge/boundary cases
6. **Assert correctly** — Use framework-specific matchers, not generic truthy checks
7. **Run and validate** — Execute tests; fix any failures before returning

## Generated Test Structure

```python
# pytest example
import pytest
from unittest.mock import MagicMock
from order_service import OrderService

@pytest.fixture
def mock_payment_gateway():
    """Mock payment gateway for order processing."""
    return MagicMock()

def test_order_succeeds_with_valid_input(mock_payment_gateway):
    """Happy path: order placed with valid amount and payment success."""
    service = OrderService(mock_payment_gateway)
    service.process_order(customer_id=123, amount=50.00)
    assert mock_payment_gateway.charge.called

def test_order_fails_on_insufficient_funds(mock_payment_gateway):
    """Failure path: payment gateway returns insufficient funds."""
    mock_payment_gateway.charge.side_effect = ValueError("Insufficient funds")
    service = OrderService(mock_payment_gateway)
    with pytest.raises(ValueError, match="Insufficient funds"):
        service.process_order(customer_id=123, amount=50.00)
```

## Coverage Requirements

Each test addresses:
- **Success path** — main behaviour under ideal conditions
- **≥1 failure path per behaviour** — exceptions, error conditions, guards
- **Boundary values** — empty, zero, None/null, max/min values

## Language Support

- **Python** — pytest with fixtures, parametrization, monkeypatch
- **JavaScript / TypeScript** — Jest with mocks, spies, async/await
- **Scala** — MUnit with scopes, fixtures, assertions

## When To Use

- Writing tests for new functions or classes
- Extending coverage for existing code
- Scaffolding test structure and mocking strategy
- Learning what good test coverage looks like

## When NOT To Use

- Reviewing existing tests → use **[test-unit-review](./test-unit-review.md)**
- Abstract standards questions → use **[test-unit-standards](./test-unit-standards.md)**
- Test doubles / mocking patterns → separate skill (test-mocking-patterns, future)
- Integration tests → use integration test skill (future)

## Related Skills

- **[test-unit-standards](./test-unit-standards.md)** — Reference for naming, isolation, assertions
- **[test-unit-review](./test-unit-review.md)** — Audit tests after writing
