# Agent Design Best Practices

This guide distils Anthropic's engineering articles — [Building Effective Agents](https://www.anthropic.com/engineering/building-effective-agents) and [Effective Context Engineering for AI Agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) — into actionable rules for designing `.agent.md` files in this repository.

---

## Table of Contents

1. [Three core principles](#1-three-core-principles)
2. [Recommended file structure](#2-recommended-file-structure)
3. [Planning transparency](#3-planning-transparency)
4. [Tool list and tool guidance](#4-tool-list-and-tool-guidance)
5. [Inline examples](#5-inline-examples)
6. [Context management — just-in-time loading](#6-context-management--just-in-time-loading)
7. [Session state and note-taking](#7-session-state-and-note-taking)
8. [Stopping conditions](#8-stopping-conditions)
9. [Handoff contracts](#9-handoff-contracts)
10. [Repo conventions every agent must follow](#10-repo-conventions-every-agent-must-follow)

---

## 1. Three core principles

Anthropic's three design principles for agents, translated to this repo:

| Principle | What it means here |
|---|---|
| **Simplicity** | One agent = one clear concern. Never give an agent scope that belongs to a cooperating agent. Mode dispatch loads one skill at a time. |
| **Transparency** | The agent must narrate its plan before executing a multi-step task. See [§3](#3-planning-transparency). |
| **ACI — Agent-Computer Interface** | Every tool the agent can call must be understood from the agent body alone. See [§4](#4-tool-list-and-tool-guidance). |

---

## 2. Recommended file structure

Organise every `.agent.md` body in this order. Use `##` Markdown headers for each section.

```
description: (YAML frontmatter)
tools: (YAML frontmatter)

# @agent-name         ← one-line purpose + relationship to cooperating agents

## Initialisation      ← storage/seed setup; runs only when starting fresh
## Session State       ← note-taking schema; required if the agent runs multi-step tasks
## Mode Dispatch       ← routing table: intent → skill + scope (if agent is multi-modal)
## Scope               ← what this agent does
## Does NOT            ← explicit out-of-scope items with named agent responsible
## Tool Guidance       ← per-tool notes (usage, edge cases, common mistakes)
## Examples            ← 1–2 canonical inline few-shot examples
## [Domain conventions] ← reference data kept inline (small, stable, always needed)
## Skills              ← table with path and "When to load" column
## Operating rules     ← decision rules; use sub-headers, not a flat bullet list
## File editing protocol ← CLI constraint protocol (if agent runs in CLI context)
## Handoff             ← inbound and outbound structured payloads
```

**Altitude rule:** Instructions should sit in the Goldilocks zone — specific enough to guide behaviour, flexible enough to avoid brittle if-else hardcoding. Avoid encoding single-valued rules (e.g. `always use field X = "Y"`) in the agent body when they belong in the skill or the Storage Profile.

---

## 3. Planning transparency

Every agent **must** instruct itself to narrate its plan before executing any multi-step task:

```markdown
**Before executing any multi-step task:** State your plan in one sentence — name the
mode or skill you will use and your first concrete action. Then proceed.
```

This satisfies Anthropic's second principle ("prioritise transparency by explicitly showing planning steps") and helps users understand and correct the agent's interpretation before it acts.

---

## 4. Tool list and tool guidance

### `tools:` frontmatter

- List **individual tools** — not group aliases like `vscode` or `browser`.
- Only include tools the agent actually needs for its stated scope.
- An agent that explicitly states "Does NOT crawl web apps" must not list `browser/clickElement`, `browser/typeInPage`, etc.

### `## Tool Guidance` body section

Add a table with one row per key tool:

```markdown
| Tool | When to use | Key guidance |
|---|---|---|
| `read/readFile` | Load entity files before updating | Always read before writing — never assume current values. |
| `edit/editFiles` | Patch existing files | Read the full target block first. Show OLD vs NEW for `Active` entity changes. |
| `search/codebase` | Confirm code deletion before deprecating | Require negative result for at least two identifiers before assuming deleted. |
```

**Rule:** If a human engineer on your team couldn't immediately tell which tool to use in a given situation, the agent can't either. Add guidance until the choice is unambiguous.

---

## 5. Inline examples

Include **1–2 canonical few-shot examples** directly in the agent body. Examples are the most token-efficient way to convey expected output format and planning behaviour.

Format:

```markdown
## Examples

**Example 1 — <mode/scenario name>**

> User: <short prompt>

Agent plan: <one-sentence narration>

_(Brief description of what happens next.)_

Expected output:
\```<language>
<representative output snippet>
\```
```

**Rules:**
- Cover the most common trigger case and one error/edge case.
- Examples must use real entity ID patterns (`US-007`, `FEAT-003`, `AC:US-007-01`).
- Step text in Gherkin examples must use domain language — no selectors, HTTP references, or database terms.
- Do not stuff every edge case in — 2 canonical examples beat 10 exhaustive ones.

---

## 6. Context management — just-in-time loading

**Skills:** Load one skill per session, only when the mode is confirmed. Never pre-load skills for modes that haven't been triggered. The `Mode Dispatch` table must show which skill maps to each intent.

**Manifests and large files:** Always load with targeted line ranges for the route(s) in scope. Load the full file only for full re-scan operations.

**Reference docs:** Do not inline content that is available in a referenced file, unless it is small (< 30 lines) and needed across all modes. Use `[Load only if …]` annotations in the Skills table.

**Gap Finder modes:** Mode detail (what HEALING does, what PLAN does) belongs in the `living-doc-gap-finder` skill — not duplicated in the agent body. The agent body should name the mode and point to the skill.

---

## 7. Session state and note-taking

Any agent that runs multi-step tasks spanning many tool calls **must** define a session state file. This prevents context rot and enables resuming interrupted sessions.

**Minimum schema:**

```markdown
# <Agent> Session State
_Auto-managed. Delete when session complete._

## Goal
<!-- One sentence -->

## Progress
<!-- Per-item status: [ ] pending | [-] in progress | [x] done -->

## Decisions & Findings
<!-- Non-obvious discoveries — expensive to re-derive -->
```

**Rules:**
- Store at `.copilot/<domain>/.session-state.md` (dot-prefix; add to `.gitignore`).
- Update after every item completes.
- Append to `Decisions & Findings` for non-obvious discoveries only.
- Never store large data objects here — those belong in the artifact file (e.g. `manifest.json`).
- Delete the file when the session goal is fully achieved.

**Compaction trigger:** When context is nearing capacity, write a compaction summary (all unresolved items + key findings) to `Decisions & Findings`, then ask the user to start a new session and resume from the state file.

---

## 8. Stopping conditions

Every agent must define explicit escalation rules. At minimum include:

```markdown
**Stopping conditions — escalate to user when:**
- <domain-specific failure condition 1>
- <domain-specific failure condition 2>
- Context is nearing capacity — write compaction summary to session state, then ask the user to resume in a new session.
- More than 50 tool calls have been made without completing the session goal — pause, summarise progress, and ask how to proceed.
```

**Why the 50-call limit matters:** Anthropic recommends max iteration caps for autonomous agents. Without a limit, compounding errors can cause an agent to execute dozens of irreversible actions before the user can intervene.

---

## 9. Handoff contracts

Agent-to-agent handoffs must use **structured payloads**, not free-form prose. Both sides (outbound and inbound) must match.

```markdown
## Handoff

**Outbound to @other-agent:**
\```
Key: value
Key: value
\```

**Inbound from @other-agent:**
\```
Key: value
\```
```

**Rules:**
- Payloads must include entity IDs, state, version, and file paths where relevant.
- Never summarise loosely — use the exact payload format.
- If the target agent is not yet deployed, document with a `TODO: @agent-name` comment rather than omitting the handoff.

---

## 10. Repo conventions every agent must follow

### AC state vocabulary

All agents in this repository use the same four AC states. Never introduce alternative spellings.

| State | Meaning |
|---|---|
| `Planned` | Drafted; no implementation yet |
| `In Review` | Implementation underway or in PR |
| `Active` | Implemented and verified |
| `Deprecated` | Superseded or deleted; requires `deprecated_at` and `deprecation_reason` |

### Entity ID format

`US-<nnn>` · `FEAT-<nnn>` · `FUNC-<nnn>` · `AC:<parent-id>-<nn>`

IDs are stable — never change an ID after creation. Bump the `version` field for changes.

### Gherkin traceability tag format

```gherkin
# AC:US-007-01 (v1.0.0 - Active) — <description>
@AC:US-007-01
Scenario: ...
```

One `# AC:` + `@AC:` pair per AC. The `@AC:` tag is the machine-readable traceability anchor — never delete or rename it without syncing the catalog entity.

### Cooperating agent boundary

| Layer | Owner |
|---|---|
| Catalog (entities, ACs, traceability links) | `@living-doc-bdd-copilot` |
| Automation (PageObjects, step definitions, feature files) | `@living-doc-bdd-copilot` |

Never cross this boundary. When a task belongs to the other agent, hand off using the structured payload — do not attempt the task yourself.
