# Skill Testing Guide

This document provides a comprehensive methodology for testing, evaluating, and optimizing skills in this repository. It covers eval creation, fixture management, iterative improvement, trigger testing, and description optimization.

---

## 1. Recommended workflow

1. Create eval cases in `skills/<skill-name>/evals/evals.json`
2. Add fixture files under `skills/<skill-name>/evals/files/` when prompts depend on local files
3. Start a Copilot CLI session from the repository root
4. Ask Copilot to use the `skill-creator` skill to test the target skill
5. Review outputs and diffs
6. Improve the skill description or body
7. Re-run targeted evals, then the full suite
8. Repeat until regressions are stable and output quality is consistently better

## 2. Eval Cases

Store evals in `skills/<skill-name>/evals/evals.json`:

```json
{
  "skill_name": "my-skill",
  "evals": [
    {
      "id": "happy-path-1",
      "prompt": "A realistic prompt a real user would type, with concrete detail",
      "expected_output": "Short description of what a successful result should do",
      "files": []
    }
  ]
}
```

Write prompts that look like real user requests, not abstract test descriptions. Include a mix of happy-path, regression, output-format, edge, negative, and paraphrased cases.

## 3. Fixtures

If the skill operates on files, place sample inputs in `skills/<skill-name>/evals/files/` and reference those files from the eval entries. Use small, representative fixtures.

## 4. With/Without Skill Comparisons

Ask for a side-by-side comparison in the Copilot CLI session:

```
Use the skill-creator skill to compare outputs for skills/my-skill with and without the skill enabled.
```

Compare correctness, completeness, structure, latency, verbosity, and formatting stability.

## 5. Reviewing Outputs and Diffs

Review changed outputs and fixture diffs. Classify each change as improvement, acceptable variation, regression, or unclear. Avoid making fixtures so strict that harmless wording improvements fail the test.

## 6. Iterative Improvement

When an eval fails, update the smallest possible part of the skill and re-run the affected cases first. Avoid large rewrites unless the skill is fundamentally mis-scoped.

## 7. Regression-First Loop

1. Run the full eval suite and save the baseline
2. Pick the largest failure cluster
3. Make one small edit to the skill
4. Re-run only affected evals and regressions
5. Review output diffs
6. Run the full suite again
7. Keep or revert the change
8. Repeat until stable

## 8. Body vs. Trigger Testing

- **Body testing:** Use `evals/evals.json` to verify that once the skill is active, it behaves correctly.
- **Trigger testing:** Create `skills/<skill-name>/evals/trigger-eval.json` to test whether the skill activates for the right queries.

## 9. Description Optimization

Ask Copilot to optimize the description against your trigger eval set:

```
Use the skill-creator skill to optimize the description for skills/my-skill using skills/my-skill/evals/trigger-eval.json.
```

## 10. What “good enough” looks like

- All smoke tests and known regressions passing
- No critical format failures
- Positive or neutral delta versus baseline
- Stable behavior across paraphrases
- Strong trigger accuracy on both train and validation queries

## 11. Practical Tips

- Use realistic prompts with concrete nouns, filenames, and intent
- Prefer several focused evals over one large vague eval
- Keep fixtures small and scenario-specific
- Update fixtures only after confirming the new behavior is actually better
- Do not optimize solely for exact string matches
- If a change improves one eval but harms unrelated ones, revert it

## 12. Minimal CLI Loop

```
gh copilot
→ "Use the skill-creator skill to test my skill at skills/my-skill"
→ inspect results and diffs
→ edit SKILL.md or fixtures
→ "Use the skill-creator skill to rerun the evals for skills/my-skill"
→ optimize description if needed
→ repeat until stable
```

---

For more on evals, see [Demystifying Evals for AI Agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents) and the `skill-creator` skill documentation.
