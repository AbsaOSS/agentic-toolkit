---
name: tdd-workflow
description: >
  Test-driven development (TDD) workflow for implementing and modifying code using vertical slicing
  (one test → one implementation cycle at a time). ALWAYS use this skill when a user needs to write
  new code, fix bugs, implement features, design systems, or add functionality — even without
  mentioning TDD explicitly. This applies to: implementing features, fixing bugs, adding functionality,
  building utilities, designing modules, capturing edge cases, planning test scenarios, documenting
  design decisions, and adding test coverage. Provides: SPEC.md planning, systematic edge case
  discovery, explicit test tables, confirmation gates, tracer bullets, and incremental red-green-refactor
  cycles. Does NOT apply to: asking what-is questions about TDD, understanding TDD concepts, reviewing
  completed tests, analyzing test suites, or refactoring when all tests pass.
---

# TDD Workflow

Write tests before code, always. SPEC.md is a session scratchpad — never commit it.

## Philosophy

**Test behavior, not implementation.** Tests verify capabilities through public interfaces. A good test reads like a spec: "refund 30 of 100, leaving 70 refundable." These survive refactors; implementation doesn't.

**Vertical slicing:** One test → implement → repeat. Each cycle learns from the last. ✅  
**Horizontal slicing (anti-pattern):** Write all tests, then all code. Produces speculative, brittle tests. ❌

## Step 1 — Create SPEC.md

Write a specification in the relevant package directory. Complete all sections:

- **Purpose:** What does this do? Why does it exist?
- **Scenarios:** Table with 3-5+ concrete cases (inputs → expected outputs)
- **Edge Cases:** Systematic list covering: input validation, boundaries, format variations, state transitions, preconditions
- **Out of Scope:** What this does NOT handle
- **Open Questions:** Unresolved design decisions

**Do not proceed until all sections are complete.** SPEC.md is your test-first blueprint.

---

## Step 2 — Test Table & Confirmation Gate

Create a test case table from your scenarios:

| # | Name | Intent | Input | Output |
|---|------|--------|-------|--------|
| 1 | test_name | goal | inputs | expected result |

**Each row must be specific enough to write a test from it without questions.** Bad: "handles refunds". Good: "refund 30 of 100, leaving 70 refundable".

### ⚠️ CONFIRMATION GATE

**STOP. DO NOT CODE YET.**

Present the test table. Ask the user:
- Does this cover the requirements?
- Add, remove, or change any cases?
- Is each case specific enough?

Only proceed when the user confirms "Yes, this is our test plan."

Record any key design decisions now (error handling approach, data types, state management).

---

## Step 3 — Tracer Bullet (First Test → First Implementation)

Start with your first test from the confirmed table. This is your tracer bullet—it proves the path works end-to-end.

**Red phase:**

1. Write ONE test for the first scenario
2. Give it a clear docstring explaining its behavior
3. Run it. It should fail (code doesn't exist yet)

**Green phase (immediately after):**

1. Write the minimum code to make this test pass
2. Do not add speculative features or handle other test cases
3. Run the full suite—this test should pass, others should not yet exist
4. Do not refactor yet—focus only on passing this test

**Key rule:** One test at a time. You just proved the path works. Move to the next test.

---

## Step 4 — Incremental Loop (Repeat for Each Remaining Test)

For each remaining scenario in your confirmed test table:

1. **Write ONE test** for the next scenario → run → fails
2. **Write minimum code** to pass this test → run → passes (should not break previous tests)
3. **Do not anticipate** future tests — only handle what this test requires
4. **Run full suite** after each cycle to confirm you haven't broken anything

Repeat: test → code → pass → test → code → pass...

Once all tests from your confirmed table pass, the incremental loop is done.

---

## Step 5 — Refactor Phase (Clean Up)

Only after ALL tests pass, now improve the code:

- Extract duplication
- Improve naming
- Simplify logic
- Organize structure
- Consider deeper modules (small interface, deep implementation)

**Rules:**
- Never refactor while RED (tests failing)
- Run full test suite after every change
- If a test fails, revert immediately
- If refactoring reveals new behaviors, pause and write tests for them

---

## Step 6 — Done

SPEC.md served its purpose. Do not update it unless the user asks to keep it.

---

## Pre-Code Checklist

Before you write the first test (Step 3), verify:

- [ ] SPEC.md complete (Purpose, Scenarios, Edge Cases, Out of Scope, Open Questions)
- [ ] Test table created and shown to user
- [ ] User confirmed test table ← **This is the gate**
- [ ] Edge cases identified
- [ ] Design decisions documented
- [ ] Test table is specific (no vague summaries — "handles refunds" → "refund 30 of 100, leaving 70 refundable")
- [ ] No implementation code written
- [ ] Tests will verify behavior through public interface only (not private methods or internal structure)
- [ ] Ready to write first test (tracer bullet)

**If any box is unchecked, do not proceed.**

---

## Core Rules

- **Do not code before confirming the test table** — this is the #1 pitfall. Design first, code second.
- **Do not commit SPEC.md** — it's a session scratchpad, not a deliverable.
- **Do not access private class members in tests** — it couples tests to implementation and breaks on refactors.
- **Do not mock internal collaborators** — test through the public interface or the behavior is implementation-specific.
- **One test at a time** — write one test, make it pass, refactor, then move to the next. Not all tests, then all code.
- **Test before code, always** — if you write implementation code, pause and write tests instead.
- **Use section separators in test files** — test names should be self-describing, no inline comments.
