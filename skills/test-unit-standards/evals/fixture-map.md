# Unit Test Standards — Evals Fixture Map

Links each eval test case to its fixture file(s).

`test-unit-standards` is the reference layer: it answers questions about test
conventions and rules. It does not write tests (see `test-unit-write`) or audit
specific test files (see `test-unit-review`), so most evals are file-free Q&A.

| Test ID | Category   | Fixture |
|---------|------------|---------|
| 1       | reference  | *(no file — standards checklist Q&A)* |
| 2       | reference  | *(no file — private member rule Q&A)* |
| 3       | reference  | *(no file — naming + asserts-per-test Q&A)* |
| 4       | reference  | *(no file — failure-path/boundary rule Q&A)* |
| 5       | reference  | *(no file — fixture placement/docs Q&A)* |
| 6       | edge-case  | *(no file — tmp_path guidance)* |
| 7       | edge-case  | *(no file — multiple-asserts guidance)* |
| 8       | negative   | *(no file — docstring task)* |
| 9       | negative   | evals/files/mixed-source-and-tests.py |
| 10      | negative   | *(no file — review request routed to test-unit-review)* |

## Fixture → purpose mapping

| Fixture file | Purpose |
|---|---|
| mixed-source-and-tests.py | Scope note — non-test (source refactor) task must not trigger standards enforcement |

## Coverage summary

- reference: 5
- edge-case: 2
- negative: 3
- **total: 10**

## Trigger eval coverage

| Direction | Count |
|---|---|
| should_trigger = true | 10 |
| should_trigger = false | 16 |
| **total** | **26** |

## Notes

Behavioral review/audit fixtures (private member access, naming, weak assertions,
copy-paste fixtures, real I/O, missing docstrings, framework idiom misuse) were
migrated to `test-unit-review/evals/files/` when this skill was narrowed to a pure
reference layer. The review skill owns file-audit behaviour and those fixtures back
its single-category regression evals.
