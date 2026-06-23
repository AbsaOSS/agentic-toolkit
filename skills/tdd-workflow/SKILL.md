---
name: tdd-workflow
description: >
  Test-driven development (TDD) workflow for implementing new code. Use this skill whenever
  the user wants to implement a feature, fix a bug, or add functionality — even without
  mentioning TDD explicitly. Enforces: SPEC.md-first specification with systematic edge
  case discovery, explicit test case confirmation with user review gates, and red-green-refactor
  cycle. Language-agnostic. Triggers on: "implement…", "I want to…", "fix the…", "add a…",
  "build a…", "write tests first", "TDD", "red-green-refactor", "unit tests before coding",
  "add test coverage", "design decisions before coding", "edge cases for…". Does NOT trigger
  for: conceptual/educational questions about TDD, reviewing existing tests, or refactoring
  code where all tests already pass.
---

# TDD Workflow

Write tests before code, always. SPEC.md is a session scratchpad — never commit it.

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

## Step 3 — Red Phase (Write Failing Tests)

Write all tests first. Code that compiles but fails:

1. Write tests in order: test 1 → test 2 → ... → test N
2. Each test has a clear docstring explaining its scenario
3. Cover every row in your confirmed test table
4. Do NOT implement code yet — only test code

Run the suite. Expect all/most tests to fail.

---

## Step 4 — Green Phase (Implement)

Implement the minimum code to pass tests:

1. Make test 1 pass → test 2 → test 3 ... (in order)
2. Each change makes one test pass without breaking others
3. Focus on passing tests, not refactoring
4. Run full suite after every change

Once all tests pass, Green phase is done.

---

## Step 5 — Refactor Phase (Clean Up)

Now improve the code while keeping tests passing:

- Extract duplication
- Improve naming
- Simplify logic
- Organize structure

Run full test suite after every change. If a test fails, revert.

---

## Step 6 — Done

SPEC.md served its purpose. Do not update it unless the user asks to keep it.

---

## Pre-Code Checklist

Before you write implementation code (Step 3), verify:

- [ ] SPEC.md complete (Purpose, Scenarios, Edge Cases, Out of Scope, Open Questions)
- [ ] Test table created and shown to user
- [ ] User confirmed test table ← **This is the gate**
- [ ] Edge cases identified
- [ ] Design decisions documented
- [ ] Test table is specific (no vague summaries)
- [ ] No implementation code written
- [ ] Ready for Red phase

**If any box is unchecked, do not proceed.**

---

## Core Rules

- **Do not code before confirming the test table** — this is the #1 pitfall. Design first, code second.
- **Do not commit SPEC.md** — it's a session scratchpad, not a deliverable.
- **Do not access private class members in tests** — it couples tests to implementation.
- **Test before code, always** — if you write implementation code, pause and write tests instead.
- **Use section separators in test files** — test names should be self-describing, no inline comments.
