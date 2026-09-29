# Fixture Map — living-doc-create-feature

## Fixture files

| File | Description |
|---|---|
| `evals/files/raw-feature-notes.md` | Discovery session notes for the Notifications Centre screen — used by the file-based eval (id=9) |

## Eval to fixture mapping

| Eval ID | Category | Fixture file(s) | Coverage |
|---|---|---|---|
| 1 | happy-path | _(none — conversational)_ | UI surface: Checkout Page — full elicitation workflow |
| 2 | happy-path | _(none)_ | API surface: Orders API — surface type identification |
| 3 | regression | _(none)_ | Orphan Feature warning (no User Stories, no Functionalities) |
| 4 | happy-path | _(none)_ | Anti-pattern: verb-phrase Feature name (Process Payment) |
| 5 | negative | _(none)_ | Routing: User Story creation → living-doc-create-user-story |
| 6 | paraphrase | _(none)_ | Notification Service — surface type (API-only) identification |
| 7 | edge-case | _(none)_ | Shared utility library — external_dependency vs Feature entity |
| 8 | output-format | _(none)_ | Canonical JSON output: all required fields, FEAT-kebab id, surface_type enum |
| 9 | file-based | `raw-feature-notes.md` | Notifications Centre — extract surface from rough notes |
| 10 | regression | _(none)_ | Anti-pattern: technology-encoded Feature name (Spring Payment Controller) |
| 11 | edge-case | _(none)_ | Anti-pattern: surface_type=UI for a REST controller |
| 12 | happy-path | _(none)_ | Kafka-topic worker (PaymentEventProcessor) — asks for AsyncAPI annotation on the handler; anchors an API Feature if annotated, else declined and recorded as external_dependencies |
| 13 | regression | _(none)_ | Candidate Functionalities not formally defined — leave functionalities=[] |
| 14 | regression | _(none)_ | Duplicate Feature name conflict resolution |

## Trigger eval summary

29 entries: 13 `should_trigger=true`, 16 `should_trigger=false`

| Routes to | Query count |
|---|---|
| living-doc-create-user-story | 1 |
| living-doc-create-functionality | 2 |
| living-doc-pageobject-scan | 1 |
| living-doc-scenario-creator | 2 |
| living-doc-update | 4 (deprecate, rename, drop a dependency, promote a dependency) |
| gherkin-step | 1 |
| bdd-maintain | 1 |
| living-doc-gap-finder | 1 |
| gherkin-living-doc-sync | 1 |
| living-doc-impact-analysis | 1 |
| data-cy-instrument | 1 |

Creation vs change: this skill owns a Feature that does not exist yet. Any change to an existing
Feature — owners, dependencies, rename, registry entry, deprecation — routes to `living-doc-update`.
