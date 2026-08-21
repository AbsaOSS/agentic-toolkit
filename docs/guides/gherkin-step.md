# Gherkin Step Definitions Skill

The `gherkin-step` skill generates and reviews step definitions for Gherkin scenarios. It supports Python behave, TypeScript/Java/Scala Cucumber, handling state sharing, parameter types, DataTable parsing, and PageObject wiring.

---

## What it does

The skill produces idiomatic step definition code:

| Output | Description |
|--------|-------------|
| **Step function stubs** | Ready-to-implement with proper signatures and docstrings |
| **Imports & setup** | Language-specific fixture initialization |
| **Parameter types** | Custom types for parsing step text (e.g., `date`, `user_role`) |
| **Anti-pattern review** | Detects hardcoded selectors, global state, missing isolation |

---

## When to trigger it

```
implement these step definitions
write step code for my Gherkin scenarios
review step definitions for anti-patterns
how do I wire a PageObject into a step?
implement steps in Python behave
help with parameter types in Cucumber
how do I share state between steps safely?
```

---

## Supported frameworks

| Language | Framework | State model |
|----------|-----------|-------------|
| Python | behave | World object + context |
| TypeScript | Cucumber | Step definitions + fixtures |
| Java | Cucumber | Hooks + dependency injection |
| Scala | Cucumber-Scala | Regex capture groups |

---

## Related skills

- [Living Doc Scenario Creator](./living-doc-scenario-creator.md) — write the scenarios
- [Living Doc PageObject Scan](./living-doc-pageobject-scan.md) — create PageObjects
- [Data-Cy Instrument](./data-cy-instrument.md) — add test IDs for selectors

---

## Testing Evals

This skill has been validated with **18 test cases** covering:
- Python behave step implementations
- Cucumber TypeScript/Java steps
- Cucumber-Scala bindings
- Parameter types and DataTable parsing
- Before/After hook setup
- World/context state sharing
