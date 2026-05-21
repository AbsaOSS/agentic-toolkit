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

## Trigger eval summary

14 entries: 10 `should_trigger=true`, 4 `should_trigger=false`

| Routes to | Query count |
|---|---|
| living-doc-create-user-story | 1 |
| living-doc-create-feature | 1 |
| living-doc-scenario-creator | 1 |
| living-doc-gap-finder | 1 |
