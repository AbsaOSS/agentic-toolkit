# Create Repository Skill

The `create-repository` skill creates and configures a brand-new GitHub repository under the Absa
organizations — **AbsaOSS** (open source) or **absa-group** (internal) from the shared
`cps-repository-template`. It applies the standard Absa CPS guardrails so every new repo starts consistent.

---

## What it does

It runs a short interactive flow and never makes changes until you confirm:

**interview → plan → confirm once → execute → report**

| Phase | What happens                                                                                                  |
|-------|---------------------------------------------------------------------------------------------------------------|
| Interview | Asks a fixed set of short questions (visibility, name, admins, code owners, labels, auto-delete, project link) |
| Plan | Shows the exact annotated `gh` commands it will run                                 |
| Confirm | You approve the plan once                                                                                     |
| Execute | Runs the approved commands verbatim, best-effort                                                              |
| Report | Prints a results table with the repo URL and what was copied from the template                                |

The repo is created from `absa-group/cps-repository-template`, which brings a README, CONTRIBUTING,
and the `.github/` folder (workflows, dependabot, issue/PR templates, and an empty CODEOWNERS).

Template link: [absa-group/cps-repository-template](https://github.com/absa-group/cps-repository-template)
c
---

## What it always applies

| Item | OSS (`AbsaOSS`) | Internal (`absa-group`) |
|------|-----------------|--------------------------|
| Created from `cps-repository-template` | ✓ | ✓ |
| Apache-2.0 license | ✓ | — (proprietary) |
| Populated CODEOWNERS | ✓ | — (template's empty file) |
| Standard Absa label taxonomy | ✓ | ✓ |
| Core Branches ruleset | ✓ | ✓ |
| Auto-delete branches on merge | ✓ | ✓ |
| Custom properties | — | ✓ |
| Project link(s) | — (cross-org not allowed) | optional |

---

## How to trigger it

Ask to create a repository. You don't have to say "repository" explicitly:

> "Create a new open-source repo under AbsaOSS called telemetry-exporter."
> "Spin up a repo for internal use called event-gate."
> "Set up a new codebase under absa-group."

It does **not** activate for modifying an existing repo (adding a single label, creating branches, PRs,
issues, or workflow files, or cloning).

---

## Notes

- Requires an authenticated GitHub CLI (`gh auth status`) as a member of the target org with permission
  to create repositories. The orgs enforce SAML SSO — if a call is rejected mid-run, the skill keeps your
  answers and tells you how to authorize and resume.
- If a step fails, the skill reports it and prints the commands to finish the steps manually.

---

## Installation

See [Getting Started](./getting-started.md) for the full install guide.
