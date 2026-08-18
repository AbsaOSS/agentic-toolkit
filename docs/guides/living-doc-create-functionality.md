# Living Doc Create Functionality Skill

The `living-doc-create-functionality` skill helps you define atomic, testable behaviors (Functionalities) with Acceptance Criteria for unit or integration tests. Functionalities are building blocks for Features—smaller and more granular than User Stories.

---

## What it does

The skill produces a Functionality entity:

| Output | Description |
|--------|-------------|
| **Atomic behavior** | Verb-phrase naming (e.g., "Calculate discount for membership tier") |
| **ACs** | Testable acceptance criteria scoped to unit/integration test level |
| **Test type** | Guidance on Unit vs. Integration vs. Component testing |
| **Feature link** | Parent Feature this Functionality belongs to |

---

## When to trigger it

```
create a functionality
document an atomic behavior
define behavior for unit test
component behavior AC
business rule definition
test type for this behavior
link functionality to feature
review this functionality
```

---

## Test types

| Type | Scope | Example |
|------|-------|---------|
| **Unit** | Single function/method | Discount calculation returns correct %; |
| **Integration** | Multiple components + state | Cart updates when item quantity changes |
| **Component** | UI component + logic | Modal opens/closes on button click |

---

## Related skills

- [Living Doc Create Feature](./living-doc-create-feature.md) — define the parent Feature
- [Living Doc Scenario Creator](./living-doc-scenario-creator.md) — write scenarios from ACs
- [Living Doc Update](./living-doc-update.md) — refine AC descriptions
- [Living Doc Gap Finder](./living-doc-gap-finder.md) — audit Functionality coverage

---

## Helper scripts

One Python utility available in `skills/living-doc-create-functionality/scripts/`:
- **next_id.py** — generate sequential Functionality entity IDs within a Feature

---

## Testing Evals

This skill has been validated with **16 test cases** covering:
- Functionality entity creation
- Test type selection (unit/integration/component)
- AC definition workflows
- Feature linkage validation
- Reuse candidate identification
