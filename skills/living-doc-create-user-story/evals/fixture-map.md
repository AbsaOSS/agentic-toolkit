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

## Trigger eval summary

14 entries: 10 `should_trigger=true`, 4 `should_trigger=false`

| Routes to | Query count |
|---|---|
| living-doc-create-feature | 1 |
| living-doc-create-functionality | 1 |
| living-doc-scenario-creator | 1 |
| living-doc-gap-finder | 1 |
