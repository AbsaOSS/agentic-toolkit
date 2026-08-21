# Unit Test Reviewer

This skill systematically audits unit tests against isolation, scope, naming, assertions, coverage, and fixture standards.

## Quick Start

Ask the agent to review tests:
- "Review these tests"
- "Audit this test file"
- "Check my unit tests"
- "Do these follow our standards?"
- "Give feedback on this test suite"

Provide the test file, and the agent will:

1. Run the test suite (pytest, Jest, MUnit, etc.)
2. Check each standard (isolation, scope, naming, assertions, coverage, fixtures)
3. Report findings grouped by severity: **Blocker / Important / Nit**

## What This Skill Does

**test-unit-review** performs a 5-step systematic audit:

1. **Load language reference** — Detect language/framework conventions
2. **Read test file completely** — Identify units under test, test count, dependencies
3. **Run tests if available** — Surface failing tests as blockers immediately
4. **Check against standards** — Walk through each standard category in order
5. **Report findings** — Group violations by severity with specific fixes

## Report Severity Levels

### Blocker

Tests that are broken or unreliable:
- **Failing tests** — any test that doesn't pass
- **Real I/O** — network calls, file reads/writes, real database connections
- **Shared mutable state** — tests that depend on execution order or share fixtures unsafely

### Important

Gaps in coverage or weak assertions:
- **Missing failure paths** — ≥1 failure path per behaviour not tested
- **Missing boundary coverage** — empty, zero, None/null, max/min values not tested
- **Weak assertions** — `assert result`, `assert x is not None` where exact value is known
- **Private member access** — tests reaching into private internals
- **Copy-pasted setup** — fixtures duplicated instead of reused
- **Unreadable naming** — test names that don't state condition and expected outcome

### Nit

Minor style issues:
- **Naming inconsistencies** — mixing naming conventions
- **Missing fixture docstrings** — fixtures without purpose documentation
- **Style issues** — formatting, unused imports, etc.

## Example Feedback

```
### Blocker
- ❌ test_payment_service_real_api (line 18): Makes real HTTP call to payment gateway. Mock the endpoint.

### Important
- ❌ test_order_with_zero_amount (line 45): Missing. Zero is a boundary value — test must verify rejection or special handling.
- ⚠️ test_order_succeeds (line 12): Assertion `assert result` is weak. Should be `assert result.status == "success"`.
- ⚠️ mock_payment_gateway (line 8): Fixture missing docstring — state purpose and side effects.

### Nit
- test_order_invalid_... and test_process_invalid_... mixed naming. Choose one prefix.

---
**Summary**: 1 blocker (remove real I/O), 2 important (add boundary test, strengthen assertion), fix naming. No other issues.
```

## Language Support

| Language | Command | Reference |
|---|---|---|
| Python + pytest | `pytest <file> -v` | `references/python-pytest.md` |
| JavaScript / TypeScript + Jest | `npx jest <file> --no-coverage` | `references/javascript-jest.md` |
| Scala + MUnit | `./mvnw test -pl <module> -Dtest=<Class>` | `references/scala-munit.md` |
| .NET | `dotnet test --filter "FullyQualifiedName~<TestClass>"` | (future) |

## When To Use

- Reviewing test files before PR merge
- Auditing test quality on an existing codebase
- Learning what standards look like in practice
- Validating test coverage and isolation

## When NOT To Use

- Writing new tests → use **[test-unit-write](./test-unit-write.md)**
- Abstract standards questions → use **[test-unit-standards](./test-unit-standards.md)**
- Reviewing PR code (non-tests) → use **[pr-review](./pr-review.md)**
- Debugging CI failures → not this skill (use debugging workflow)

## Related Skills

- **[test-unit-write](./test-unit-write.md)** — Generate tests following standards
- **[test-unit-standards](./test-unit-standards.md)** — Reference for standards definitions
- **[pr-review](./pr-review.md)** — Review full PR (including tests + source)
