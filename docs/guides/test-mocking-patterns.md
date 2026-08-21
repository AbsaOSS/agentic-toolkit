# Test Mocking Patterns Skill

The `test-mocking-patterns` skill guides test double selection and implementation. It activates when you need to decide which double to use (mock, stub, spy, fake, dummy), implement a double in Python, JavaScript/TypeScript, or Scala, or diagnose a mock that isn't working.

---

## What it does

Given a dependency in the code under test, the skill:

1. **Classifies the dependency** — query (return value matters) vs command (side effect to verify) vs fire-and-forget
2. **Recommends the right double** — stub, mock, spy, fake, or dummy based on intent
3. **Provides implementation guidance** — correct patching paths, library calls, and cleanup
4. **Diagnoses broken mocks** — wrong patch target, missing cleanup, over-specified assertions, wrong return type

---

## Double selection quick reference

| Dependency interaction | Recommended double |
|---|---|
| Returns a value the unit under test uses; no need to verify the call | **Stub** |
| Called for a side effect; test must verify it was called | **Mock** |
| Need to verify the call AND preserve the real return value | **Spy** |
| Stateful in-process replacement of an interface | **Fake** |
| Required by the type signature but never invoked | **Dummy** |

> Prefer stubs over mocks — stubs make fewer assumptions about internal behaviour, keeping tests less brittle.

---

## Languages covered

| Language | Libraries |
|---|---|
| Python | `pytest-mock`, `unittest.mock`, `responses`, `pytest-httpx`, `freezegun` |
| JavaScript / TypeScript | Jest (`jest.fn()`, `jest.mock()`, `jest.spyOn()`) |
| Scala | mockito-scala |

---

## How to trigger it

Ask naturally — the skill fires on intent:

```
should I use a mock or stub for the HTTP client?
what test double should I use for the payment gateway?
my mock isn't being called — the real implementation runs instead
where should I patch requests.get?
how do I mock an environment variable?
how do I verify a method was called with specific arguments?
should I mock the boto3 client directly or wrap it?
how do I freeze time in a pytest test?
```

> **Does NOT trigger** for writing full test suites (use `test-unit-write`), reviewing test files for standards violations (use `test-unit-review`), or managing test data and fixtures (use `test-data-management`).

---

## Common patching mistakes

| Symptom | Likely cause | Fix |
|---|---|---|
| Mock is never called; real code runs | Mock not injected, or wrong patch target | Confirm the unit receives the mock; patch where the name is imported |
| `assert_called` fails but real call visible in logs | Patching the source module, not the import location | Patch `mymodule.requests.get`, not `requests.get` |
| Mock state bleeds between tests | No cleanup | Use `mocker` fixture (Python) or `jest.clearAllMocks()` in `beforeEach` |
| Test breaks on unrelated internal changes | Over-specified assertions | Use `ANY` / `expect.any()` for irrelevant args |

---

## Key principles

### Patch where the name is imported (Python)

```python
# Module under test: import requests as http_lib
# ✅ — patch the name in the module under test
mocker.patch("myapp.service.http_lib.get", return_value=stub_response)

# ❌ — patching the source has no effect on the already-imported alias
mocker.patch("requests.get", return_value=stub_response)
```

### Don't mock what you don't own

Avoid mocking third-party types (boto3, SQLAlchemy sessions, gRPC stubs) directly. Wrap them in a thin interface you control and mock that interface instead. The integration test verifying the real connector belongs in an integration test, not a unit test.

### Use freezegun for datetime (Python)

`datetime` is a C extension — patching it directly is fragile. Use `freezegun`:

```python
from freezegun import freeze_time

@freeze_time("2025-01-15 12:00:00")
def test_timestamp_is_fixed():
    ...
```

---

## Installation

The skill is installed with the rest of the toolkit:

```bash
npx skills add https://github.com/AbsaOSS/agentic-toolkit -g
```

To install only this skill:

```bash
npx skills add https://github.com/AbsaOSS/agentic-toolkit -g --skill test-mocking-patterns
```
