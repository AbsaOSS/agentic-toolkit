---
name: shared
description: >
  Internal reference bundle — not a task skill. Holds shared reference docs
  (skills/shared/references/) that other skills load, including the ngx-ui-watchtower API.
  Do not activate this for a user request; it has no standalone behavior of its own.
  Install it alongside any skill whose own SKILL.md names it as a required companion —
  the consuming skill's install instructions list the exact command.
license: Apache-2.0
---

# shared

This is not a task skill — it has no workflow of its own and should never be selected to
handle a user request. It exists so this folder is a normal, installable, name-matching
skill unit (per `CONTRIBUTING.md`'s one-dir-one-skill convention), which lets it be
installed as a **sibling** directory alongside any skill that depends on it:

```bash
npx skills add https://github.com/AbsaOSS/agentic-toolkit -g --skill <dependent-skill>
npx skills add https://github.com/AbsaOSS/agentic-toolkit -g --skill shared
```

Dependent skills load the references they need from this sibling directory. See
[references/](references/) for the shared API documentation.
