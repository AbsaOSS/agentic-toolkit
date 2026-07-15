# Fixture Map — living-doc-gap-finder

## Fixture files

| File | Description |
|---|---|
| `evals/files/catalog-snapshot.json` | Snapshot of the living doc catalog + webapp inventory showing: 8 uncovered US ACs, 5 uncovered Functionality ACs, 1 undocumented screen after normalisation, 2 orphan Features, 1 orphan User Story, 3 orphan tests, and 2 empty Features |
| `evals/files/gap-report.json` | Expected gap report output produced by compute_gaps.py before normalisation — used as reference for output-format eval |

## Eval to fixture mapping

| Eval ID | Category | Fixture file(s) | Coverage |
|---|---|---|---|
| 1 | happy-path | `catalog-snapshot.json` | Full gap analysis: all 9 gap types, severity levels, normalisation rules, coverage % |
| 2 | happy-path | _(none)_ | Coverage metric formula and separate US vs Functionality reporting |
| 3 | happy-path | _(none)_ | ORPHAN_TEST resolution: link or create Functionality, never delete |
| 4 | regression | _(none)_ | Batch processing advice: domain-by-domain, prioritise by business risk |
| 5 | negative | _(none)_ | Routing: creating a User Story → living-doc-create-user-story |
| 6 | paraphrase | _(none)_ | "Holes in living doc" → gap analysis framing |
| 7 | edge-case | _(none)_ | Broken-link orphan test: AC ID deleted from catalog |
| 8 | output-format | `gap-report.json` | Canonical gap report JSON: coverage section + gaps[] array structure |
| 9 | regression | _(none)_ | STALE_REFERENCE (Gap type 7): active test linked to deprecated AC |
| 10 | edge-case | _(none)_ | Two-phase strategy for 50+ orphan tests and untested ACs |
| 11 | happy-path | _(none)_ | ORPHAN_FUNCTIONALITY (Gap type 5): Functionality with no parent Feature |
| 12 | regression | `catalog-snapshot.json` | Normalisation: /reports/legacy ↔ FEAT-008 — not an UNDOCUMENTED_SURFACE |

## Trigger eval summary

19 entries: 13 `should_trigger=true`, 6 `should_trigger=false`

| Routes to | Query count |
|---|---|
| living-doc-create-user-story | 1 |
| living-doc-create-feature | 1 |
| living-doc-update | 1 |
| gherkin-step | 1 |
