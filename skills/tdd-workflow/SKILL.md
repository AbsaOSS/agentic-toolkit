---
name: tdd-workflow
description: >
  Test-driven development (TDD) workflow for writing or changing production code. Use this
  skill whenever the user is about to implement a feature, add a function, fix a bug, or
  build new functionality — even if they never say "TDD." If new code will be written, this
  skill should take over. Enforces SPEC.md-first as a local scratchpad with systematic
  edge case discovery, explicit test table confirmation with user review gates, and the
  red–green–refactor cycle before implementation. Language-agnostic. Triggers on:
  "implement this feature using TDD," "write the tests first," "write failing tests first,"
  "unit tests before coding," "red-green-refactor," "TDD," "I want to implement…," "fix
  the … bug," "add a … function," "build a … utility/feature," "add test coverage before
  I add the new feature," "spec it out and write tests before touching the code," "what
  edge cases and boundary conditions should we test," "document design decisions before
  coding," "what test cases do we need for this feature." Does NOT trigger for: conceptual
  or educational questions about testing/TDD, reviewing an existing test suite for gaps, or
  pure refactors where tests already pass and no new behavior is being added.
---

# TDD Workflow

Enforce the red–green–refactor TDD cycle. SPEC.md is a local-only session scratchpad — never committed.

## Step 1 — Create & Complete SPEC.md

Create `SPEC.md` in the relevant package/module directory using `assets/SPEC_TEMPLATE.md`. **Complete the entire SPEC before moving forward.**

### SPEC.md Completion Checklist (All Required)
- ✓ **Purpose:** One clear paragraph explaining what the component does and why
- ✓ **Scenarios:** Detailed table with at least 3-5 scenarios covering happy path, rejections, edge cases
- ✓ **Edge Cases:** Explicit list of boundary conditions and failure modes (see patterns below)
- ✓ **Out of Scope:** Clear list of what this component does NOT handle
- ✓ **Open Questions:** Unresolved decisions that need input before implementation

**If any box is unchecked, do not proceed to Step 2.** SPEC.md is your test-first specification.

### Edge Case Discovery Patterns
Think systematically about each input/state. For each field:
- **Input validation:** What happens with empty, null, negative, zero, very large values?
- **Boundary conditions:** Smallest positive value? Largest supported? Off-by-one?
- **Format variations:** Spaces, dashes, trailing zeros, case sensitivity?
- **State transitions:** Can B happen before A? What's the valid sequence?
- **Precondition violations:** What if a required state doesn't exist?

**SPEC.md configuration:** This file is a session scratchpad — it must never be committed. It is ignored by default (already in `.gitignore`). If you want to keep it permanently, rename it and commit it explicitly.

---

## Step 2 — Build & Confirm Test Case Table

Create a test case table from your SPEC scenarios using this exact format:

| # | Test Name | Intent | Input Summary | Expected Output Summary |
|---|-----------|--------|---|---|
| 1 | name_of_test | one-line intent | describe inputs concisely | describe pass/fail concisely |
| 2 | ... | ... | ... | ... |

**Each entry must be specific enough that a developer can write a test from it without asking questions.** Avoid vague summaries like "handles refunds" — instead: "refund 30.00 of 100.00 approved payment, leaving 70.00 refundable."

### Confirmation Gate — MANDATORY PAUSE

**🛑 DO NOT CODE YET. WAIT FOR USER CONFIRMATION BEFORE PROCEEDING. 🛑**

Present the test table and ask the user:
- "Does this cover the requirements?"
- "Are there test cases you'd add, remove, or change?"
- "Is each case specific enough?"

Incorporate user feedback:
- Add cases if coverage gaps exist
- Remove cases if out of scope
- Clarify cases until specific
- **Re-present the table and ask again if changes were made**

Only when the user confirms "Yes, this is our test plan" do you proceed to Step 3.

### Design Decisions Record (Optional, Helpful)

Before moving to Step 3, capture key decisions:
```
## Design Decisions
- Error handling: [exception / result object / status code?] → Choose: _____
- Data representation: [type/format decisions] → Choose: _____
- [Other key assumption] → Choose: _____
```

This prevents rework later.

---

## Step 3 — Red Phase

Write all failing tests first. Write test code that compiles but does not pass. Follow this process:

1. **Order matters:** Implement test 1 → test 2 → test 3 ... → test N. This reveals missing functionality progressively.
2. **Each test must state its scenario:** Use clear docstrings/descriptions so anyone reading the test understands what case it covers.
3. **Cover all distinct inputs:** For each row in your confirmed test table, write one test.
4. **Do not implement yet:** Only test code. If you find yourself writing implementation code, stop and write test-only code.

Run the full test suite. **Expect all or most tests to fail** — that's the "Red" phase.

---

## Step 4 — Green Phase

Implement the minimum code to make tests pass. Follow this process:

1. **Implement test-by-test:** Make test 1 pass → test 2 → test 3 ... → test N.
2. **Minimal changes:** Each change should make one test pass without breaking others.
3. **Keep focus:** Ignore refactoring urges in this phase. Just make tests pass.
4. **Run full suite after each change:** Confirm no regressions as you go.

Once all tests pass, you've completed the Green phase.

---

## Step 5 — Refactor Phase

Clean up the now-passing implementation without changing observable behavior. Focus on:
- Extract duplication (helper methods, constants)
- Improve naming (variables, methods, classes)
- Simplify logic (reduce nesting, extract complex conditions)
- Organize code (group related methods, clarify intent)

**After every refactor change, run the full test suite.** If a test fails, revert and try a different refactor. The goal is code that is both correct *and* maintainable.

---

## Step 6 — Done

SPEC.md served its purpose as a scratchpad. Do not update it post-implementation unless the user explicitly asks to keep it.

---

## Pre-Code Checklist

Before you write a single line of implementation code (Step 3), verify:

- [ ] SPEC.md created with Purpose, Scenarios, Edge Cases, Out of Scope, Open Questions
- [ ] Test case table created and presented to user
- [ ] Test case table reviewed and approved by user (confirmation gate passed)
- [ ] Edge cases explicitly identified and categorized
- [ ] Design decisions documented (or deferred with rationale)
- [ ] Test table is specific enough — no vague summaries
- [ ] No implementation code written yet
- [ ] Ready to enter Red phase

**If any box is unchecked, do not proceed to Step 3 (Red phase).**

---

## Enforce these rules throughout

- **Do not start coding before the test table is confirmed** — jumping ahead short-circuits the design conversation and leads to tests written to fit code rather than the reverse. This is the #1 pitfall.
- **Do not commit SPEC.md** — it is a session scratchpad, not a deliverable; committing it creates noise and may expose unfinished thinking.
- **Do not access private members of the class under test in tests** — tests that reach into internals couple themselves to implementation details, making refactors fragile.
- **Prefer `# --- section ---` separators over inline comments in test files** — test names and docstrings should be self-describing; prose comments outside methods add clutter.
- **Test before code, always** — if you find yourself writing implementation code, pause and write test code instead. Every feature should have a failing test first.
