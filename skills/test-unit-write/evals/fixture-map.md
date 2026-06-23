# Unit Test Write — Evals Fixture Map

Links each eval test case to its fixture file(s).

| Test ID | Category  | Fixture |
|---------|-----------|---------|
| 1       | happy-path  | evals/files/source-order-service.py |
| 2       | happy-path  | evals/files/source-price-calculator.py |
| 3       | extension   | evals/files/partial-happy-path-only.py |
| 4       | negative    | evals/files/partial-happy-path-only.py |
| 5       | negative    | *(no file — double-selection question)* |

## Fixture → Scenario mapping

| Fixture file | Scenario exercised |
|---|---|
| source-order-service.py | Write full test suite from scratch; two deps to stub; multiple failure paths |
| source-price-calculator.py | Write tests for a class with HTTP dep and env var; promo code path adds extra double |
| partial-happy-path-only.py | Extend existing tests with failure and boundary coverage without modifying existing tests |

## Coverage summary

- happy-path: 2
- extension: 1
- negative: 2
- **total: 5**

## Trigger eval coverage

| Direction | Count |
|---|---|
| should_trigger = true | 10 |
| should_trigger = false | 8 |
| **total** | **18** |
