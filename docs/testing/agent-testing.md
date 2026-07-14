# Agent Testing Guide

This document describes how to test, evaluate, and tune `.agent.md` files by validating body output quality through manual testing. This is the practical equivalent of [skill-testing.md](./skill-testing.md) applied to agents, but simpler because agents are manually invoked (no auto-triggering to test).

---

## Why agent testing is different from skill testing

| Dimension | Skill | Agent |
|---|---|---|
| Trigger mechanism | `description:` field in SKILL.md YAML — auto-matched | `@agent-name` mention in Copilot Chat — manual |
| Body loaded when? | When skill description matches your prompt | When user explicitly @-mentions the agent name |
| What to tune | Description keywords for activation + body instructions | Body sections (scope, handoff, modes); description for documentation only |
| Tool for eval loop | `skill-creator` (optimize trigger descriptions) | Manual testing (invoke with `@agent-name` and verify outputs) |

The key insight: an agent's `description:` is **documentation only** — it does not affect invocation. Unlike skills (auto-triggered by description match), agents require explicit `@agent-name` mention. Use the `description:` field to document the agent's purpose and scope for users.

---

## 1. Recommended workflow

Since agents are invoked explicitly via `@agent-name` (not by description matching), skip trigger evals and focus on body quality:

1. Create body eval cases in `.github/agents/evals/<agent-name>/evals.json`
2. Start a Copilot Chat session from the repository root
3. Invoke the agent with `@agent-name` and test the prompts from your evals
4. Review output quality against expected results
5. Edit structural sections directly in the `.agent.md` file (tools list, scope, handoff, modes)
6. Re-run evals; repeat until stable

> Note: The `description:` field in `.agent.md` is for documentation/help text only — it does not affect invocation. Update it to clearly state the agent's purpose and scope.

---

## 2. File layout

```
.github/
  agents/
    my-agent.agent.md          ← agent definition
    evals/
      my-agent/
        evals.json             ← body behavior tests
        files/                 ← fixture files referenced by evals
```

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

## 4. Running body evals

When testing your agent, manually invoke it with `@agent-name` using the prompts from `evals.json`:

```
@my-agent I want to set up BDD automation for our app at https://app.example.com. 
The Angular router is at src/app/app-routing.module.ts.
```

Verify the output against the `expected_output` field. Repeat for each eval case until all pass.

**What to validate:**

1. All body-referenced tools are present in the frontmatter `tools:` list
2. Mode dispatch (e.g., RE-SCAN, HEALING) activates correctly when mode keywords appear in the prompt
3. Scope boundaries match the `## Scope` and `## Does NOT` sections
4. Handoff targets are correct when the agent needs to delegate work

> Tip: If an eval expects a tool that's not available, add it to the `.agent.md` frontmatter `tools:` list. If scope is wrong, edit the relevant section (`## Scope`, `## Does NOT`, or a specific mode block).

---

## 5. Structural edits

When body evals reveal a section is wrong (wrong scope, missing tool, bad handoff), edit the `.agent.md` file directly:

- **Missing tool** — add the tool name to the `tools:` list in the YAML frontmatter
- **Wrong scope boundary** — update the relevant section (`## Scope`, `## Does NOT`, or the specific mode block)
- **Broken handoff** — update the `## Handoff` section with the correct target agent and conditions

---

## 6. What to tune — agent-specific checklist

| Check | Good signal | Bad signal |
|---|---|---|
| **Scope boundaries** | Refuses work outside its Does-NOT list | Silently attempts work outside its scope |
| **Mode activation** | RE-SCAN / HEALING / REMOVE activate on correct triggers | Wrong mode fires, or modes don't activate |
| **Handoff clarity** | Outputs correct hand-off message to the right agent | Hands off to wrong agent or swallows the work |
| **Tool completeness** | All tools needed by the body are in the frontmatter `tools:` list | Body references a tool not in `tools:` — it will be unavailable |
| **Description clarity** | Description field clearly explains agent purpose and usage | Description is vague or misleading about scope |

---

## 7. Description best practices

Since the `description:` field is documentation-only (not an activation trigger), use it to communicate the agent's purpose, domain, and key scope boundaries to users:

**Good pattern:**

```yaml
description: >
  Lifecycle for living documentation and BDD automation.
  Create/update User Stories, Features, Functionalities; generate Gherkin scenarios;
  scan webapp for PageObjects; manage test artifacts.
  Use @-mention: @living-doc-bdd-copilot COMMAND.
  NOT for: unit tests, production code, security/perf review.
```

**Bad patterns:**

```yaml
# BAD — vague, doesn't explain domain or usage
description: >
  Helps with testing and documentation.

# BAD — talks about auto-triggering (agents use @-mention only)
description: >
  Automatically activated when you describe BDD tasks.

  Living documentation catalog (User Stories, Features, Functionalities, ACs, impact
  analysis, gap finding) and BDD automation (Playwright crawl/explore/scan, PageObjects
  create/heal, Gherkin scenarios/feature files/step definitions, living-doc sync,
  scenario coverage). Setup: seed.yaml → manifest.json, credential checks, guided
  traversal. NOT for: unit tests, production code, API specs, CI/CD, debugging,
  performance, security.
```

The `NOT for:` clause is as important as the positive terms — it prevents the agent from firing on adjacent-but-out-of-scope requests. An explicit `Triggers:` keyword list is not required; structured domain nouns and verbs are sufficient for the matching mechanism to work.

---

## 9. Body eval iteration loop

Repeat until all body evals pass:

1. Invoke the agent with `@agent-name` using a prompt from `evals.json`
2. Review output against the `expected_output` field
3. If output doesn't match, identify the root cause:
   - **Wrong tool?** — add the missing tool to the `tools:` list in the frontmatter
   - **Wrong scope?** — update the `## Scope` or `## Does NOT` section
   - **Mode didn't activate?** — fix the mode dispatch logic (e.g., RE-SCAN, HEALING keywords)
   - **Bad handoff?** — correct the `## Handoff` section
4. Edit the `.agent.md` file directly with the fix
5. Re-run that eval case
6. Move to the next eval case; repeat until all pass

**Tip:** Run body evals in order (easiest first) to catch missing tools early before diving into scope or mode issues.

---

For the full eval methodology (subagent spawning, benchmark aggregation, the viewer), see [skill-testing.md](./skill-testing.md) — the process is identical once the eval files are in place.
