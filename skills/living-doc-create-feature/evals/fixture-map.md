# Fixture Map — living-doc-create-feature

## Fixture files

No fixture files for this skill. All evals are conversational — the skill provides
procedural guidance for structuring a Feature entity from user-provided answers.

## Eval to fixture mapping

| Eval ID | Category | Fixture file(s) | Coverage |
|---|---|---|---|
| 1 | happy-path | _(none — conversational)_ | UI surface: Checkout Page — full elicitation workflow |
| 2 | happy-path | _(none)_ | API surface: Orders API — surface type identification |
| 3 | regression | _(none)_ | Orphan Feature warning (no User Stories, no Functionalities) |
| 4 | happy-path | _(none)_ | Anti-pattern: verb-phrase Feature name (Process Payment) |
| 5 | negative | _(none)_ | Routing: User Story creation → living-doc-create-user-story |

## Trigger eval summary

14 entries: 10 `should_trigger=true`, 4 `should_trigger=false`

| Routes to | Query count |
|---|---|
| living-doc-create-user-story | 1 |
| living-doc-create-functionality | 1 |
| living-doc-pageobject-scan | 1 |
| living-doc-scenario-creator | 1 |
