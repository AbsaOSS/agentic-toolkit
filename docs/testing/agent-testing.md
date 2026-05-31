# Agent Testing Guide

This document describes how to test, evaluate, and tune `.agent.md` files — specifically how to use `skill-creator`'s eval methodology (for description trigger accuracy). This is the practical equivalent of [skill-testing.md](./skill-testing.md) applied to agents.

---

## Why agent testing is different from skill testing

| Dimension | Skill | Agent |
|---|---|---|
| Trigger mechanism | `description:` field in SKILL.md YAML | `description:` field in `.agent.md` YAML |
| Body loaded when? | When skill is activated by description match | When user addresses `@agent-name` or description matches |
| What to tune | Description trigger keywords + body instructions | Description trigger keywords + body sections (scope, handoff, maintenance modes) |
| Tool for eval loop | `skill-creator` (fully supported) | `skill-creator` (description eval loop applies directly) |

The key insight: an agent's `description:` block is read by the same matching mechanism as a skill's `description:`. Everything `skill-creator` does to optimize skill descriptions applies 1-for-1 to agent descriptions.

---

## 1. Recommended workflow

1. Create trigger eval cases in `.github/agents/evals/<agent-name>/trigger-eval.json`
2. Create body eval cases in `.github/agents/evals/<agent-name>/evals.json`
3. Start a Copilot Chat session from the repository root
4. Ask Copilot to use the `skill-creator` skill, pointing it at the agent's eval files
5. Review trigger accuracy and output quality
6. Edit structural sections directly in the `.agent.md` file (tools list, scope, handoff, modes)
7. Re-run evals; repeat until stable

---

## 2. File layout

```
.github/
  agents/
    my-agent.agent.md          ← agent definition
    evals/
      my-agent/
        trigger-eval.json      ← which prompts should (and should not) invoke the agent
        evals.json             ← body behavior tests
        files/                 ← fixture files referenced by evals
```

---

## 3. Trigger eval format

Store at `.github/agents/evals/<agent-name>/trigger-eval.json` as a **flat JSON array** (no wrapper object):

```json
[
  {
    "id": 1,
    "query": "Scan the webapp at https://app.example.com and generate PageObjects",
    "should_trigger": true,
    "reason": "'scan webapp' + 'generate pageobjects' core phrase"
  },
  {
    "id": 2,
    "query": "Explore the app and map all the UI surfaces",
    "should_trigger": true,
    "reason": "'explore the app' maps to crawl/explore mode"
  },
  {
    "id": 3,
    "query": "Create a User Story for the loyalty points redemption feature",
    "should_trigger": true,
    "reason": "Catalog entity creation — living-doc layer"
  },
  {
    "id": 4,
    "query": "Write a unit test for the login validator",
    "should_trigger": false,
    "reason": "Unit test authoring — out of scope"
  },
  {
    "id": 5,
    "query": "Debug the null pointer exception in PaymentService.processOrder()",
    "should_trigger": false,
    "reason": "Application debugging — outside scope"
  }
]
```

Note: the field is `query` (not `prompt`). The `reason` field is for human documentation only — it is not used by the eval runner.

Write at least **5 should-trigger** and **5 should-not-trigger** cases. Should-not-trigger cases are as important as the positive ones — they catch over-broad descriptions that shadow other agents.

---

## 4. Body eval format

Store at `.github/agents/evals/<agent-name>/evals.json`. Same schema as skill evals:

```json
{
  "agent_name": "my-agent",
  "evals": [
    {
      "id": "business-seed-assembly",
      "prompt": "I want to set up BDD automation for our app at https://app.example.com. The Angular router is at src/app/app-routing.module.ts.",
      "expected_output": "Agent assembles seed.yaml from the router file, proposes base_url, lists known_routes, confirms credential env var names before crawling.",
      "files": ["src/app/app-routing.module.ts"]
    },
    {
      "id": "re-scan-stale-locator",
      "prompt": "RE-SCAN — the checkout page was redesigned.",
      "expected_output": "Agent loads manifest.json, navigates to /checkout, validates component_id locators, flags stale ones, updates PageObject selectors. Does NOT touch unrelated pages.",
      "files": ["manifest.json"]
    },
    {
      "id": "healing-scope",
      "prompt": "HEALING — these 3 scenarios are failing: LoginPage submit, CheckoutPage confirm, DashboardPage filter.",
      "expected_output": "Agent scopes work to those 3 failing tests only. Does not re-run or touch passing tests.",
      "files": []
    }
  ]
}
```

---

## 5. Running the eval loop

Point `skill-creator` at the agent files — it treats the `description:` block the same way it treats a skill description.

### Trigger accuracy

