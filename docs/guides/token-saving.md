# Token-Saving Skill

The `token-saving` skill enforces concise, low-noise AI responses. It is **always active** — it applies to every reply without needing to be triggered by a specific phrase.

---

## What it changes

Without the skill, AI assistants commonly pad responses with filler openers, closing platitudes, and repeated context. This skill removes that noise.

| Behaviour | Without skill | With skill |
|-----------|--------------|------------|
| Response opener | "Great question! Certainly, I'd be happy to help..." | Directly answers |
| Closing | "Let me know if you have any questions!" | Stops when done |
| Repeated context | Restates what you just said | Skips it |
| Factual answers | Unlimited prose | ≤ 5 lines |
| Action lists | Unlimited bullets | Capped at 4 |
| Full file dumps | Common | Only when you ask |

---

## Code output footer

Every response that writes or changes code ends with exactly this footer — no more, no less:

```
**What changed:** <one line>
**Why:** <one line>
**How to verify:** <command or test instruction>
```

This applies to: new functions, patches, inline diffs, config snippets, or any code block representing a change.

It does **not** apply to: Q&A, reviews, planning, comparisons, or conceptual explanations.

---

## Overriding the skill

The brevity rules suspend for a single response when you explicitly ask for depth:

> "Give me a full explanation."
> "Deep dive into this."
> "Don't hold back."
> "Complete explanation."

The next response is fully unrestricted. Rules resume after that.

---

## Precedence

If another active skill specifies its own output format (e.g. a review skill with a Blocker / Important / Nit structure), that format takes precedence over this skill's rules.

---

## Installation

The skill is installed along with the rest of the toolkit:

```bash
npx skills add https://github.com/AbsaOSS/agentic-toolkit -g
```

To install only this skill:

```bash
npx skills add https://github.com/AbsaOSS/agentic-toolkit -g --skill token-saving
```

See [Getting Started](../getting-started.md) for the full install guide.
