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
| 5 | negative | _(none)_ | Routing: standalone Gherkin without a US → living-doc-scenario-creator (standalone mode) |
| 6 | paraphrase | _(none)_ | "Write feature tests for US-nnn" → scenario generation request |
| 7 | edge-case | _(none)_ | All ACs Planned → zero scenarios generated; coverage report with skip reasons |
| 8 | output-format | _(none)_ | .feature file structure: @US_ID:, Feature: header, # AC: + @AC: per scenario |
| 9 | edge-case | _(none)_ | /aspect:value param encoding for multi-aspect ACs |
| 10 | output-format | _(none)_ | Feature-level @US_ID: tag vs. per-scenario @AC: tags |
| 11 | regression | _(none)_ | coverage_report.py: @AC: tag mismatch causing false "not covered" result |
| 12 | happy-path | _(none)_ | Merge policy: existing scenario already matches AC intent exactly → skip, no duplicate; AC marked covered |
| 13 | regression | _(none)_ | Merge policy: existing scenario intent matches but GWT text is stale → update in place, no new scenario; routes @AC: tag sync to gherkin-living-doc-sync if needed |
| 14 | edge-case | _(none)_ | Merge policy: existing scenario is deprecated/review-needed → propose replacement, mark old as superseded, human review before delete |
| 15 | edge-case | _(none)_ | Merge policy: AC already has 3+ linked scenarios → flag for review instead of adding another; user picks the canonical scenario |
| 16 | regression | _(none)_ | coverage_report.py: @AC: tag counts as coverage, bare # AC: comment does not; mixed set reports 1 covered / 2 gaps |
| 17 | regression | _(none)_ | coverage_report.py: empty features directory → all ACs NOT COVERED, exit code 1, no hallucinated coverage |
| 18 | regression | _(none)_ | coverage_report.py: zero-padding mismatch (@AC:US-10-02 vs US-010-02) → NOT COVERED + unrecognised-tag warning, no fuzzy matching |
| 19 | happy-path | _(none)_ | coverage_report.py: all ACs tag-matched → 100% covered, real file names listed, exit code 0 |
| 20 | happy-path | _(none)_ | Gap-to-generation handoff: coverage report gaps become the scenario-creator queue, processed in report order |
| 21 | output-format | _(none)_ | Regression closeout: single happy-day scenario tagged @AC: + @Regression; scan_ac_links.py and coverage_report.py must show 0 NOT COVERED happy-path ACs before close |
| 22 | regression | _(none — inline FUNC/AC definition in prompt)_ | Functionality feature file: @FUNC_ID: tag, Feature: name uses plain hyphen separator (not em/en dash), # AC:/@AC: pairing |

## Trigger eval summary

18 entries: 13 `should_trigger=true`, 5 `should_trigger=false`

| Routes to | Query count |
|---|---|
| gherkin-step | 1 |
| living-doc-gap-finder | 1 |
| gherkin-living-doc-sync | 1 |
