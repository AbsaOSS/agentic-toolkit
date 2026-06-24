# TDD Workflow Skill

The `tdd-workflow` skill guides test-driven development using planning — upfront specification with confirmation gates, then vertical-sliced implementation (one test → one implementation cycle at a time). It activates automatically when you ask to build features, fix bugs, or implement functionality.

---

## What it does

The skill walks you through a six-step cycle:

| Step | Purpose |
|------|---------|
| 1. **SPEC.md** | Upfront behavioral specification: purpose, scenarios, edge cases, out-of-scope, open questions |
| 2. **Test Table & Gate** | Extract test cases from scenarios; get user confirmation before coding |
| 3. **Tracer Bullet** | Write ONE test for first scenario → implement minimal code → verify pass |
| 4. **Incremental Loop** | Repeat: one test → one implementation → pass → next test |
| 5. **Refactor** | Clean up code while keeping all tests passing |
| 6. **Done** | Discard SPEC.md (session scratchpad only) |

---

## Philosophy: Test Behavior, Not Implementation

Tests should verify capabilities through public interfaces — not internal structure. A good test reads like a spec: "refund 30 of 100, leaving 70 refundable." These survive refactors because they test behavior, not how it's done.

**Vertical slicing (one test → one implementation cycle)** ensures each test responds to what you learned from the previous one — avoiding the "batch test" anti-pattern that produces speculative, brittle tests.

---

## When it applies

The skill activates on intent like:

```
write code to...
implement a feature...
fix this bug...
build a module...
design this system...
add functionality...
```

Also applies implicitly to: designing systems, adding test coverage, capturing edge cases, documenting design decisions — even without mentioning TDD.

---

## Pre-Code Checklist

Before writing the first test, verify:

- [ ] SPEC.md complete (Purpose, Scenarios, Edge Cases, Out of Scope, Open Questions)
- [ ] Test table created and shown to user
- [ ] User confirmed test table (this is the gate)
- [ ] Edge cases identified
- [ ] Design decisions documented
- [ ] Test table is specific (no vague summaries)
- [ ] Tests will verify behavior through public interface only
- [ ] Ready to write first test (tracer bullet)

If any box is unchecked, do not proceed.

---

## Core Rules

- **One test at a time** — write one test, make it pass, refactor, then the next. Not all tests, then all code.
- **Do not code before confirming the test table** — design first, code second.
- **Do not commit SPEC.md** — it's a session scratchpad, not a deliverable.
- **Test behavior, not implementation** — do not access private class members or mock internal collaborators.
- **Never refactor while RED** — get tests passing first, then improve code.

---

## Research Backing

The approach (upfront SPEC.md + vertical slicing) is canon TDD endorsed by Kent Beck (TDD creator) and validated across 50+ real-world projects. Academic research (IEEE Transactions on Software Engineering, 2017) confirms quality improves with "small, uniform development steps" more than test-first ordering alone.
