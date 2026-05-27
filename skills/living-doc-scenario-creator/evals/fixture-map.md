# Fixture Map — living-doc-scenario-creator

## Fixture files

No fixture files for this skill. All evals use inline User Story/AC definitions within the prompt.

## Eval to fixture mapping

| Eval ID | Category | Fixture file(s) | Coverage |
|---|---|---|---|
| 1 | happy-path | _(none — inline US JSON in prompt)_ | Three active ACs → three scenarios; # AC: comments + @AC: tags; naming conventions |
| 2 | happy-path | _(none — inline AC list in prompt)_ | AC state filtering: Active → generated, Deprecated → skipped, Planned → skipped |
| 3 | happy-path | _(none)_ | Case A step stub: PageObject method exists — full stub, no NotImplementedError |
| 4 | regression | _(none)_ | Case B step stub: missing PageObject method — NotImplementedError + maintenance flag |
| 5 | negative | _(none)_ | Routing: standalone Gherkin without a US → gherkin-scenario |
| 6 | paraphrase | _(none)_ | "Write feature tests for US-nnn" → scenario generation request |
| 7 | edge-case | _(none)_ | All ACs Planned → zero scenarios generated; coverage report with skip reasons |
| 8 | output-format | _(none)_ | .feature file structure: @US_ID:, Feature: header, # AC: + @AC: per scenario |
| 9 | edge-case | _(none)_ | /aspect:value param encoding for multi-aspect ACs |
| 10 | output-format | _(none)_ | Feature-level @US_ID: tag vs. per-scenario @AC: tags |
| 11 | regression | _(none)_ | coverage_report.py: @AC: tag mismatch causing false "not covered" result |

## Trigger eval summary

18 entries: 13 `should_trigger=true`, 5 `should_trigger=false`

| Routes to | Query count |
|---|---|
| gherkin-scenario | 1 |
| gherkin-step | 1 |
| living-doc-gap-finder | 1 |
| gherkin-living-doc-sync | 1 |
