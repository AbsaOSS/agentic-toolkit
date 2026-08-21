# Living Doc Scenario Creator Skill

The `living-doc-scenario-creator` skill generates Gherkin scenarios and `.feature` files directly from User Story and Functionality Acceptance Criteria, with full traceability via `@AC:` tags.

---

## What it does

The skill produces complete feature files:

| Output | Description |
|--------|-------------|
| **Scenarios** | One scenario per AC (or Scenario Outline for variations) |
| **Feature file** | Header with entity ID, status, description |
| **Traceability tags** | `@AC:` tags linking each scenario to its AC |
| **Coverage report** | Which ACs are covered, which are pending |

---

## When to trigger it

```
write gherkin scenarios for this acceptance criteria
generate feature file from user story
create scenarios from functionality
BDD scenarios for...
scenario from AC
standalone feature file
```

---

## Two modes

| Mode | Input | Output |
|------|-------|--------|
| **Entity mode** | US or Functionality with ACs | Complete feature file; all ACs → scenarios |
| **Standalone** | Business description (no entity) | Feature file with `@AC:STANDALONE` tags |

---

## Related skills

- [Living Doc Create User Story](./living-doc-create-user-story.md) — write the User Story first
- [Living Doc Create Functionality](./living-doc-create-functionality.md) — write the Functionality first
- [Gherkin Step Definitions](./gherkin-step.md) — implement the steps
- [Living Doc PageObject Scan](./living-doc-pageobject-scan.md) — create PageObjects
- [Gherkin ↔ Living Doc Sync](./gherkin-living-doc-sync.md) — maintain scenarios and ACs in sync
- [Data-Cy Instrument](./data-cy-instrument.md) — add missing `data-cy` attributes

---

## Helper scripts

One Python utility available in `skills/living-doc-scenario-creator/scripts/`:
- **coverage_report.py** — generate AC coverage report showing scenario-to-AC mapping

---

## Testing Evals

This skill has been validated with **21 test cases** covering:
- Entity mode: US and Functionality inputs
- Standalone mode: free-form scenarios
- Scenario Outline generation for variations
- AC traceability tag creation
- Coverage report accuracy
