# Unit Test Review — Evals Fixture Map

Links each eval test case to its fixture file(s).

| Test ID | Category       | Fixture |
|---------|----------------|---------|
| 1       | happy-path     | evals/files/compliant-auth-service-tests.py |
| 2       | multi-violation | evals/files/multi-violation-report-tests.py |
| 3       | regression     | evals/files/missing-coverage-subscription-tests.py |
| 4       | negative       | *(no file — write request routed away)* |
| 5       | negative       | *(no file — runtime debugging question)* |
| 6       | paraphrase     | *(no file — informal phrasing)* |
| 7       | edge-case      | *(no file — pytest.approx guidance)* |
| 8       | output-format  | *(no file — format documentation)* |
| 9       | regression     | evals/files/flaky-shared-mock-state.py |
| 10      | regression     | evals/files/integration-test-in-unit-suite.py |

## Fixture → Rule mapping

| Fixture file | Primary category exercised |
|---|---|
| compliant-auth-service-tests.py | All six categories — no violations (confirms reviewer does not fabricate) |
| multi-violation-report-tests.py | All six categories — isolation, scope, naming, assertions, coverage, fixtures |
| missing-coverage-subscription-tests.py | Coverage completeness and weak assertions |
| flaky-shared-mock-state.py | Isolation — shared mutable state, order-dependent tests |
| integration-test-in-unit-suite.py | Isolation — real I/O (Kafka), integration test in unit suite |

## Coverage summary

- happy-path: 1
- multi-violation: 1
- regression: 3
- negative: 2
- paraphrase: 1
- edge-case: 1
- output-format: 1
- **total: 10**

## Trigger eval coverage

| Direction | Count |
|---|---|
| should_trigger = true | 11 |
| should_trigger = false | 8 |
| **total** | **19** |
