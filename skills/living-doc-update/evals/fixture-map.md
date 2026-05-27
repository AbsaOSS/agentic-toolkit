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
| 8 | paraphrase | *(no file — add AC phrased as "update the story")* |
| 9 | edge-case | *(no file — descope AC mid-sprint: status=descoped, do not delete)* |
| 10 | output-format | *(no file — AC text change: OLD/NEW diff + linked scenario list)* |
| 11 | file-based | `payment-living-doc.md` | AC-2 SLA change from 3 s to 1 s (p99) |
| 12 | happy-path | *(no file — Feature deprecation with superseded_by field)* |
| 13 | regression | *(no file — validate_entity.py post-update validation)* |
| 14 | regression | *(no file — US promotion blocked by missing error-path AC)* |

## Coverage summary

- happy-path: 2 (add AC to User Story, Feature deprecation with superseded_by)
- regression: 5 (US promotion check, deprecate Functionality, Feature ownership, AC ID stability, validate after update)
- negative: 2 (create US redirect, gap-finder redirect)
- paraphrase: 1 (add AC phrased as "update the story")
- edge-case: 1 (descope AC mid-sprint)
- output-format: 1 (AC diff format)
- file-based: 1 (payment living doc SLA update)

## Rules exercised

| Rule | Eval ID |
|---|---|
| Add AC to existing User Story | 1 |
| US promotion invariants check | 2, 14 |
| Deprecate entity — never delete | 3, 12 |
| Feature ownership update in JSON + registry | 4 |
| AC ID stability when modifying description | 5 |
| Out-of-scope: create US → living-doc-create-user-story | 6 |
| Out-of-scope: find gaps → living-doc-gap-finder | 7 |
| Descope AC mid-sprint | 9 |
| Change summary format with OLD/NEW diff | 10, 11 |
| superseded_by field on Feature deprecation | 12 |
| validate_entity.py post-update check | 13 |
