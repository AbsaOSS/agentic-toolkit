# Fixture Map — living-doc-create-user-story

## Fixture files

| File | Description |
|---|---|
| `evals/files/incomplete-user-story.json` | User Story US-042 (password reset) with only a happy-path AC — missing error and alternative paths |

## Eval to fixture mapping

| Eval ID | Category | Fixture file(s) | Coverage |
|---|---|---|---|
| 1 | happy-path | _(none — conversational elicitation)_ | Full elicitation workflow: actor → narrative → Feature → ACs → completeness check → output |
| 2 | happy-path | `incomplete-user-story.json` | Completeness check: detects missing error + alternative ACs |
| 3 | happy-path | _(none)_ | Anti-pattern: invalid actor ("the system") |
| 4 | regression | _(none)_ | Anti-pattern: technical AC (DB implementation detail) |
| 5 | negative | _(none)_ | Routing: atomic behavior → living-doc-create-functionality |
| 6 | paraphrase | _(none)_ | SMS password reset — full elicitation with happy path + error paths |
| 7 | edge-case | _(none)_ | Two actors for same capability → two separate User Stories |
| 8 | output-format | _(none)_ | Canonical UserStory JSON: as_a/i_want/so_that, AC:US-<nnn>-<nn> format |
| 9 | regression | _(none)_ | Anti-pattern: 'I want' clause with 'and' — two capabilities bundled |
| 10 | regression | _(none)_ | Anti-pattern: single-value placeholder {error type} |
| 11 | regression | _(none)_ | Anti-pattern: non-observable outcome (background job) |
| 12 | edge-case | _(none)_ | Duplicate AC across two User Stories → shared Functionality |

## Trigger eval summary

18 entries: 13 `should_trigger=true`, 5 `should_trigger=false`

| Routes to | Query count |
|---|---|
| living-doc-create-feature | 1 |
| living-doc-create-functionality | 1 |
| living-doc-scenario-creator | 2 |
| living-doc-gap-finder | 1 |
