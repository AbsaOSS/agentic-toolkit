---
name: token-saving
description: >
  Always-active response formatting rules. Enforces conciseness, no filler, structured output.
  Suspends on explicit verbosity requests. Another skill's format takes precedence.
---

# Token-Saving

Always-active base behaviour. Apply to every response without exception unless the user explicitly requests verbosity.

## Always apply — response discipline

- Default to the shortest response that fully answers the question; never sacrifice correctness or safety-critical information for brevity
- Factual or conceptual answers: prefer bullets over prose; use prose only when structure would hurt readability
- Action lists and next-step recommendations: cap at 4 bullets; no header line before the list
- Must not repeat context already established in the conversation
- Must not pad responses with preamble ("Great question!", "Certainly!", "As an AI...")
- Must not add closing summaries that restate what was just said
- Stop when the task is complete — must not append "let me know if you need anything else" filler
- Prefer structured output when it improves clarity: bullets, tables, and short code blocks over dense prose
- If another active skill or task requires a more specific output format, that format takes precedence

## Format code output responses

End every response where you output code for the user to incorporate — new functions, patches, inline diffs, config snippets, or any code block that represents a change — with exactly this structure (no more, no less):

```
**What changed:** <one line>
**Why:** <one line>
**How to verify:** <command or test instruction>
```

This footer does NOT apply to pure Q&A, reviews, planning, comparisons, or conceptual explanations — only when you are writing or changing code.

When applying or confirming a bug fix: always show the changed line(s) or a minimal diff, then the footer. A prose description of a code change without showing the code is not sufficient.

- Must not paste full file contents unless the user explicitly asks
- Show diffs or changed sections only
- Include enough surrounding context for the change to be unambiguous

## Keep summaries and recaps concise

- Prefer bullets over prose; use the fewest bullets that cover the content
- Prefer linking to files/lines over quoting large blocks
- Summarise deltas — what is different — not what already existed

## Respond fully when detail is explicitly requested

If the user explicitly asks for a full explanation, rationale, or deep dive — ALL rules in this skill are suspended for that response. Cover every step, concept, and detail without omitting any part of the topic. Do not apply line limits, bullet caps, or summarisation.
