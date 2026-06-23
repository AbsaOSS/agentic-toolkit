---
name: test-unit-review
description: >
  Review and audit existing unit tests against quality standards. Activate when the user
  asks to review, critique, give feedback, check quality, or audit any existing test file
  — including informal requests like "does this look right?" or sharing a test for a quality
  opinion. This skill evaluates tests for isolation, scope, naming, assertions, coverage, and
  fixture reuse.
  Triggers on: "review these tests", "audit this test file", "check my tests", "are these
  tests good enough", "do these tests follow our standards", "LGTM on tests",
  "does this test look right", "is this test missing anything", "any issues with my tests",
  "give feedback on this test file", "are these tests up to scratch", "are these tests
  properly isolated", "test isolation check", "assertion quality".
  Does NOT trigger for: writing new tests (use test-unit-write), adding tests or coverage
  (use test-unit-write), choosing test doubles or mocking strategy (use test-mocking-patterns),
  managing test data strategies (use test-data-management), debugging failing tests at runtime,
  general PR review (use pr-review), or integration test planning (use test-integration-standards).
  Pairs with test-unit-write (to add missing tests) and test-unit-standards (for reference).
license: Proprietary
compatibility: GitHub Copilot
---

# Unit Test Reviewer

**For writing new tests**, use **test-unit-write**. **For test doubles**, use **test-mocking-patterns**.

## Step 1 — Load language reference

Identify language/framework from imports or file extension. Load reference:

| Language / framework | Reference file |
|---|---|
| Python + pytest | `../test-unit-standards/references/python-pytest.md` |
| JavaScript / TypeScript + Jest | `../test-unit-standards/references/javascript-jest.md` |
| Scala + MUnit | `../test-unit-standards/references/scala-munit.md` |

## Step 2 — Read test file completely

Read entire file first. Note: unit under test, test count, imports, dependencies touched.

## Step 3 — Run tests if available

| Language | Command |
|---|---|
| Python | `pytest <test-file> -v` |
| TypeScript | `npx jest <test-file> --no-coverage` |
| Scala | `./mvnw test -pl <module> -Dtest=<TestClass>` |
| .NET | `dotnet test --filter "FullyQualifiedName~<TestClass>"` |

**Failing tests = Blocker** (regardless of style). Continue standards check even if all pass.

## Step 4 — Check against standards

Work through each standard from `../test-unit-standards/SKILL.md` in order.
For each category, list every violation found before moving to the next.

### 4.1 Isolation

- Real external I/O? (network calls, file reads/writes, real DB connections)
- Shared mutable state between tests?
- Tests that depend on execution order?

### 4.2 Scope

- Private members accessed (see language reference for the convention)?
- Test bypassing the public API to reach internal state?

### 4.3 Naming

- Does each test name clearly state unit, condition, and expected outcome?
- Apply the naming format from the language reference

### 4.4 Assertion quality

- Weak assertions (`assert result`, `assert result is not None`) where exact value known?
- Missing assertions (test body with no assert)?
- Side-effect assertions using manual truthy instead of framework matcher?
- **Note:** `pytest.approx` is **correct** for floats — do not flag. It is a specific assertion that verifies the value within a tolerance, stronger than truthy or `is not None` checks and kills arithmetic operator mutants. Only flag genuine weak assertions.

### 4.5 Coverage

- Success path per behaviour?
- Failure path per behaviour?
- Boundary values (zero, empty, None/null, max)?

### 4.6 Fixtures

- Setup code copy-pasted across tests?
- Shared fixtures lacking docstring?

## Step 5 — Report findings

Group by severity. Cite test name, line, rule, fix suggestion. Empty sections show `(none)`. End with a line confirming overall compliance or summarizing blockers/important issues.

### Blocker

Broken tests, real I/O calls, or shared state (suite unreliable/order-dependent).

### Important

Missing failure/boundary coverage, weak/absent assertions, private member access, copy-pasted setup, unreadable naming.

### Nit

Minor naming inconsistencies, missing fixture docstrings, style issues.

**Explicitly confirm compliance** for each category checked when no violations found.