```
Use the skill-creator skill to optimize the description for .github/agents/my-agent.agent.md
using the trigger evals at .github/agents/evals/my-agent/trigger-eval.json.
Constraints: ≤ 1024 chars; structured domain nouns/verbs; include a NOT for: boundary clause.
Report precision and recall scores for each candidate. Repeat until all trigger evals pass.
```

`skill-creator` will propose candidate descriptions, score them against the eval set, and iterate.

### Body quality

```
Use the skill-creator skill to run the body evals for .github/agents/my-agent.agent.md
using .github/agents/evals/my-agent/evals.json.
Verify: (1) all body-referenced tools are present in the frontmatter tools: list,
(2) mode dispatch routes to the correct skill for each intent,
(3) scope boundaries match ## Scope and ## Does NOT, (4) handoff targets are correct.
Only fix scope, tool, or handoff issues — do not rewrite unless fundamentally mis-scoped.
Repeat until all evals pass.
```

Use the same with-skill / baseline comparison flow described in [skill-testing.md](./skill-testing.md).

---

## 6. Structural edits

When body evals reveal a section is wrong (wrong scope, missing tool, bad handoff), edit the `.agent.md` file directly:

- **Missing tool** — add the tool name to the `tools:` list in the YAML frontmatter
- **Wrong scope boundary** — update the relevant section (`## Scope`, `## Does NOT`, or the specific mode block)
- **Broken handoff** — update the `## Handoff` section with the correct target agent and conditions

---

## 7. What to tune — agent-specific checklist

Beyond the standard skill tuning checklist, also verify:

| Check | Good signal | Bad signal |
|---|---|---|
| **Trigger precision** | Agent fires only for its domain | Fires for requests that belong to another agent |
| **Trigger recall** | All domain phrases trigger it | Mis-fires to default agent for known phrases |
| **Scope boundaries** | Refuses work outside its Does-NOT list | Silently attempts work outside its scope |
| **Mode activation** | RE-SCAN / HEALING / REMOVE activate on correct triggers | Wrong mode fires, or modes don't activate |
| **Handoff clarity** | Outputs correct hand-off message to the right agent | Hands off to wrong agent or swallows the work |
| **Tool completeness** | All tools needed by the body are in the frontmatter `tools:` list | Body references a tool not in `tools:` — it will be unavailable |

---

## 8. Description anti-patterns

These are the most common description problems observed in agent files:

**Over-broad description** — causes the agent to shadow other agents:
```yaml
# BAD — fires on almost everything
description: >
  Helps with testing, documentation, and web apps.
```

**Under-specified triggers** — causes the agent to miss its domain:
```yaml
# BAD — won't fire on "crawl the UI" or "playwright scan"
description: >
  Generates BDD tests.
```

**Good pattern** — minimalist semantic description with a `NOT for:` boundary:
```yaml
description: >
  Living documentation catalog (User Stories, Features, Functionalities, ACs, impact
  analysis, gap finding) and BDD automation (Playwright crawl/explore/scan, PageObjects
  create/heal, Gherkin scenarios/feature files/step definitions, living-doc sync,
  scenario coverage). Setup: seed.yaml → manifest.json, credential checks, guided
  traversal. NOT for: unit tests, production code, API specs, CI/CD, debugging,
  performance, security.
```

The `NOT for:` clause is as important as the positive terms — it prevents the agent from firing on adjacent-but-out-of-scope requests. An explicit `Triggers:` keyword list is not required; structured domain nouns and verbs are sufficient for the matching mechanism to work.

---

## 9. Regression-first loop

Same as skill testing — run the full trigger-eval set, fix the largest failure cluster, re-run:

1. Run full trigger-eval and body-eval sets; save baseline scores
2. Identify largest failure cluster (e.g. 4 should-not-trigger cases fire)
3. Make one description change
4. Re-run trigger-eval only
5. Review delta
6. Run full suite
7. Keep or revert
8. Repeat until all trigger evals pass and body eval delta is positive or neutral

---

## 10. Minimal session

```
VS Code Copilot Chat (or gh copilot):
→ "Use the skill-creator skill to test the agent at .github/agents/my-agent.agent.md
   using the evals at .github/agents/evals/my-agent/.
   Report trigger precision/recall and body eval pass rate."
→ inspect trigger accuracy report and body output diffs;
  classify each change as improvement, regression, or neutral
→ edit the `.agent.md` file directly to fix structural issues
  (scope, tools: list, mode dispatch, handoff)
→ "Use the skill-creator skill to optimize the description for .github/agents/my-agent.agent.md
   using .github/agents/evals/my-agent/trigger-eval.json.
   Keep ≤ 1024 chars; include a NOT for: boundary clause. Repeat until all evals pass."
→ re-run full eval suite; keep or revert each change; repeat until stable
```

---

For the full eval methodology (subagent spawning, benchmark aggregation, the viewer), see [skill-testing.md](./skill-testing.md) — the process is identical once the eval files are in place.
