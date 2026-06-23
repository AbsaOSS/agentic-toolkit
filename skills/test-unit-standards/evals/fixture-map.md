# Unit Test Standards — Evals Fixture Map

Links each eval test case to its fixture file(s).

| Test ID | Category | Fixture |
|---|---|---|
| 1 | happy-path | evals/files/compliant-payment-tests.py |
| 2 | regression | evals/files/real-io-violations.py |
| 3 | regression | evals/files/private-member-access.py |
| 4 | regression | evals/files/weak-assertions-no-failure.py |
| 5 | regression | evals/files/copy-paste-setup.py |
| 6 | regression | evals/files/bad-naming-missing-boundaries.py |
| 7 | happy-path | evals/files/source-discount-calculator.py |
| 8 | negative | *(no file — docstring task)* |
| 9 | paraphrase | evals/files/real-io-violations.py |
| 10 | multi-violation | evals/files/multi-violation-audit.py |
| 11 | regression | evals/files/shared-mutable-state.py |
| 12 | regression | evals/files/missing-docstrings-stray-comments.py |
| 13 | negative | evals/files/mixed-source-and-tests.py |
| 14 | paraphrase | *(no file — informal phrasing)* |
| 15 | edge-case | *(no file — tmp_path guidance)* |
| 16 | output-format | *(no file — format documentation)* |
| 17 | regression | evals/files/framework-idiom-misuse.py |

## Fixture → Rule mapping

| Fixture file | Primary rule(s) exercised |
|---|---|
| compliant-payment-tests.py | All rules — no violations (reference implementation) |
| real-io-violations.py | Isolation — real I/O (filesystem, HTTP, DB) |
| private-member-access.py | Scope — private member access |
| weak-assertions-no-failure.py | Assertion completeness, boundary values |
| copy-paste-setup.py | Fixture management |
| bad-naming-missing-boundaries.py | Naming conventions, boundary values |
| source-discount-calculator.py | All rules — write-from-scratch task |
| shared-mutable-state.py | Isolation — shared mutable state between tests |
| missing-docstrings-stray-comments.py | Naming/structure — docstrings required, no stray comments |
| mixed-source-and-tests.py | Scope note — non-test task must not trigger rule enforcement |
| multi-violation-audit.py | All rules — isolation, scope, naming, assertions, fixtures, boundaries |
| framework-idiom-misuse.py | Assertions — pytest.raises idiom (regex match parameter) |

## Coverage summary

- happy-path: 2
- regression: 8
- negative: 2
- paraphrase: 2
- multi-violation: 1
- edge-case: 1
- output-format: 1
- **total: 17**

## Trigger eval coverage

| Direction | Count |
|---|---|
| should_trigger = true | 12 |
| should_trigger = false | 18 |
| **total** | **30** |
