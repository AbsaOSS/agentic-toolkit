# Fixture Map — living-doc-bdd-copilot agent evals

## Eval coverage summary

| Eval ID | Category | Description | Fixture files |
|---------|----------|-------------|---------------|
| 1 | happy-path | Business Seed assembly — seed.yaml structure | — |
| 2 | happy-path | Create mode: PageObject generation from crawled surface | — |
| 3 | happy-path | Scenario generation from US ACs | — |
| 4 | regression | RE-SCAN mode — selector drift detection and repair | — |
| 5 | regression | HEALING mode — broken step definitions | — |
| 6 | negative | Create User Story request stays in this agent — no handoff | — |
| 7 | paraphrase | "fix failing tests" → HEALING mode trigger | — |
| 8 | regression | REMOVE mode — full feature removal with pre-deletion checklist | — |
| 9 | regression | Partial state rule: seed.yaml present, manifest.json absent → first run | — |
| 10 | regression | Credential safety — literal credentials in seed.yaml rejected | — |
| 11 | edge-case | Source E guided traversal — blocked crawl, unknown field value | — |
| 12 | output-format | manifest.json entry structure for a scanned route | — |
| 25 | negative | Unit test request → decline + point to test-unit-write skill | — |

## Trigger eval summary

| Count | Triggers (should_trigger=true) | Non-triggers (should_trigger=false) |
|-------|-------------------------------|--------------------------------------|
| 44 total | 22 true | 22 false |

> No fixture files — all evals use inline prompt/expected_output; agent behavior is assessed against the agent.md operating rules and skill definitions.
