# Living Doc Update Skill

The `living-doc-update` skill helps you amend living documentation entities: add Acceptance Criteria, change ownership, update status, link entities, and deprecate outdated behaviors. All changes propagate through the traceability system.

---

## What it does

The skill updates and validates entity changes:

| Operation | Effect |
|-----------|--------|
| **Add/modify/remove AC** | Version tracked; may trigger scenario sync |
| **Change status** | draft → ready → in_review → deprecated |
| **Change ownership** | Update team responsible for entity |
| **Link entities** | Connect User Stories to Features, Functionalities to Features |
| **Deprecate entity** | Tag dependent scenarios `@deprecated`; cleanup triggered |

---

## When to trigger it

```
update user story
add acceptance criteria to user story
descope this AC
deprecate feature
mark user story ready
change feature owner
update functionality
link user story to feature
change entity status
```

---

## Update types & propagation

| Type | Downstream skill |
|------|------------------|
| **Add AC** | None — create scenarios via [Living Doc Scenario Creator](./living-doc-scenario-creator.md) |
| **Modify AC** | [Gherkin ↔ Living Doc Sync](./gherkin-living-doc-sync.md) to sync scenarios |
| **Descope AC** | Gherkin sync tags scenarios `@deprecated` |
| **Deprecate entity** | [BDD Maintain](./bdd-maintain.md) removes test files |
| **Change status to ready** | Scenario creation enabled |

---

## Related skills

- [Living Doc Scenario Creator](./living-doc-scenario-creator.md) — write scenarios from new/modified ACs
- [Gherkin ↔ Living Doc Sync](./gherkin-living-doc-sync.md) — sync scenarios when ACs change
- [BDD Maintain](./bdd-maintain.md) — clean up tests after deprecation
- [Living Doc Impact Analysis](./living-doc-impact-analysis.md) — see impact of changes

---

## Helper scripts

One Python utility available in `skills/living-doc-update/scripts/`:
- **validate_entity.py** — validate entity structure and state transitions during updates

---

## Testing Evals

This skill has been validated with **16 test cases** covering:
- Adding/modifying/removing ACs
- Status transitions (draft → ready → deprecated)
- Ownership changes and notifications
- Entity linking workflows
- Propagation to downstream skills
