# Unit Test Review — Evals Fixture Map

Links each eval test case to its fixture file(s).

| Test ID | Category        | Fixture |
|---------|-----------------|---------|
| 1       | happy-path      | evals/files/compliant-auth-service-tests.py |
| 2       | multi-violation | evals/files/multi-violation-report-tests.py |
| 3       | regression      | evals/files/missing-coverage-subscription-tests.py |
| 4       | negative        | *(no file — write request routed away)* |
| 5       | negative        | *(no file — runtime debugging question)* |
| 6       | paraphrase      | *(no file — informal phrasing)* |
| 7       | edge-case       | *(no file — pytest.approx guidance)* |
| 8       | output-format   | *(no file — format documentation)* |
| 9       | regression      | evals/files/flaky-shared-mock-state.py |
| 10      | regression      | evals/files/integration-test-in-unit-suite.py |
| 11      | regression      | evals/files/real-io-violations.py |
| 12      | regression      | evals/files/private-member-access.py |
| 13      | regression      | evals/files/weak-assertions-no-failure.py |
| 14      | regression      | evals/files/copy-paste-setup.py |
| 15      | regression      | evals/files/bad-naming-missing-boundaries.py |
| 16      | regression      | evals/files/missing-docstrings-stray-comments.py |
| 17      | edge-case       | evals/files/framework-idiom-misuse.py |

## Fixture → Rule mapping

| Fixture file | Primary category exercised |
|---|---|
| compliant-auth-service-tests.py | All six categories — no violations (confirms reviewer does not fabricate) |
| multi-violation-report-tests.py | All six categories — isolation, scope, naming, assertions, coverage, fixtures |
| missing-coverage-subscription-tests.py | Coverage completeness and weak assertions |
| flaky-shared-mock-state.py | Isolation — shared mutable state, order-dependent tests |
| integration-test-in-unit-suite.py | Isolation — real I/O (Kafka), integration test in unit suite |
| real-io-violations.py | Isolation — real I/O (filesystem, HTTP, DB) |
| private-member-access.py | Scope — private member access |
| weak-assertions-no-failure.py | Assertions — completeness, weak assertions, missing failure/boundary coverage |
| copy-paste-setup.py | Fixtures — copy-pasted setup, missing shared fixture |
| bad-naming-missing-boundaries.py | Naming conventions and boundary coverage |
| missing-docstrings-stray-comments.py | Naming/structure — docstrings required, no stray comments |
| framework-idiom-misuse.py | Assertions — pytest.raises idiom (regex match parameter) |

## Coverage summary

- happy-path: 1
- multi-violation: 1
- regression: 12
- negative: 2
- paraphrase: 1
- edge-case: 2
- output-format: 1
- **total: 20**

## Trigger eval coverage

| Direction | Count |
|---|---|
| should_trigger = true | 11 |
| should_trigger = false | 8 |
| **total** | **19** |

## Notes

Single-category fixtures 11–17 (real I/O, private member access, weak assertions,
copy-paste setup, bad naming, missing docstrings, framework idiom misuse) were
migrated from `test-unit-standards/evals/files/` when that skill was narrowed to a
pure reference layer. They give the review skill dedicated per-category regression
coverage alongside the existing multi-violation and compliant fixtures.
