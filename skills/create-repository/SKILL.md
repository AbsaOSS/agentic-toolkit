---
name: create-repository
description: >
  Creates and configures a brand-new GitHub repository under the Absa organizations: AbsaOSS (open source)
  or absa-group (internal). Runs a short interactive interview, then an annotated gh command plan that
  creates the repo from the shared cps-repository-template (copies file structure) and, as part of that setup,
  adds theApache-2.0 license (open source repos), admins, a populated CODEOWNERS file, the standard Absa
  label taxonomy (cloned from the template), the ruleset, and auto-delete-branches, plus project
  links for internal repos. Use this whenever someone wants to create, spin up, scaffold, or
  set up a new repository, project, codebase, or service repo under AbsaOSS or absa-group. Even if they don't
  say "repository" explicitly. Do NOT use for modifying an existing repo (adding a single label, granting
  access on a repo that already exists, creating branches, pull requests, issues, or workflow files, or
  cloning). Use only for creating a new repository from scratch.
---

# Create Repository

Interactive: **interview** → **plan** → **confirm once** → **execute** → **report**.
The skill is done once the repository exists and is configured.

Keep every prompt short. Move fast: when the user says yes or accepts a suggested default, take it and go
straight to the next step — no extra deliberation or re-confirmation. Ask follow-ups only when an answer is
genuinely unclear; the interview is designed so that shouldn't be necessary.

Wherever a step accepts multiple values (admins, code owners, projects), let the user separate them however
is natural — commas or spaces — and figure out the split yourself. Don't burden the prompt with formatting rules.

Keep the whole skill simple and explicit so it runs reliably even on smaller models: plain sequential `gh`
commands, no clever scripts, no helper languages, no temp files.

The repo is created **from the shared template** `absa-group/cps-repository-template`. Templating copies only
the files on the template's default branch — README, CONTRIBUTING, `appid.json`, and the `.github/` folder
(GitHub workflows, dependabot, issue/PR templates, and an **empty** CODEOWNERS). It does **not** copy labels,
rulesets, repository settings, collaborators, or a license — those remain explicit steps.

## Step 0 — Preflight (before any questions)

Run `gh auth status`. If it exits non-zero, **stop immediately** and tell the user:

> This skill needs an authenticated GitHub CLI with org-admin permissions for AbsaOSS / absa-group.
> Set a `GITHUB_TOKEN` (or run `gh auth login`) with the right scopes, then re-run.

Do not probe individual scopes — permission problems surface on the specific call at execution time.

## The interview

Ask **exactly** these questions, in this order — the interview must be identical every time so the
experience is predictable. Items 1–4 are required; 5–6 are recommended (accepting the suggested option is
the fast path); 7 (project link) is asked only for internal repos.

**Copy, don't compose.** Each step below gives the exact text after `Ask:` and, where present, an exact
`Options:` list. Use that text **verbatim, character for character** — don't rephrase the question, don't
add your own parenthetical hints, don't invent a Yes/No framing that isn't already in the text below.
If a step has no `Options:` list, it's freeform — just ask the question and take the raw answer.

**Always included at creation (no questions asked):**

- The repo is created **from the `absa-group/cps-repository-template`**, which brings a **README** and the
  rest of the standard scaffolding — our repos must have at least README-level documentation.
