# Gherkin ↔ Living Doc Sync Skill

The `gherkin-living-doc-sync` skill keeps Gherkin scenarios and Acceptance Criteria synchronized. It detects drifting links, missing `@AC:` tags, step text mismatches, and propagates AC changes from the catalog back to feature files.

---

## What it does

The skill audits traceability and produces sync reports:

| Output | Description |
|--------|-------------|
| **AC link audit** | Finds missing `@AC:` tags, stale links, orphaned scenarios |
| **Step text drift** | Flags scenarios where step text diverged from AC descriptions |
| **Deprecation tagging** | Tags scenarios `@deprecated` when ACs are descoped |
| **AC change propagation** | Maps AC edits back to affected scenarios |

---

## When to trigger it

```
sync gherkin to living doc
feature file out of sync
scenario not linked to AC
step text changed
gherkin drift
AC link missing in feature file
BDD sync
traceability broken
propagate AC changes
AC was descoped
```

---

## What it audits

- `@AC:` tag presence and validity
- AC status alignment (active vs. deprecated)
- Scenario coverage (is every scenario linked?)
- Step text alignment with AC descriptions
- Orphaned scenarios (no AC link)
- Stale links (AC deleted, scenario still tagged)

---

## Related skills

- [Living Doc Scenario Creator](./living-doc-scenario-creator.md) — create scenarios from ACs
- [Living Doc Update](./living-doc-update.md) — edit AC descriptions
- [Living Doc Gap Finder](./living-doc-gap-finder.md) — find untested ACs
---

## Helper scripts

One Python utility available in `skills/gherkin-living-doc-sync/scripts/`:
- **scan_ac_links.py** — audit `@AC:` tag health and detect missing/stale links

---

## Testing Evals

This skill has been validated with **14 test cases** covering:
- AC link detection and validation
- Step text drift scenarios
- Deprecation tagging workflows
- AC change propagation