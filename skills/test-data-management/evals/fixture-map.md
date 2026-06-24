# Test Data Management — Evals Fixture Map

Links each eval test case to its fixture file(s).

| Test ID | Category   | Fixture |
|---------|------------|---------|
| 1       | happy-path | evals/files/separate-variation-tests.py |
| 2       | regression | evals/files/copy-paste-data-setup.py |
| 3       | happy-path | *(no file — production data policy question)* |
| 4       | happy-path | *(no file — timestamp determinism question)* |
| 5       | negative   | *(no file — double selection routed away)* |

## Fixture → Scenario mapping

| Fixture file | Scenario exercised |
|---|---|
| separate-variation-tests.py | Six test functions testing the same logic → collapse to parametrize; two failure tests correctly remain separate |
| copy-paste-data-setup.py | Repeated Package construction → extract factory function; non-deterministic datetime.now() → patch to fixed value |

## Coverage summary

- happy-path: 3
- regression: 1
- negative: 1
- **total: 5**

## Trigger eval coverage

| Direction | Count |
|---|---|
| should_trigger = true | 12 |
| should_trigger = false | 4 |
| **total** | **16** |
