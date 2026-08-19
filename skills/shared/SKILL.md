---
name: shared
description: >
  Internal library — not a task skill. Holds shared Python modules (skills/shared/lib/)
  and shared reference docs (skills/shared/references/) that other living-doc and BDD
  skills import or load, e.g. the canonical AC-ID grammar and entity-ID assignment logic.
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

Each dependent skill's own `sys.path` lookup (`Path(__file__).parent.parent.parent / "shared" / "lib"`)
is a relative sibling path, not a repo-absolute one — installing both skills into the same
skills root is what makes the import resolve after a standalone (single-skill) install.

See [lib/README.md](lib/README.md) for the module list (`living_doc_id.py`, `ac_tag.py`) and
the import pattern each consumer follows, and [references/](references/) for the shared
schemas and glossary docs.
