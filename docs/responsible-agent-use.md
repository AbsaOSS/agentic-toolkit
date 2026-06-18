# Responsible AI Agent Use & Token Budget

A practical guide to not burning your **GitHub Copilot** budget in a handful of prompts. Covers where the
budget actually goes, how context, plugins, MCP servers, and skills affect cost, and a must-do checklist.

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
   in a conversation is re-sent (and re-billed) on **every turn**. A long chat is not free history; it is a
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
| **Input** | Everything sent to the model: your prompt, system instructions, chat history, pasted files, tool / MCP schemas | Base rate — cheapest per token, but usually the **largest volume** | Can be cached |
| **Output** | Everything the model generates: explanations, code, tool calls | **2–6× the input rate** (across Copilot's model menu the output spread is ~40×) | **Never** discounted by caching |
| **Cached input** | Input the model has already seen, served from a reused prefix | **~10% of the input rate** (a cache *read* is up to ~90% off) | This *is* the discount |

How it works:

- **Input** is re-sent on every turn — a 50-file context is billed as input on turn 1, turn 2, turn 3… This is
  where context discipline pays off most, because the volume is large and recurring.
- **Output** is the priciest per token. Generating a full rewritten file costs far more than generating a small
  diff, even when the input is identical. Caching never touches output.
- **Caching** lets the provider skip re-processing an unchanged prefix. A *cache read* is heavily discounted
  (~90% off input). Anthropic models add a small **cache write** premium (~1.25× input) the first time a prefix
  is cached; OpenAI caches automatically with no write surcharge. Caches are short-lived (Anthropic's default
  window is ~5 minutes of inactivity) and are invalidated the moment the cached prefix changes.

> On GitHub Copilot all three are metered at each model's API rate and converted to AI Credits (1 credit =
> $0.01). Inline code completion and Next Edit Suggestions stay **free**.

### Cut each one

**Input tokens — reduce the volume you resend**

- Keep context tight and task-scoped; reference `path:line`, don't paste whole files.
- Summarise large logs / JSON before feeding them in.
- Connect only the MCP servers you need — every server's tool schemas are input on *every* turn.
- Start a new conversation when the task changes, so old history stops being resent.

**Output tokens — generate less, and cheaper**

- Ask for **diffs / just the changed lines**, not full-file rewrites.
- Request concise answers; use a brevity skill like [`token-saving`](./token-saving.md) to kill filler output.
- Don't ask a model to echo back code you already have.
- For verbose, low-stakes generation, drop to a cheaper model — the output-rate spread between models is huge.

**Cached tokens — engineer for cache hits**

- Keep the **large, stable part of context first and unchanged** (system instructions, a big reference file) so
  it forms a reusable prefix; put the part that changes at the end.
- Within one task, keep working in the **same conversation** and reply promptly — caches expire after a few
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
| **Mode** | Inline completion, single-shot chat | Multi-step agent loops left running |
| **MCP servers** | 2-3 relevant servers | Many servers, each injecting tool schemas + data |
| **Code review** | Targeted, on real diffs | Auto-review on every push |

Everything below is about pulling these levers in the cheap direction without losing capability.

---

## Context: maintain it, then clear it

The single biggest cost driver is the **context window**. Every token in it is re-sent on every turn — so a
conversation that accumulates files, logs, and back-and-forth gets more expensive with each reply, even when
the new question is small.

**Maintain context deliberately:**

- Keep one conversation to **one task**. Scope creep = context creep.
- Paste **only the relevant lines**, not entire files. Reference `path:line` instead of dumping.
- Prefer the agent **reading** a file on demand over you pre-loading it "just in case."
- Summarise long outputs (logs, test runs, JSON) **before** feeding them in — process, don't paste raw.

**Clear context aggressively:**

- Start a **new conversation** when the task changes. Don't continue an old thread out of convenience.
- Use `/clear` (or the client equivalent) the moment a sub-task is done.
- If a thread has gone long and circular, **summarise the state into 5 lines, start fresh** with that summary.
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

## Agent mode: powerful, and the easiest way to overspend

Agent mode runs **multiple model turns per request** — it reads, plans, edits, and verifies in a loop. Each
loop iteration is billed.

- Give agents **narrow, well-specified tasks**. Vague goals cause exploratory wandering (= many turns).
- Provide constraints up front (files, acceptance criteria) so the agent doesn't burn turns discovering them.
- **Stop a runaway agent.** If it's looping or off-track, interrupt — don't let it spend to a dead end.
- Use single-shot chat for anything that doesn't genuinely need autonomous multi-step execution.

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
- Skills encode a workflow **once** so you don't re-explain it (and re-pay for it) in every conversation.
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

- [ ] One conversation = one task. New task → new conversation.
- [ ] Right model selected for the task (base for trivial, premium only when it earns it).
- [ ] Only the MCP servers / plugins needed for *this* work are connected.
- [ ] Relevant skills available (so you don't re-explain workflows).

**While working**

- [ ] Share `path:line` references, not whole-file dumps.
- [ ] Summarise large outputs (logs/JSON/test runs) before feeding them in.
- [ ] Give agents narrow, fully-specified tasks; stop them if they wander.
- [ ] Clear / start fresh the moment a sub-task is done.

**Hygiene & guardrails**

- [ ] Watch the context-window indicator; near-full = max cost per turn.
- [ ] Reserve auto code review for real diffs.
- [ ] Periodically audit connected MCP servers and installed plugins; remove the unused.

---

## TL;DR

> Tokens are the bill. Context size and model choice set the token count. Keep context tight, clear it often,
> connect only the MCP servers and plugins you need, let skills carry repeated workflows, and give agents narrow
> tasks.

---

## Sources

- [GitHub Copilot is moving to usage-based billing — GitHub Blog](https://github.blog/news-insights/company-news/github-copilot-is-moving-to-usage-based-billing/)
- [Models and pricing for GitHub Copilot — GitHub Docs](https://docs.github.com/en/copilot/reference/copilot-billing/models-and-pricing) (input / output / cached token rates per model)
- [GitHub Copilot AI Credits Are Live: A Cost Playbook — digitalapplied](https://www.digitalapplied.com/blog/github-copilot-ai-credits-billing-2026-cost-audit-playbook) (1 credit = $0.01; output-rate spread)
- [Prompt caching — Anthropic / Claude API Docs](https://docs.claude.com/en/docs/build-with-claude/prompt-caching) (cache read discount, cache write premium, TTL)
- [Prompt caching — OpenAI API Docs](https://platform.openai.com/docs/guides/prompt-caching) (automatic caching, input-only discount)
- [LLM API Pricing Comparison 2026 — CloudZero](https://www.cloudzero.com/blog/llm-api-pricing-comparison/) (input-vs-output multiples across providers)
- [Extending GitHub Copilot Chat with MCP servers — GitHub Docs](https://docs.github.com/en/copilot/how-tos/provide-context/use-mcp/extend-copilot-chat-with-mcp)
