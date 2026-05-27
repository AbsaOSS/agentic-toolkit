# Fixture Map — living-doc-bdd-copilot agent evals

## Eval coverage summary

| Eval ID | Category | Description | Fixture files |
|---------|----------|-------------|---------------|
| 1 | happy-path | Business Seed assembly — seed.yaml structure | — |
| 2 | happy-path | Create mode: PageObject generation from crawled surface | — |
| 3 | happy-path | Scenario generation from US ACs | — |
| 4 | regression | RE-SCAN mode — selector drift detection and repair | — |
| 5 | regression | HEALING mode — broken step definitions | — |
| 6 | negative | User Story creation request → route to @living-doc-copilot | — |
| 7 | paraphrase | "fix failing tests" → HEALING mode trigger | — |
| 8 | regression | REMOVE mode — full feature removal with pre-deletion checklist | — |
| 9 | regression | Partial state rule: seed.yaml present, manifest.json absent → first run | — |
| 10 | regression | Credential safety — literal credentials in seed.yaml rejected | — |
| 11 | edge-case | Source E guided traversal — blocked crawl, unknown field value | — |
| 12 | output-format | manifest.json entry structure for a scanned route | — |

## Trigger eval summary

| Count | Triggers (should_trigger=true) | Non-triggers (should_trigger=false) |
|-------|-------------------------------|--------------------------------------|
| 24 total | 20 true | 4 false |

False cases:
- `create a User Story` → @living-doc-copilot
- `write a unit test` → @sdet-copilot
- `update AC state` → @living-doc-copilot
- `TypeScript quality gate` → @quality-gate-copilot (out of scope)
- `update AC on US-007` → @living-doc-copilot

> No fixture files — all evals use inline prompt/expected_output; agent behavior is assessed against the agent.md operating rules and skill definitions.
