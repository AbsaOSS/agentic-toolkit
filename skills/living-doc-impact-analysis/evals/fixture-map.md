# Living Doc Impact Analysis — Evals Fixture Map

| Test ID | Category | Fixture |
|---|---|---|
| 1 | happy-path | *(no file — PR domain logic impact map scenario)* |
| 2 | regression | *(no file — API contract change scenario re-run list)* |
| 3 | regression | *(no file — release sign-off checklist scenario)* |
| 4 | regression | *(no file — changed module missing from feature_registry in catalog.json)* |
| 5 | regression | *(no file — infra-only change None impact level)* |
| 6 | negative | *(no file — update entity redirect to living-doc-update)* |
| 7 | negative | *(no file — gap-finding redirect to living-doc-gap-finder)* |
| 8 | paraphrase | *(no file — "what needs re-testing" re-test checklist framing)* |
| 9 | edge-case | *(no file — shared utility MoneyUtils fan-out to all consumers)* |
| 10 | output-format | *(no file — code-level impact report: method signature change format)* |
| 11 | file-based | `changed-notification-service.py` | Impact of NotificationClient.send() signature change |
| 12 | edge-case | *(no file — test-only PR: None impact level)* |
| 13 | happy-path | *(no file — PR with domain service + REST controller: fan-out trace)* |
| 14 | regression | *(no file — shared utility rounding change fan-out across three Features)* |

## Coverage summary

- happy-path: 2 (domain logic impact trace, multi-file fan-out)
- regression: 5 (API contract, release sign-off, missing registry entry, infra-only, shared utility)
- negative: 2 (update entity redirect, gap-finder redirect)
- paraphrase: 1 (re-test checklist framing)
- edge-case: 2 (shared utility fan-out, test-only None impact)
- output-format: 1 (method signature change format)
- file-based: 1 (NotificationClient signature change)

## Rules exercised

| Rule | Eval ID |
|---|---|
| Map changed file → Feature → US → scenarios | 1, 13 |
| API contract change impact trace | 2 |
| Release sign-off checklist | 3 |
| Flag missing feature_registry coverage | 4 |
| Classify infra change as None impact | 5 |
| Out-of-scope: update entity → living-doc-update | 6 |
| Out-of-scope: find gaps → living-doc-gap-finder | 7 |
| Re-test checklist framing | 8 |
| Shared utility fan-out to all consumers | 9, 14 |
| Method signature change code-level format | 10 |
| File-based method signature analysis | 11 |
| Test-only change → None impact | 12 |
