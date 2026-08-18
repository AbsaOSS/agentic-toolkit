# Living Doc Impact Analysis Skill

The `living-doc-impact-analysis` skill traces code changes to your living documentation. Given a PR diff or refactored module, it identifies affected Features, Functionalities, and User Stories—and determines what must be reviewed, updated, or re-tested.

---

## What it does

The skill produces an impact map:

| Output | Description |
|--------|-------------|
| **Affected entities** | Features, Functionalities, User Stories touched by the change |
| **Traceability chain** | Code path → Feature → Behaviors → Scenarios |
| **Re-test plan** | Which scenarios must re-run; which need updates |
| **Coverage gaps** | Undocumented code paths |

---

## When to trigger it

```
what does this change affect?
PR impact on living doc
trace affected user stories
affected features
impact analysis
PR review for documentation
what needs re-testing?
bootstrap feature registry
```

---

## Supported patterns

The skill maps:

- Code module → Feature owner
- Feature → Functionalities (atomic behaviors)
- Functionalities → Scenarios (test coverage)
- User Story → Features (end-to-end flow)

---

## Related skills

- [Living Doc Update](./living-doc-update.md) — modify affected entities
- [Living Doc Scenario Creator](./living-doc-scenario-creator.md) — write scenarios for gaps
- [Living Doc Gap Finder](./living-doc-gap-finder.md) — audit coverage after changes
- [Gherkin ↔ Living Doc Sync](./gherkin-living-doc-sync.md) — sync affected scenarios

---

## Helper scripts

One Python utility available in `skills/living-doc-impact-analysis/scripts/`:
- **trace_impact.py** — trace code changes to living doc entities and compute impact

---

## Testing Evals

This skill has been validated with **15 test cases** covering:
- PR diff impact tracing
- Module refactoring impact mapping
- Traceability chain validation
- Re-test plan generation
- Coverage gap detection