- The **Apache-2.0** license on **OSS (`AbsaOSS`) repos only** — we always use it for open source. It's added
  as a `LICENSE` file right after creation (the `--template` flag can't also apply a license). Internal
  (`absa-group`) repos get no license (they're proprietary).
- The **Core Branches ruleset** on every repo — PR review with code-owner approval, the required "PR
  Requirements" check, signed commits, and no force-push/deletion on the default branch. Applied from the
  bundled `assets/rulesets.json`; not something the interview asks about.

The template auto-initializes the repo, so the default branch (`master`) exists before any configuration runs.

### 1. Visibility (required) → derives the org

Ask: "Is this repository open source or internal?" Options:

- `Open source — AbsaOSS (public)`
- `Internal — absa-group (private)`

Strict 1:1 mapping, no separate org question, no cross-combinations:

- open source → org `AbsaOSS`, `--public`
- internal → org `absa-group`, `--private`

### 2. Name (required)

Ask: "What should the repository be called? (e.g. aquasec-scan-results)"

Validate, in this order:

1. **kebab-case** is the one mechanical rule (`^[a-z0-9]+(-[a-z0-9]+)*$`). If it doesn't match, offer a
   friendly active fix using the normalized form (lowercase, `.`/spaces/camelCase boundaries → `-`):
   "Use of the kebab-case style is highly recommended, would you like `event-gate` instead?"
2. **Purpose & no people names** are advisory. A good name makes the repo's purpose clear to a first-time
   reader, pattern `<system>-<purpose>` (e.g. `aquasec-scan-results`), and contains no personal names. If
   the name looks non-descriptive or person-named, warn once, but accept it if the
   user insists. Only kebab-case gets the active fix; these are overridable nudges.

**Assist fallback (opt-in, never first):** only if the user is unsure, ask them to describe the repo's
purpose and propose 1–3 kebab-case `<system>-<purpose>` candidates.

Don't check name availability — a collision surfaces when `gh repo create` runs.

### 3. Admins (required, ≥1)

Ask: "Who should be repository admin? Enter one or more GitHub usernames."
Each becomes a repository admin.

### 4. Code owners (required, ≥1 user)

Ask: "Who should be the code owners?" Options:

- `Same people as the admins (@admin1, @admin2)`
- `Write a different set of code owners`

If the `Write a different set of code owners` option is chosen, ask: "Enter the GitHub usernames for
the code owners."

A single global `CODEOWNERS` rule covers all files. Individuals only — no teams.

### 5. Labels (recommended)

The full Absa label taxonomy lives on the template. Ask:
"Do you want to clone the standard Absa label set (can be found at
https://github.com/absa-group/cps-repository-template/labels)?" Options:

- `Yes, add proposed label set (recommended)`
- `No, keep the GitHub default label set`

All-or-nothing: yes clones the taxonomy with a single `gh label clone` from
`absa-group/cps-repository-template`; no keeps only GitHub's built-in defaults.

### 6. Auto-delete branches (recommended on)

Ask: "Auto-delete branches after merge?" Options:

- `Yes, auto-delete branches after merge (recommended)`
- `No, keep merged branches`

If yes, one PATCH sets `delete_branch_on_merge=true` on the repository.

### 7. Project link(s) — internal repos only (recommended, 0:n)

**Only ask this for internal (`absa-group`) repos.** GitHub forbids linking a repository to a project
owned by a different org, and all Absa projects live under `absa-group`.
So an OSS (`AbsaOSS`) repo can never link to them — **skip this step entirely for OSS repos**, don't even ask.

For internal repos, ask: "Which absa-group project(s) should this be linked to? Enter project number(s),
or press Enter to skip." Empty → skip.

## Build and confirm the plan

Present the plan **only for the steps that will actually run** — never list or mention steps that are
skipped (e.g. no project link on OSS repos; no license on internal repos). Don't explain what's being skipped or why.

Format the plan like this: a title line, then each step as a numbered plain-language sentence with its
command(s) in a fenced code block underneath. **Do not** write the descriptions as `#` comments inside the
code — the sentence goes above the block, the command goes in the block. Keep each description to one short
sentence; the user will ask if something is unclear.

```
Plan for repository `{owner}/{name}` creation ({OSS|internal})

The repository will be created based on the CPS repo template (https://github.com/absa-group/cps-repository-template),
which also brings the standard scaffolding: README, CONTRIBUTING, the GitHub workflows, the PR and issue
templates, the dependabot config, and appid.json (update appid.json with its repo's own Support
contact and AppIds before deploying).

1. Create the {public|private} repo from the template.
```
gh repo create {owner}/{name} --{public|private} --template absa-group/cps-repository-template
```

2. Add the Apache-2.0 LICENSE.                ← OSS repos only; omit the whole step otherwise
```
gh api -X PUT repos/{owner}/{name}/contents/LICENSE \
  -f message="Add Apache-2.0 license" \
  -f content="$(gh api /licenses/apache-2.0 --jq .body | base64)"
```

3. Grant @{admin} admin access.               ← one line per admin
```
gh api -X PUT repos/{owner}/{name}/collaborators/{admin} -f permission=admin
```

4. Set .github/CODEOWNERS to "* @{owner1} @{owner2}".
```
CO_SHA=$(gh api repos/{owner}/{name}/contents/.github/CODEOWNERS --jq .sha)
gh api -X PUT repos/{owner}/{name}/contents/.github/CODEOWNERS \
  -f message="Set CODEOWNERS" -f content="$(printf '* @{owner1} @{owner2}\n' | base64)" -f sha="$CO_SHA"
```

5. Clone the full Absa label taxonomy from the template.
```
gh label clone absa-group/cps-repository-template --repo {owner}/{name}
```

6. Apply the Core Branches ruleset.
```
gh api -X POST repos/{owner}/{name}/rulesets --input {skill-dir}/assets/rulesets.json
```

7. Auto-delete head branches after merge.
```
gh api -X PATCH repos/{owner}/{name} -F delete_branch_on_merge=true
```

8. Link the repository to project #{number}.  ← private repos only (one line per project); omit otherwise
```
gh project link {number} --owner absa-group --repo absa-group/{name}
```

Then ask one confirmation with these options: `Execute the plan` and there is by default Others.
Renumber the steps so they are sequential for whatever set actually applies (e.g. an internal repo has no
license step, so its steps still run 1, 2, 3, …).

## Execute

On confirmation, run **exactly the commands shown in the approved plan, verbatim** — the plan is the
contract. The user only agreed to what they saw, so don't run anything extra or surprising:

- **No helper languages or scripts** — no `python`/`python3 -c`, no `node`, no bash loops, no reading assets
  at runtime beyond the `--input {skill-dir}/assets/rulesets.json` already in the plan. Don't use `/tmp`.
- **No added output filters or parsing** — don't tack on `--jq`, `| grep`, `| head`, or similar that weren't
  in the planned command. Run each `gh` line as-is.
- **No extra read-back / verification calls** — don't call `.../collaborators/{u}/permission`, re-`GET` the
  repo, etc. Judge each step's success from its own exit status.
- **No proactive `sleep`s or waits, no pre-emptive conditional wrapping.** Run the CODEOWNERS `GET` exactly
  as planned, as its own plain command — don't wrap it in an `if`/retry script "just in case". Only if that
  call actually comes back 404 (template files still copying) do you react: run a plain `sleep 3`, then
  re-run the exact same `GET` command once, plain, before treating it as a failure. This reactive retry is
  the only deviation from "run the plan verbatim" that's ever allowed, and only fires after a real 404, not
  before.

The only runtime-dynamic pieces are the ones already visible in the plan — the `CO_SHA=$(...)` capture for
CODEOWNERS and the `content="$(gh api /licenses/apache-2.0 --jq .body | base64)"` substitution in the LICENSE
step. Everything else is a literal `gh` command.

- If `gh repo create` (step 1) fails, abort — there's nothing to configure. Report the error (often a name
  collision or a permissions problem).
- Everything after creation is independent. Use **best-effort**: if a call fails, keep going and collect the
  failure. `gh label clone` already skips labels that exist; a ruleset that already exists (HTTP 422) is fine.

End with **exactly** the block below and nothing else — no leading line like "All steps succeeded", no
trailing commentary, no summary sentence before or after it. Output only the title line, a blank line, the
results table listing **only the steps that ran** (no skipped rows), a blank line, then the template link, in
that literal order, every time. For example (an OSS repo — no project-link row):

```
Repository `cps-test-repo` successfully created via /create-repository skill

| Step                          | Result                                        |
| ----------------------------- | --------------------------------------------- |
| Create repo                   | ✓ https://github.com/AbsaOSS/cps-test-repo    |
| Apache-2.0 license            | ✓                                             |
| Admin                         | ✓ @admin-dev                                  |
| CODEOWNERS                    | ✓ * @admin-dev                                |
| Labels                        | ✓ Cloned from template                        |
| Core Branches ruleset         | ✓                                             |
| Auto-delete branches on merge | ✓                                             |

Template: https://github.com/absa-group/cps-repository-template
```

For internal repos, add a Link to project row e.g. `| Linked project | ✓ #203 |`. If a
step failed, show ✗ with a short reason on that row so the user can fix it manually.
