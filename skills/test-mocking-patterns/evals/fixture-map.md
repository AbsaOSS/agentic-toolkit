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

## Fixture → Scenario mapping

| Fixture file | Scenario exercised |
|---|---|
| source-email-notification-service.py | Classify three different dependency types (HTTP query → stub, SMTP command → mock, metrics → mock/dummy) |
| wrong-patch-target.py | Diagnose wrong patch namespace; provide correct target |
| source-audit-service.py | Spy vs mock decision for an injected external dependency with internal formatting |

## Coverage summary

- happy-path: 3
- regression: 1
- negative: 2
- **total: 6**

## Trigger eval coverage

| Direction | Count |
|---|---|
| should_trigger = true | 13 |
| should_trigger = false | 5 |
| **total** | **18** |
