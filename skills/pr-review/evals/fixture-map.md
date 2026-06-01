# PR Review Evals Fixture Map

This file links each eval test case to its related fixture diff.

| Test ID | Category | Fixture |
|---|---|---|
| 1 | happy-path | skills/pr-review/evals/files/api-rename.diff |
| 2 | happy-path | skills/pr-review/evals/files/iac-wildcard-iam.diff |
| 3 | regression | skills/pr-review/evals/files/ci-gate-bypass.diff |
| 4 | happy-path | skills/pr-review/evals/files/standard-clean-pr.diff |
| 5 | happy-path | skills/pr-review/evals/files/dependency-bump-risk.diff |
| 6 | regression | skills/pr-review/evals/files/db-migration-risks.diff |
| 7 | regression | skills/pr-review/evals/files/elevated-risk-auth-refactor.diff |
| 8 | edge-case | skills/pr-review/evals/files/large-pr-and-vague-desc.diff |
| 9 | negative | skills/pr-review/evals/files/docs-release-notes.diff |
| 10 | paraphrase | skills/pr-review/evals/files/api-rename.diff |
| 11 | paraphrase | skills/pr-review/evals/files/ci-gate-bypass.diff |
| 12 | multi-section | skills/pr-review/evals/files/multi-section-risks.diff |
| 13 | happy-path | skills/pr-review/evals/files/skill-definition-clean.diff |
| 14 | regression | skills/pr-review/evals/files/skill-definition-violations.diff |
| 15 | paraphrase | skills/pr-review/evals/files/skill-definition-violations.diff |

> **Note:** Eval-9 (release-notes negative case) is intentionally listed here in `evals.json` for quality-suite coverage, and is also mirrored in `trigger-eval.json` as `n11-release-notes-from-diff` for trigger-boundary coverage.

## Coverage Summary

- happy-path: 5
- regression: 4
- edge-case: 1
- negative: 1
- paraphrase: 3
- multi-section: 1
- total: 15

