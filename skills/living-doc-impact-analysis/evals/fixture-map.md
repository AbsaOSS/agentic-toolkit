# Living Doc Impact Analysis — Evals Fixture Map

| Test ID | Category | Fixture |
|---|---|---|
| 1 | happy-path | *(no file — PR domain logic impact map scenario)* |
| 2 | regression | *(no file — API contract change scenario re-run list)* |
| 3 | regression | *(no file — release sign-off checklist scenario)* |
| 4 | regression | *(no file — changed module missing from FEATURE_REGISTRY)* |
| 5 | regression | *(no file — infra-only change None impact level)* |
| 6 | negative | *(no file — update entity redirect to living-doc-update)* |
| 7 | negative | *(no file — gap-finding redirect to living-doc-gap-finder)* |

## Coverage summary

- happy-path: 1 (PR domain logic full impact trace)
- regression: 4 (API contract, release sign-off, missing registry entry, infra-only)
- negative: 2 (update entity redirect, gap-finder redirect)

## Rules exercised

| Rule | Eval ID |
|---|---|
| Map changed file → Feature → US → scenarios | 1 |
| API contract change impact trace | 2 |
| Release sign-off checklist | 3 |
| Flag missing FEATURE_REGISTRY coverage | 4 |
| Classify infra change as None impact | 5 |
| Out-of-scope: update entity → living-doc-update | 6 |
| Out-of-scope: find gaps → living-doc-gap-finder | 7 |
