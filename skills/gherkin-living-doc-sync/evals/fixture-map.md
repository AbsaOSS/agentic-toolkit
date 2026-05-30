# Fixture Map — gherkin-living-doc-sync

## Fixture files

No fixture files for this skill. All evals are conversational — the skill operates on feature files and a living doc catalog referenced by path, not by inline fixture content.

## Eval to fixture mapping

| Eval ID | Category | Fixture file(s) | Coverage |
|---|---|---|---|
| 1 | happy-path | _(none — conversational)_ | Missing # AC: headers in checkout.feature — SYNC ACTION blocks per scenario |
| 2 | happy-path | _(none)_ | AC description updated in living doc → propagate to # AC: comment in feature file |
| 3 | happy-path | _(none)_ | Step text drift after UI rename → DRIFT DETECTED block with two fix options |
| 4 | regression | _(none)_ | US deprecated in living doc → @deprecated + @review-needed tags on linked scenarios |
| 5 | negative | _(none)_ | Routing: new scenario authoring → bdd-scenario-gen |
| 6 | paraphrase | _(none)_ | "Feature files are a mess after redesign" → prioritised repair plan: steps first, then links |
| 7 | edge-case | _(none)_ | Broken AC reference (US-099 not in catalog) → resolution options, never remove the link |
| 8 | output-format | _(none)_ | Sync run output format: SYNC ACTION + DRIFT DETECTED blocks + summary line |
| 9 | happy-path | _(none)_ | @AC: Cucumber tag vs # AC: comment — both required, each serves a distinct purpose |
| 10 | happy-path | _(none)_ | scan_ac_links.py audit command and output interpretation |
| 11 | regression | _(none)_ | Aspect param mismatch: @AC: tag has /aspect: but # AC: comment does not mirror it |
| 12 | edge-case | _(none)_ | Descoped AC: tag scenario @wip/@pending, add comment, never delete |

## Trigger eval summary

20 entries: 14 `should_trigger=true`, 6 `should_trigger=false`

| Routes to | Query count |
|---|---|
| bdd-scenario-gen | 2 |
| gherkin-step | 1 |
| living-doc-gap-finder | 1 |
| living-doc-create-user-story | 1 |
