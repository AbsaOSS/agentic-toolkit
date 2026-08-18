# Test Mocking Patterns — Evals Fixture Map

Links each eval test case to its fixture file(s).

| Test ID | Category     | Fixture |
|---------|--------------|---------|
| 1       | happy-path   | evals/files/source-email-notification-service.py |
| 2       | regression   | evals/files/wrong-patch-target.py |
| 3       | happy-path   | evals/files/source-audit-service.py |
| 4       | happy-path   | *(no file — env var patching question)* |
| 5       | negative     | evals/files/source-email-notification-service.py |
| 6       | negative     | *(no file — test review request)* |
| 7       | paraphrase   | *(no file — database isolation question)* |
| 8       | edge-case    | *(no file — from...import patch target question)* |
| 9       | output-format | *(no file — stub vs mock code output format)* |
| 10      | happy-path   | *(no file — Jest clearAllMocks question)* |
| 11      | edge-case    | *(no file — don't mock what you don't own / boto3)* |
| 12      | happy-path   | *(no file — freezegun datetime mocking)* |

## Fixture → Scenario mapping

| Fixture file | Scenario exercised |
|---|---|
| source-email-notification-service.py | Classify three different dependency types (HTTP query → stub, SMTP command → mock, metrics → mock/dummy); negative routing for test-unit-write |
| wrong-patch-target.py | Diagnose wrong patch namespace; provide correct target |
| source-audit-service.py | Spy vs mock decision for an injected external dependency with internal formatting |

## Coverage summary

- happy-path: 5 (1, 3, 4, 10, 12)
- regression: 1 (2)
- negative: 2 (5, 6)
- paraphrase: 1 (7)
- edge-case: 2 (8, 11)
- output-format: 1 (9)
- **total: 12**

## Trigger eval coverage

| Direction | Count |
|---|---|
| should_trigger = true | 15 |
| should_trigger = false | 6 |
| **total** | **21** |
