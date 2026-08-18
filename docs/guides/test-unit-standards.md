# Unit Test Standards

This skill defines comprehensive reference standards for unit testing across Python, JavaScript/TypeScript, and Scala.

## Quick Start

Ask the agent about unit test best practices:
- "What are our standards for unit test isolation?"
- "How should I name a test in pytest?"
- "What are the naming conventions for Jest tests?"
- "How do I structure fixtures properly?"

## What This Skill Does

**test-unit-standards** provides language-agnostic principles plus language-specific conventions for:

- **Isolation** — no real I/O, independent tests, no shared mutable state
- **Scope** — unit = one function/method/class, public interface only
- **Naming** — test names state scenario clearly
- **Assertions** — specific over generic, cover success + ≥1 failure path per behaviour
- **Coverage** — success paths, failure paths, boundary values (empty, zero, null, max)
- **Fixtures** — framework-idiomatic location, reusable, documented

## Language References

The skill loads language-specific guidance for:

| Language / Framework | Location |
|---|---|
| Python + pytest | `skills/test-unit-standards/references/python-pytest.md` |
| JavaScript / TypeScript + Jest | `skills/test-unit-standards/references/javascript-jest.md` |
| Scala + MUnit | `skills/test-unit-standards/references/scala-munit.md` |

## When To Use

- **Abstract questions**: "What are our standards?", "Best practices for X?", "Naming convention?"
- **Learning**: Understanding isolation rules, fixture reuse, coverage depth
- **Validation**: Confirming a test design before writing or reviewing

## Related Skills

- **[test-unit-write](./test-unit-write.md)** — Generate new tests following standards
- **[test-unit-review](./test-unit-review.md)** — Audit existing tests against standards
