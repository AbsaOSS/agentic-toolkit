# Fixture Map — living-doc-gap-finder

## Fixture files

| File | Description |
|---|---|
| `evals/files/catalog-snapshot.json` | Snapshot of the living doc catalog + webapp inventory showing: 8 uncovered ACs (including 5 critical), 1 undocumented screen, 1 orphan Feature, 2 orphan tests, 5 Functionality ACs with no linked tests |

## Eval to fixture mapping

| Eval ID | Category | Fixture file(s) | Coverage |
|---|---|---|---|
| 1 | happy-path | `catalog-snapshot.json` | Full gap analysis: all 5 gap types detected, gap report with severity levels, coverage % calculation |
| 2 | happy-path | _(none)_ | Coverage metric explanation and calculation |
| 3 | happy-path | _(none)_ | Orphan test resolution: link or create Functionality, never delete |
| 4 | regression | _(none)_ | Batch processing advice: domain-by-domain, prioritise by business risk |
| 5 | negative | _(none)_ | Routing: creating a User Story → living-doc-create-user-story |

## Trigger eval summary

14 entries: 11 `should_trigger=true`, 3 `should_trigger=false`

| Routes to | Query count |
|---|---|
| living-doc-create-user-story | 1 |
| living-doc-create-feature | 1 |
| living-doc-tutorial-creator | 1 |
