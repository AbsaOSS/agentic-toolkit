# Fixture Map — living-doc-create-functionality

## Fixture files

| File | Description |
|---|---|
| `evals/files/broad-functionality.json` | Draft Functionality with over-broad name ("Handle checkout") and vague ACs — tests completeness enforcement |

## Eval to fixture mapping

| Eval ID | Category | Fixture file(s) | Coverage |
|---|---|---|---|
| 1 | happy-path | _(none — conversational)_ | Full elicitation: cart validation behavior, completeness checklist, atomic ACs, error codes |
| 2 | happy-path | `broad-functionality.json` | Blocker detection: broad name, vague ACs, no error codes |
| 3 | happy-path | _(none)_ | unit vs integration decision for a DB uniqueness check |
| 4 | regression | _(none)_ | Reuse candidate detection: same AC in two User Stories |
| 5 | negative | _(none)_ | Routing: User Story creation → living-doc-create-user-story |
| 6 | paraphrase | _(none)_ | Gold member discount business rule — Functionality elicitation |
| 7 | edge-case | _(none)_ | 12 ACs → non-atomic scope signal; recommend split |
| 8 | output-format | _(none)_ | Canonical Functionality JSON: all required fields, test_coverage array |
| 9 | regression | _(none)_ | Anti-pattern: noun name ('Password Validation') → verb phrase required |
| 10 | happy-path | _(none)_ | Feature inference from context ('checkout domain') |
| 11 | regression | _(none)_ | Missing parent Feature: ORPHAN_FUNCTIONALITY anti-pattern |
| 12 | edge-case | _(none)_ | Vague AC ('validates') — non-testable; rewrite with explicit When/Then + error code |

## Trigger eval summary

22 entries: 16 `should_trigger=true`, 6 `should_trigger=false`

| Routes to | Query count |
|---|---|
| living-doc-create-user-story | 1 |
| living-doc-create-feature | 1 |
| living-doc-scenario-creator | 1 |
| living-doc-gap-finder | 1 |
| living-doc-update | 1 |
| living-doc-pageobject-scan | 1 |
