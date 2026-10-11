<!-- What problem does it solve or what feature does it add? -->
## Overview

Deletes the living-doc part of this repository. It now lives in `AbsaOSS/living-doc` under `agentic/`, next to
the canon it writes, and ships from there: `AbsaOSS/living-doc#53`.

Complete removal — no pointer, no redirect, no stub folder. Anyone looking for these skills finds them in
`living-doc`'s `README.md` and in its `agentic/README.md`.

Why now: two copies of the same skills existed, and this one reads canon references pinned to a `living-doc`
commit that has since moved on, so its copies are stale and would drift further with every canon change. A user
installing from here would get skills that disagree with the canon. `#40` was closed rather than merged, so
`master` never received the canon alignment — what is here is the older state, with nothing to preserve.

<!-- Summarize the key changes in the Pull Request. -->
## Key Changes

- **104 files deleted.** The nine living-doc skills, the three BDD skills the agent used
  (`data-cy-instrument`, `gherkin-step`, `bdd-maintain`), all of `skills/shared/`, the
  `living-doc-bdd-copilot` agent with its evals, the 13 guides for them, and
  `.github/workflows/test-scripts.yml`.
- **13 skills and 10 guides remain**, and they are untouched.
- **Six pages edited** (+22 / −136 lines): the skill catalog, the docs index, the contributing examples, the
  getting-started walkthrough, and the two agent guides.

### Why `skills/shared/` goes whole

On `master` it held nothing but living-doc material: `SKILL.md`, `lib/` (`ac_tag.py`, `living_doc_id.py` and
their two tests) and `references/` (two canon copies plus three JSON schemas). Nothing outside the deleted
skills referenced `shared/lib` or `shared/references` — `git grep -l -e shared/lib -e shared/references --
skills/` over the skills that stay returns nothing.

There was **no canon sync script on `master`**: `scripts/sync-living-doc-reference.sh` only ever existed on the
closed `#40` branch, so the two canon copies here were hand-maintained and stale. They go with `shared/`.

### Why the test workflow goes

`test-scripts.yml` has one job: it discovers `skills/**/test_*.py` and runs each file. After this deletion **no
`test_*.py` file remains anywhere under `skills/`**, so the job would pass on an empty set and report green. A
workflow that tests nothing is worse than no workflow. `check-pr-requirements.yml` is now the only workflow, and
it references no path under `skills/`.

### What changed on the six pages

| File | Change |
|---|---|
| `README.md` | 12 catalog rows removed. The **Agent Roster** section is removed with them: `living-doc-bdd-copilot` was the only agent, so the section would have been a heading over an empty table. The FAQ entry explaining skills versus agents stays. |
| `docs/README.md` | The **Agent Guides** section and the **Living Documentation & BDD Skills** section with its three sub-sections are removed, along with their entries in Contents. |
| `CONTRIBUTING.md` | The shared-reference and shared-utility guidance stays; its examples no longer name deleted files. The shared-module convention — a thin wrapper per dependent skill, a `README.md` recording consumers — is now stated directly instead of by reference. |
| `docs/getting-started.md` | The **Install Agents** section is removed: it told readers to copy an agent file that no longer exists, and linked the removed Agent Roster anchor. |
| `docs/guides/agent-design.md` | Kept, re-illustrated. The mode-detail rule and the cooperating-agent boundary are now stated generically instead of through the living-doc agent. |
| `docs/testing/agent-testing.md` | Kept, re-illustrated. The good and bad `description:` examples use a release agent. |

`agent-design.md` and `agent-testing.md` teach how to write any `.agent.md` and only *illustrated* the point
with the living-doc agent, so the guidance stays and the examples changed. `.github/agents/` is now empty, which
matches the README's own scope statement: agents are something this repository may host, not something it ships
today.

### Verification

```
$ git grep -il -e living-doc -e living_doc -e bdd-maintain -e gherkin-step -e data-cy-instrument -e bdd-copilot
(no matches)

$ ls skills | wc -l          # 13
$ ls docs/guides | wc -l     # 10
$ ls -A .github/agents       # gone
$ ls .github/workflows       # check-pr-requirements.yml
$ git ls-files skills/ | grep "test_.*\.py"
(no matches — which is why the test workflow is removed)
```

No relative link in any Markdown file is broken, and no workflow references a deleted path.

One check for the reviewer: three skills are missing from the `README.md` catalog —
`create-issue`, `create-repository-workspace` and `python-standards`. All three were already missing before this
change; this PR adds no fourth. The `create-repository` row was briefly lost while editing and has been restored
from `master` verbatim.

<!-- Add attached issue that this PR solves. -->
## Related
Closes #44
