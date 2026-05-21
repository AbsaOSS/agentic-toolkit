# Living Doc Update — Evals Fixture Map

| Test ID | Category | Fixture |
|---|---|---|
| 1 | happy-path | *(no file — add AC to existing User Story scenario)* |
| 2 | regression | *(no file — US promotion invariant check scenario)* |
| 3 | regression | *(no file — deprecate deleted Functionality scenario)* |
| 4 | regression | *(no file — Feature ownership change scenario)* |
| 5 | regression | *(no file — modify AC description without breaking traceability)* |
| 6 | negative | *(no file — create US redirect to living-doc-create-user-story)* |
| 7 | negative | *(no file — gap-finding redirect to living-doc-gap-finder)* |

## Coverage summary

- happy-path: 1 (add AC to User Story)
- regression: 4 (US promotion check, deprecate Functionality, Feature ownership change, modify AC)
- negative: 2 (create US redirect, gap-finder redirect)

## Rules exercised

| Rule | Eval ID |
|---|---|
| Add AC to existing User Story | 1 |
| US promotion invariants check | 2 |
| Deprecate entity — never delete | 3 |
| Feature ownership update in JSON + registry | 4 |
| AC ID stability when modifying description | 5 |
| Out-of-scope: create US → living-doc-create-user-story | 6 |
| Out-of-scope: find gaps → living-doc-gap-finder | 7 |
