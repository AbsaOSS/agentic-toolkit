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
| 9 | edge-case | *(no file — descope AC mid-sprint: AC stays 'planned' with no target version, reason recorded on a '- Rationale:' bullet, AC not deleted)* |
| 10 | happy-path | *(no file — AC text change: OLD/NEW diff + linked scenario list)* |
| 11 | happy-path | `payment-living-doc.md` — AC-2 SLA change from 3 s to 1 s (p99) |
| 12 | regression | *(no file — Feature deprecation with superseded_by field)* |
| 13 | regression | *(no file — validate_entity.py post-update validation)* |
| 14 | edge-case | *(no file — US promotion blocked by missing error-path AC)* |
| 15 | regression | *(no file — business-rule change to an active AC: minor version bump, ID stable)* |
| 16 | regression | *(no file — Feature rename cascade)* |
| 17 | happy-path | `dependency-promotion-catalog.json` — `payment-events` promoted to an API Feature; named in `external_dependencies` by FEAT-001 *and* FEAT-002 (different casing), prompt mentions only FEAT-001 |

## Coverage summary

- happy-path: 4 (add AC to User Story, AC diff format, payment living doc SLA update, dependency promotion cascade)
- regression: 8 (US promotion check, deprecate Functionality, Feature ownership, AC ID stability, Feature deprecation with superseded_by, validate after update, active-AC version bump, Feature rename cascade)
- negative: 2 (create US redirect, gap-finder redirect)
- paraphrase: 1 (add AC phrased as "update the story")
- edge-case: 2 (descope AC mid-sprint, US promotion blocked by missing error-path AC)

A dependency that is only added or only dropped has no eval of its own — nothing about either
cascades. The promotion (17) is the one situation that does.

## Rules exercised

| Rule | Eval ID |
|---|---|
| Add AC to existing User Story | 1 |
| US promotion invariants check | 2, 14 |
| Deprecate entity — never delete | 3, 12 |
| Feature ownership update in JSON + registry | 4 |
| AC ID stability when modifying description | 5, 15 |
| Out-of-scope: create US → living-doc-create-user-story | 6 |
| Out-of-scope: find gaps → living-doc-gap-finder | 7 |
| Descope AC mid-sprint | 9 |
| Change summary format with OLD/NEW diff | 10, 11 |
| superseded_by field on Feature deprecation | 12 |
| validate_entity.py post-update check | 13 |
| Minor version bump for a business-rule change to an active AC | 15 |
| Feature rename cascade | 16 |
| Dependency promotion: route creation to living-doc-create-feature, scan every Feature's `external_dependencies`, record the edge on the calling Functionality, no re-parenting, `ORPHAN_FEATURE` on the new Feature | 17 |
