---
name: test-unit-write
description: >
  Write unit tests from scratch or extend partial coverage for functions, classes, or modules.
  Activate when the user asks to write, generate, add, or scaffold unit tests — including
  partial coverage requests like "add failure-path tests" or "add boundary tests". Also
  activates for "help me test this" and "what tests should I write for X?".
  Triggers on: "write unit tests for", "add tests for", "generate test cases for",
  "help me test this", "I need unit tests", "add failure-path coverage", "add edge case tests",
  "add boundary tests", "test this method", "generate test", "what tests should I write".
  Does NOT trigger for: reviewing existing tests (use test-unit-review), asking about
  test conventions (use test-unit-standards), choosing test doubles (use test-mocking-patterns),
  managing test data (use test-data-management), debugging failing tests at runtime,
  integration or e2e test planning, or general code refactoring.
  Pairs with test-unit-standards (reference) and test-mocking-patterns (test-double selection).
license: Apache-2.0
compatibility: GitHub Copilot
---

# Unit Test Writer

**For reviewing tests**, use **test-unit-review**. **For test doubles**, use **test-mocking-patterns**.

## Step 1 — Load language reference

Identify language/framework from file extension, imports, build files. Load reference:

| Language / framework | Reference file |
|---|---|
| Python + pytest | `../test-unit-standards/references/python-pytest.md` |
| JavaScript / TypeScript + Jest | `../test-unit-standards/references/javascript-jest.md` |
| Scala + MUnit | `../test-unit-standards/references/scala-munit.md` |

Apply language-specific naming, fixture, assertion guidance throughout.

## Step 2 — Analyse source

Read file. Identify:
- Public API (functions, methods, constructors)
- Dependencies (args, services, modules)
- I/O boundaries (HTTP, DB, files, env, clock, randomness)
- Return values & side effects
- Failure conditions (exceptions, guards, errors)

**Do not write tests yet.**

## Step 3 — Choose mock strategy

| Dependency | Strategy |
|---|---|
| HTTP / API | Stub with canned response |
| DB / ORM / repo | Stub repo/DAO layer |
| File I/O | Stub in-memory or `tmp_path` |
| Env vars | Monkeypatch at boundary |
| Clock | Inject/patch to fixed datetime |
| Randomness / UUID | Patch deterministically |
| Pure helpers | Call real implementation |

**Unsure on mock vs stub vs spy vs fake?** Consult **test-mocking-patterns**.

## Step 4 — Scaffold test file

1. Determine file location (language reference)
2. Write imports (framework, mocking, unit under test)
3. Declare shared fixtures for mocks (Step 3)
4. Document fixture purpose & side effects

**Do not write test functions yet.**

## Step 5 — Write test cases

Order: 1) Happy path, 2) Failure paths (≥1 per behaviour), 3) Edge/boundary cases (empty, zero, None, max/min).

**Extending existing file:** Add only new tests; do not modify/remove existing.

Per test:
- Name per language reference
- Docstring: scenario in plain language
- Public interface only, no private access
- One logical behaviour (multiple asserts OK if collectively confirm single outcome)
- **One test per exception type + condition** — do not combine invalid inputs. Each deserves own test. Exception: a single boundary path may cover the last valid and first invalid value together (e.g. `amount == total` succeeds, `amount > total` raises). Use `pytest.raises` context manager; use `pytest.mark.parametrize` for many inputs.

## Step 6 — Assert correctly

Verify per language reference:
- No `is not None` / `toBeDefined()` / `assert result` where exact value known
- Exception tests assert specific type & message (where meaningful)
- Side-effect assertions use framework matcher, not manual truthy
- Float comparisons use approximate matcher

## Step 7 — Run and validate

1. Run test suite
2. Confirm all new tests pass
3. Fix before returning if any fail — no broken tests returned
4. If runner unavailable, state explicitly and note tests unverified

## Demo format (format/structure examples)

For *"show what tests look like"* requests:
- Names: `test_<unit>_<condition>_<expected>`
- One-line docstring per test
- Fixtures via `@pytest.fixture` with `MagicMock()`
- **Exactly one `assert` or `pytest.raises()`** — keep minimal/focused. Real files may have multiple asserts (see Step 5).

