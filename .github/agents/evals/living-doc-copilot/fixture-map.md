# Fixture Map — living-doc-copilot agent evals

## Eval coverage summary

| Eval ID | Category | Description | Fixture files |
|---------|----------|-------------|---------------|
| 1 | happy-path | Storage Profile elicitation on session start | — |
| 2 | happy-path | Create User Story with full AC metadata fields | — |
| 3 | happy-path | PLAN mode — draft ACs from PO description in PLANNED state | — |
| 4 | happy-path | Impact analysis: code change → impact map | — |
| 5 | regression | HEALING mode — stale Functionality deprecation | — |
| 6 | negative | Gherkin scenario request → route to @living-doc-bdd-copilot | — |
| 7 | paraphrase | "document a behavior" → create Functionality entity | — |
| 8 | regression | Updating ACTIVE AC bumps version, preserves ID, flags Gherkin stale | — |
| 9 | regression | Storage Profile reuse — does NOT re-ask within same session | — |
| 10 | regression | AC completeness check — missing state/version/pre-conditions/not_in_scope | — |
| 11 | negative | Webapp scan/PageObject request → route to @living-doc-bdd-copilot | — |
| 12 | edge-case | HEALING mode — ORPHAN_FUNCTIONALITY repair with Feature link proposal | — |

## Trigger eval summary

| Count | Triggers (should_trigger=true) | Non-triggers (should_trigger=false) |
|-------|-------------------------------|--------------------------------------|
| 20 total | 15 true | 5 false |

False cases:
- `scan webapp / generate pageobjects` → @living-doc-bdd-copilot
- `generate BDD scenarios` → @living-doc-bdd-copilot
- `write a unit test` → @sdet-copilot
- `fix failing BDD tests` → @living-doc-bdd-copilot
- `crawl the app and create PageObjects` → @living-doc-bdd-copilot

> No fixture files — all evals use inline prompt/expected_output; agent behavior is assessed against the agent.md operating rules.
