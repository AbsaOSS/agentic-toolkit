# Agent Testing Guide

This document describes how to test, evaluate, and tune `.agent.md` files — specifically how to use `agent-customization` (for structural edits) together with `skill-creator`'s eval methodology (for description trigger accuracy). This is the practical equivalent of [skill-testing.md](./skill-testing.md) applied to agents.

---

## Why agent testing is different from skill testing

| Dimension | Skill | Agent |
|---|---|---|
| Trigger mechanism | `description:` field in SKILL.md YAML | `description:` field in `.agent.md` YAML |
| Body loaded when? | When skill is activated by description match | When user addresses `@agent-name` or description matches |
| What to tune | Description trigger keywords + body instructions | Description trigger keywords + body sections (scope, handoff, maintenance modes) |
| Tool for structural edits | `skill-creator` | `agent-customization` |
| Tool for eval loop | `skill-creator` (fully supported) | `skill-creator` (description eval loop applies directly) |

The key insight: an agent's `description:` block is read by the same matching mechanism as a skill's `description:`. Everything `skill-creator` does to optimize skill descriptions applies 1-for-1 to agent descriptions.

---

## 1. Recommended workflow

1. Create trigger eval cases in `.github/agents/evals/<agent-name>/trigger-eval.json`
2. Create body eval cases in `.github/agents/evals/<agent-name>/evals.json`
3. Start a Copilot Chat session from the repository root
4. Ask Copilot to use the `skill-creator` skill, pointing it at the agent's eval files
5. Review trigger accuracy and output quality
6. Use `agent-customization` to edit structural sections (tools list, scope, handoff, modes)
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

Mirrors the skill trigger-eval format exactly. Store at `.github/agents/evals/<agent-name>/trigger-eval.json`:

```json
{
  "agent_name": "my-agent",
  "evals": [
    {
      "id": "should-trigger-1",
      "prompt": "scan this webapp and generate pageobjects",
      "should_trigger": true
    },
    {
      "id": "should-trigger-2",
      "prompt": "explore the app and create page objects for the login screen",
      "should_trigger": true
    },
    {
      "id": "should-not-trigger-1",
      "prompt": "create a user story for the login feature",
      "should_trigger": false,
      "expected_agent": "living-doc-copilot"
    },
    {
      "id": "should-not-trigger-2",
      "prompt": "write a unit test for the login validator",
      "should_trigger": false
    }
  ]
}
```

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
```

`skill-creator` will propose candidate descriptions, score them against the eval set, and iterate.

### Body quality

```
Use the skill-creator skill to run the body evals for .github/agents/my-agent.agent.md
using .github/agents/evals/my-agent/evals.json.
```

Use the same with-skill / baseline comparison flow described in [skill-testing.md](./skill-testing.md).

---

## 6. Structural edits — use `agent-customization`

When body evals reveal a section is wrong (wrong scope, missing tool, bad handoff), use the `agent-customization` skill to fix the structural parts:

```
Use the agent-customization skill to add `mcp_microsoft_pla_browser_wait_for` to the tools list
in .github/agents/my-agent.agent.md.
```

```
Use the agent-customization skill to update the HEALING mode scope in
.github/agents/my-agent.agent.md — it should be scoped to failing tests only.
```

`agent-customization` understands `.agent.md` YAML frontmatter and section structure, so it handles these edits safely without breaking the file format.

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

**Good pattern** — explicit Triggers list with concrete phrases:
```yaml
description: >
  Bridge living documentation to executable tests. ... 
  Triggers: "scan webapp", "generate pageobjects", "heal pageobjects",
  "playwright crawl", "BDD pipeline", "crawl the UI".
```

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
gh copilot
→ "Use the skill-creator skill to test the agent at .github/agents/my-agent.agent.md
   using the evals at .github/agents/evals/my-agent/"
→ inspect trigger accuracy and body output diffs
→ use agent-customization to fix structural issues
→ "Use the skill-creator skill to optimize the description using the trigger-eval.json"
→ re-run evals until stable
```

---

For the full eval methodology (subagent spawning, benchmark aggregation, the viewer), see [skill-testing.md](./skill-testing.md) — the process is identical once the eval files are in place.
