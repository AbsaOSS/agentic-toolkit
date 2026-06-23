# Unit Test Review — Evals Fixture Map

Links each eval test case to its fixture file(s).

| Test ID | Category       | Fixture |
|---------|----------------|---------|
| 1       | happy-path     | evals/files/compliant-auth-service-tests.py |
| 2       | multi-violation | evals/files/multi-violation-report-tests.py |
| 3       | regression     | evals/files/missing-coverage-subscription-tests.py |
| 4       | negative       | *(no file — write request routed away)* |
| 5       | negative       | *(no file — runtime debugging question)* |

## Fixture → Rule mapping

| Fixture file | Primary category exercised |
|---|---|
| compliant-auth-service-tests.py | All six categories — no violations (confirms reviewer does not fabricate) |
| multi-violation-report-tests.py | All six categories — isolation, scope, naming, assertions, coverage, fixtures |
| missing-coverage-subscription-tests.py | Coverage completeness and weak assertions |

## Coverage summary

- happy-path: 1
- multi-violation: 1
- regression: 1
- negative: 2
- **total: 5**

## Trigger eval coverage

| Direction | Count |
|---|---|
| should_trigger = true | 11 |
| should_trigger = false | 6 |
| **total** | **17** |
