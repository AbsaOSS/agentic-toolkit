# Unit Test Write — Evals Fixture Map

Links each eval test case to its fixture file(s).

| Test ID | Category  | Fixture |
|---------|-----------|---------|
| 1       | happy-path  | evals/files/source-order-service.py |
| 2       | happy-path  | evals/files/source-price-calculator.py |
| 3       | extension   | evals/files/partial-happy-path-only.py |
| 4       | negative    | evals/files/partial-happy-path-only.py |
| 5       | negative    | *(no file — double-selection question)* |
| 6       | paraphrase  | *(no file — informal phrasing)* |
| 7       | edge-case   | *(no file — structure guidance)* |
| 8       | output-format | *(no file — format documentation)* |
| 9       | regression  | *(no file — simple method guidance)* |
| 10      | happy-path  | evals/files/source-parametrized-discounts.py |

## Fixture → Scenario mapping

| Fixture file | Scenario exercised |
|---|---|
| source-order-service.py | Write full test suite from scratch; two deps to stub; multiple failure paths |
| source-price-calculator.py | Write tests for a class with HTTP dep and env var; promo code path adds extra double |
| partial-happy-path-only.py | Extend existing tests with failure and boundary coverage without modifying existing tests |
| source-parametrized-discounts.py | Use pytest.mark.parametrize to cover multiple tiers and values; avoid test duplication |

## Coverage summary

- happy-path: 3
- extension: 1
- negative: 2
- paraphrase: 1
- edge-case: 1
- output-format: 1
- regression: 1
- **total: 10**

## Trigger eval coverage

| Direction | Count |
|---|---|
| should_trigger = true | 10 |
| should_trigger = false | 11 |
| **total** | **21** |
