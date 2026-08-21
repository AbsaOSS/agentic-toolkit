# Test Data Management Skill

The `test-data-management` skill guides consistent, maintainable test data setup across unit and integration tests. It activates when the question is about _how_ to structure or supply data to tests — not about writing the tests themselves.

---

## What it covers

| Topic | Guidance |
|---|---|
| Parametrised tests | When to collapse repeated test functions into a single data-driven test |
| Factory / builder pattern | Default-value factories with keyword overrides; composable nested factories |
| Production data | Why to never use production data (even anonymised); generator-script pattern |
| Deterministic data | Injecting fixed timestamps; avoiding `datetime.now()` in test setup |
| Minimal data | Inline data for simple cases; external fixtures only for complex payloads |
| Integration test cleanup | Transaction rollback, truncation, test containers, run-scoped IDs |

---

## When it fires

The skill activates on intent — it does not require exact phrasing:

```
my test setup is duplicated everywhere
how do I avoid copy-pasting test data across 10 tests?
can I use production data in tests?
my test keeps breaking because the expected timestamp changes every run
how do I create a factory for test orders?
how should I seed data for integration tests?
how do I clean up after an integration test?
```

---

## When it does not fire

| Situation | Correct path |
|---|---|
| Choosing mock, stub, spy, or fake | Test mocking / doubles guide |
| Writing test logic and assertions | Test authoring guide |
| Reviewing tests for standards compliance | Test review guide |
| Debugging a test runtime error | General debugging |
| Configuring test infrastructure (containers, DBs) | Infrastructure / DevOps guide |

---

## Language support

The skill covers patterns for Python, TypeScript/JavaScript, Scala, Java, and .NET. Examples default to Python but the language table in the skill body maps each pattern to the idiomatic tool for each ecosystem.

---

## Evals

The skill ships with 10 functional evals (`evals/evals.json`) and 19 trigger evals (`evals/trigger-eval.json`). Run them to validate behaviour after edits — see [Skill Testing](../testing/skill-testing.md).

---

## Installation

See [Getting Started](../getting-started.md) for the full install guide.
