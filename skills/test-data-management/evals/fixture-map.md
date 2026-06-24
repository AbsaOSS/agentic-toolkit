# Test Data Management — Evals Fixture Map

Links each eval test case to its fixture file(s).

| Test ID | Category     | Fixture |
|---------|--------------|---------|
| 1       | happy-path   | evals/files/separate-variation-tests.py |
| 2       | regression   | evals/files/copy-paste-data-setup.py |
| 3       | happy-path   | *(no file — production data policy question)* |
| 4       | happy-path   | *(no file — timestamp determinism question)* |
| 5       | negative     | *(no file — double selection routed away)* |
| 6       | paraphrase   | *(no file — cross-test coupling / factory question)* |
| 7       | edge-case    | *(no file — composable nested factories)* |
| 8       | output-format| *(no file — factory output format check)* |
| 9       | happy-path   | *(no file — integration test cleanup strategies)* |
| 10      | edge-case    | *(no file — TypeScript/Jest parametrize)* |

## Fixture → Scenario mapping

| Fixture file | Scenario exercised |
|---|---|
| separate-variation-tests.py | Six test functions testing the same logic → collapse to parametrize; two failure tests correctly remain separate |
| copy-paste-data-setup.py | Repeated Package construction → extract factory function; non-deterministic datetime.now() → patch to fixed value |

## Coverage summary

- happy-path: 4
- regression: 1
- negative: 1
- paraphrase: 1
- edge-case: 2
- output-format: 1
- **total: 10**

## Trigger eval coverage

| Direction | Count |
|---|---|
| should_trigger = true | 14 |
| should_trigger = false | 5 |
| **total** | **19** |
