# Responsible AI Agent Use & Token Budget

A practical guide to not burning your **GitHub Copilot** budget in a handful of prompts. Written for
**agent-mode work** — where the agent reads, edits, and verifies in a loop, which is how most engineering with
Copilot now happens and where the budget goes fastest. Covers where the budget actually goes, and how agent
mode, context, sub-agents, MCP servers, plugins, and skills each affect cost — plus a must-do checklist.

---

## Why this matters: how the cost works

As of **June 1, 2026**, GitHub Copilot bills by **usage**, not by a flat request count. Work is charged by
**per-token model pricing** — but not every token costs the same. An interaction is billed as:

```
(input tokens × input_rate) + (output tokens × output_rate) + (cached input × cached_rate)
```

Input, output, and cached tokens each carry a **different rate**, and the rate also depends on the model. The
[next section](#token-types-what-youre-actually-paying-for) breaks the three apart; the discipline in this guide
follows from three facts:

1. **Cost scales with tokens**, and input tokens scale with **how much context you carry** — every input token
   in a session is re-sent (and re-billed) on **every turn**. A long session is not free history; it is a
   recurring charge.
2. **The model is a multiplier.** A premium reasoning model on a trivial task costs many times what a base
   model would.
3. **The token *type* matters.** Output tokens cost several times more than input; cached input costs a
   fraction. The bill depends not just on *how many* tokens but *which kind*.

Inline code completion (autocomplete) and Next Edit Suggestions are **free** — they don't consume credits.
**Chat, agent mode, and code review** are the expensive part, because they push large context through capable
models, repeatedly.

> A bloated context window sent to a premium model on every turn is how a budget disappears in a few queries.

---

## Token types: what you're actually paying for

Every interaction is billed across three kinds of token, each at a **different rate**:

| Token type | What it is | Relative cost | Caching |
|------------|------------|---------------|---------|
| **Input** | Everything sent to the model each turn: your prompt, system + instruction files, the running history, **every file the agent reads and every command / tool result it captures**, plus tool / MCP schemas | Base rate — cheapest per token, but usually the **largest volume** (agent loops inflate it fast) | Can be cached |
| **Output** | Everything the model generates: reasoning, edits, tool calls — **on every turn of the loop** | **2–6× the input rate** (across Copilot's model menu the output spread is ~40×) | **Never** discounted by caching |
| **Cached input** | Input the model has already seen, served from a reused prefix | **~10% of the input rate** (a cache *read* is up to ~90% off) | This *is* the discount |

How it works:

- **Input** is re-sent on every turn, and in agent mode it compounds: each file the agent reads and each command
  output it captures stays in context and is re-billed on every later turn. A ten-step agent task pays for its
  early file reads ten times over. This is where context discipline pays off most.
- **Output** is the priciest per token, and an agent emits output **every turn** — reasoning, tool calls, and
  edits across the whole loop. Targeted edits cost far less than rewriting whole files; a long autonomous run on
  a vague goal is mostly output you pay a premium for. Caching never touches output.
- **Caching** lets the provider skip re-processing an unchanged prefix. A *cache read* is heavily discounted
  (~90% off input). Anthropic models add a small **cache write** premium (~1.25× input) the first time a prefix
  is cached; OpenAI caches automatically with no write surcharge. Caches are short-lived (Anthropic's default
  window is ~5 minutes of inactivity) and are invalidated the moment the cached prefix changes.

> On GitHub Copilot all three are metered at each model's API rate and converted to AI Credits (1 credit =
> $0.01). Inline code completion and Next Edit Suggestions stay **free**.

### Cut each one

**Input tokens — control what the agent pulls into context**

- **Scope the agent.** Point it at the specific files or folders the task touches, not "the repo." The narrower
  the scope, the less it reads in.
- Let the agent **read on demand**, but steer it **off huge or generated files** (lockfiles, build output,
  vendored code) it doesn't need.
- Keep a **project instructions file** (e.g. `.github/copilot-instructions.md`) so you don't re-explain
  conventions every session — written once, it loads as a stable, cacheable prefix.
- Prefer **search / grep** over having the agent read whole files when it only needs a few symbols.
- Connect only the MCP servers you need — every server's tool schemas are input on *every* turn.
- Start a new session when the task changes, so old reads and history stop being resent.

**Output tokens — make the agent generate less**

- Steer the agent toward **targeted edits**, not rewriting whole files it could patch in place.
- **Bound the loop:** give acceptance criteria so it stops when done instead of polishing, and interrupt a run
  that's spiralling — every extra turn is more output.
- Use a brevity skill like [`token-saving`](./token-saving.md) to cut filler from the agent's prose.
- Don't have the agent echo back code or files it already has in context.
- For verbose, low-stakes work, drop to a cheaper model — the output-rate spread between models is huge.

**Cached tokens — engineer for cache hits**

- Keep the **large, stable part of context first and unchanged** (system instructions, a big reference file) so
  it forms a reusable prefix; put the part that changes at the end.
- Within one task, keep working in the **same session** and reply promptly — caches expire after a few
  minutes of inactivity, and editing early context invalidates the cache.
- This is the one place where *not* clearing helps: clear when the **task** changes, but during a task a stable
  prefix earns the cache discount on every follow-up turn.

---

## Where the budget actually goes

Five levers account for nearly all avoidable spend:

| Lever | Cheap | Expensive |
|-------|-------|-----------|
| **Context size** | Tight, task-scoped context | Whole repo / long history resent every turn |
| **Model choice** | Base / lightweight model | Premium reasoning model for trivial tasks |
| **Agent loop** | Bounded task, named files, a clear stop condition | Open-ended loop on a vague, repo-wide goal |
| **MCP servers** | 2-3 relevant servers | Many servers, each injecting tool schemas + data |
| **Code review** | Targeted, on real diffs | Auto-review on every push |

Everything below is about pulling these levers in the cheap direction without losing capability.

---

## Context: maintain it, then clear it

The single biggest cost driver is the **context window**. Every token in it is re-sent on every turn — so a
session that accumulates files, logs, and back-and-forth gets more expensive with each reply, even when the new
question is small.

**Maintain context deliberately:**

- Keep one session to **one task**. Scope creep = context creep.
- **Scope what the agent can read** — name the files or folders in play so it doesn't wander the whole tree.
- Let the agent read on demand, but steer it **off huge or generated files** (lockfiles, build logs, vendored
  code) that bloat context without helping.
- When a step produces a wall of output (full test run, verbose build), have the agent **run it narrowly** (one
  test, one package) so it doesn't ingest and then re-send megabytes of logs every later turn.

**Clear context aggressively:**

- Start a **new session** when the task changes. Don't continue an old one out of convenience.
- Use `/clear` (or the client equivalent) the moment a sub-task is done.
- If a session has gone long and circular, **summarise the state into 5 lines, start fresh** with that summary.
- Watch for context warnings — a near-full window means you're paying maximum tokens on every reply.

> Rule of thumb: if you can't say why a piece of text needs to be in context **right now**, it's costing you.

> **Caching caveat:** clear between *tasks*, not on every turn of the same task. Mid-task, a stable unchanged
> context prefix earns the cache discount — see
> [Token types](#token-types-what-youre-actually-paying-for).

---

## Models: match the model to the task

Per-token pricing means model choice is a direct cost multiplier.

- **Trivial / mechanical** (rename, format, boilerplate, simple Q&A) → base or lightweight model.
- **Hard reasoning** (architecture, tricky bugs, multi-file refactors) → premium model, deliberately.
- Don't leave a premium model selected as your default for everything.
- One well-scoped premium query beats five vague ones that each resend a fat context.

---

## Agent mode: the default — and where most budget goes

Agent mode is how most work happens now: the agent **reads, plans, edits, and verifies in a loop**, many model
turns per request. It's also where budget evaporates, because every turn re-sends the accumulated context
(input) and emits fresh reasoning and edits (output). The fix isn't to avoid agent mode — it's to run it
**bounded and well-scoped**.

- **Scope tightly.** Name the files, folder, or component the task touches. An agent told "fix the repo" reads
  far more than one told "fix the validation in `auth/login.ts`."
- **Plan before editing.** For anything non-trivial, have the agent produce a short plan first, confirm it, then
  execute. A wrong direction caught in the plan costs a few hundred tokens; caught after ten edit-verify turns,
  it costs thousands.
- **Give a stop condition.** State acceptance criteria so the agent knows when it's done and doesn't keep
  polishing.
- **Watch verification cost.** Running the full test suite or build on every loop dumps large output into
  context each time. Point the agent at the **targeted test or package** for the change.
- **Stop a runaway.** If it's looping, re-reading the same files, or off-track, interrupt — don't let it spend
  to a dead end.
- **Reuse the session** for tightly related steps, so the stable prefix (instructions, already-read files) stays
  cached; start fresh when the task genuinely changes.

---

## Sub-agents: isolate heavy work, keep the main context lean

A **sub-agent** is a separate agent instance the main agent spawns to handle a focused subtask. It runs in its
**own context window**: it reads files, runs searches, and produces tool output in isolation, then returns
**only a compact summary or result** to the main thread. The intermediate noise — the file reads, the search
hits, the verbose command output — stays inside the sub-agent and never enters the main conversation.

> **Availability varies by tool.** Native sub-agent spawning is built into harnesses like Claude Code; in GitHub
> Copilot the same idea surfaces through custom agents and orchestration features. The token figures below come
> from the Claude ecosystem but the principle is general — isolate a subtask in its own context, return only the
> result — and applies wherever your tool supports it.

Why it protects the budget: the expensive thing in agent mode is context that **accumulates and is re-sent on
every turn**. Offload a read-heavy subtask and those tokens are paid **once**, inside the sub-agent, then
discarded — the main thread only ever carries the summary, instead of dragging the whole investigation through
every subsequent turn.

**Good candidates to delegate:**

- Large codebase searches / "where is X used" sweeps across many files.
- Log, test-output, or data analysis that produces a wall of text you only need a conclusion from.
- Multi-file investigation where only the *finding* matters to the downstream task.

**The catch — sub-agents are not free.** Each one opens its own context window and re-establishes its own setup,
so spawning them carelessly can cost *more*, not less. Anthropic reports that a single agent uses roughly **4×**
the tokens of a plain chat, and multi-agent systems about **15×**. The saving is real only when delegation
**replaces** context that would otherwise pile up in the main thread — or when the sub-agent runs a cheaper
model.

**Use them well:**

- Delegate **self-contained, read / search / analysis-heavy** tasks; have the sub-agent return a **tight
  summary**, not raw dumps.
- Pass **scoped context in** (the specific question plus the few files it needs), not the whole history — a
  structured hand-off is hundreds of tokens; forwarding the full conversation is thousands.
- Run workers on a **cheaper model** (premium orchestrator, lightweight workers) — reported 5–10× cost cuts at
  similar quality.
- Don't fan out sub-agents for trivial work; below a certain size the per-agent overhead outweighs the saving.

> Rule of thumb: delegate to a sub-agent when a subtask's **intermediate** tokens dwarf its **answer**. You pay
> for the work once and keep only the answer.

---

## MCP servers: every connected server has a standing cost

Model Context Protocol (MCP) servers extend Copilot Chat with external tools and data. Useful — but each
connected server injects its **tool definitions (schemas) into context**, and tool **results** add more tokens
on top.

- Connect **only the MCP servers you need for the current work.** Disconnect the rest.
- Prefer servers that return **focused, filtered** results over ones that dump large payloads.
- 8 servers each advertising 10 tools = a large fixed context tax on **every** turn, before you ask anything.
- Audit periodically — remove servers you stopped using.

---

## Skills & plugins: spend tokens once, save them every turn

**Skills** are loadable instruction bundles (like those in this repo). Used well, they are net **token savers**:

- A skill like [`token-saving`](./token-saving.md) trims filler from every response — pure savings.
- Skills encode a workflow **once** so you don't re-explain it (and re-pay for it) in every session.
- They load **on demand** when a task matches, so a large library doesn't tax context until it's relevant
  (see [What Is a Skill?](./getting-started.md#what-is-a-skill) for the loading model).

**Plugins** bundle skills, agents, and MCP servers into one install. The convenience hides a cost: a plugin may
auto-connect MCP servers or auto-load context you didn't ask for.

- Install plugins **deliberately**; review what each one connects or loads.
- A plugin that auto-attaches several MCP servers is several standing context taxes — know before you install.
- Disable plugin features you don't use.

---

## The must-do checklist

Run through this before and during any non-trivial Copilot session.

**Before you start**

- [ ] One session = one task. New task → new session.
- [ ] Right model selected for the task (base for trivial, premium only when it earns it).
- [ ] Only the MCP servers / plugins needed for *this* work are connected.
- [ ] Relevant skills available (so you don't re-explain workflows).

**While working (agent mode)**

- [ ] Scope the agent to the files / folders in play — not "the repo."
- [ ] Plan-then-execute for non-trivial tasks; confirm direction before it edits.
- [ ] Give a clear stop condition; interrupt loops that wander or re-read.
- [ ] Run targeted tests / builds, not the full suite, on each verify step.
- [ ] Delegate heavy read / search / analysis to a sub-agent; keep only its summary in the main thread.
- [ ] Start a fresh session when the task changes.

**Hygiene & guardrails**

- [ ] Watch the context-window indicator; near-full = max cost per turn.
- [ ] Reserve auto code review for real diffs.
- [ ] Periodically audit connected MCP servers and installed plugins; remove the unused.

---

## TL;DR

> Tokens are the bill. In agent mode every loop re-sends context (input) and emits edits (output), so cost
> compounds with scope and loop length. Scope the agent to the files in play, plan before it edits, give it a
> stop condition, run targeted tests, connect only the MCP servers you need, and let skills and an instructions
> file carry the repeated context. Delegate heavy read/search subtasks to sub-agents so their noise stays out of
> the main thread. Clear between tasks, not mid-task.

---

## Sources

- [GitHub Copilot is moving to usage-based billing — GitHub Blog](https://github.blog/news-insights/company-news/github-copilot-is-moving-to-usage-based-billing/)
- [Models and pricing for GitHub Copilot — GitHub Docs](https://docs.github.com/en/copilot/reference/copilot-billing/models-and-pricing) (input / output / cached token rates per model)
- [GitHub Copilot AI Credits Are Live: A Cost Playbook — digitalapplied](https://www.digitalapplied.com/blog/github-copilot-ai-credits-billing-2026-cost-audit-playbook) (1 credit = $0.01; output-rate spread)
- [Prompt caching — Anthropic / Claude API Docs](https://docs.claude.com/en/docs/build-with-claude/prompt-caching) (cache read discount, cache write premium, TTL)
- [Prompt caching — OpenAI API Docs](https://platform.openai.com/docs/guides/prompt-caching) (automatic caching, input-only discount)
- [LLM API Pricing Comparison 2026 — CloudZero](https://www.cloudzero.com/blog/llm-api-pricing-comparison/) (input-vs-output multiples across providers)
- [Extending GitHub Copilot Chat with MCP servers — GitHub Docs](https://docs.github.com/en/copilot/how-tos/provide-context/use-mcp/extend-copilot-chat-with-mcp)
- [How we built our multi-agent research system — Anthropic](https://www.anthropic.com/engineering/multi-agent-research-system) (single agent ~4× / multi-agent ~15× chat token usage)
- [Subagents in the SDK — Claude Code Docs](https://code.claude.com/docs/en/agent-sdk/subagents) (isolated context window, summary-only return)
- [Why Claude Code Subagents Burn So Many Tokens — youcanbuildthings](https://youcanbuildthings.com/articles/claude-code-subagents-token-usage/) (per-agent overhead caveat)
