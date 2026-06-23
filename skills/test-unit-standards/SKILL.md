---
name: test-unit-standards
description: >
  Unit test standards reference: isolation, scope, naming, assertions, coverage, fixtures.
  Does not write or audit tests.
  Triggers on: "unit test standards", "test naming convention", "best practices for unit tests",
  "how should I structure my tests".
  Does NOT trigger for: writing tests (use test-unit-write), reviewing tests (use test-unit-review),
  test doubles (use test-mocking-patterns), test data (use test-data-management), PR review (use pr-review).
license: Apache-2.0
compatibility: GitHub Copilot
---

# Unit Test Standards

**Applies to test code only.** Non-test tasks: complete normally without enforcing rules.

## Step 0 — Load reference

Detect language/framework. Load reference:

| Language / framework | Reference file |
|---|---|
| Python + pytest | `references/python-pytest.md` |
| JavaScript / TypeScript + Jest | `references/javascript-jest.md` |
| Scala + MUnit | `references/scala-munit.md` |

If no reference exists, apply language-agnostic rules below and note missing guidance.
When no violations found, explicitly confirm compliance for each category.

## Isolation

- No real external APIs, DBs, file systems, network
- Mock/stub all I/O and boundaries
- Independent tests, no shared mutable state
- Runnable in isolation, any order

## Scope

- Unit = one function, method, or class
- Test public interface only
- No direct private member access (see language reference)

## Naming and structure

- Test names state scenario (follow language reference format)
- One logical behavior per test (multiple asserts OK if collectively confirming single outcome)
- Docstring required stating scenario (not inline comments)
- No loose comments between methods; inline context comments OK (e.g. `# edge case: empty list`)

## Assertions

- Test: return values, exceptions, log messages (contract-sensitive), exit codes
- Cover success + ≥1 failure path per behaviour
- Cover boundary values & empty/null inputs
- Specific over generic assertions (see language reference)
- **Note on exception assertions:** When using `pytest.raises(..., match=...)`, the `match` parameter accepts a regex pattern. Plain literal strings (e.g., `match="Invalid user"`) are valid regex patterns. Only flag if the string contains unescaped regex metacharacters (e.g., `match="Price."` without escaping the dot) and the test intends a literal match.

## Fixtures

- Place in framework-idiomatic location (Python: `conftest.py`)
- Reuse across tests; no copy-pasted setup
- Document purpose & side effects

## Report by severity

Group violations under three headings. Empty sections: `(none)`.

### Blocker
Broken tests, real I/O, shared state (suite unreliable/order-dependent).

### Important
Missing failure/boundary coverage, weak/absent assertions, private access, copy-pasted setup, unreadable naming.

### Nit
Minor naming inconsistencies, missing fixture docstrings, style issues.

## Note: pytest `tmp_path`

`pytest.tmp_path` violates isolation (real file system). Flag as **Important**. Preferred fix: refactor to accept file-like object, use `io.BytesIO`/`io.StringIO`. Accept `tmp_path` only if core logic requires real path and refactoring disproportionate — document explicitly.
