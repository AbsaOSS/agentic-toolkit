---
name: pr-review
description: >
  PR code review with structured domain checklists. ALWAYS invoke for any request to review a
  PR, diff, or code changes — even casual ones like "LGTM?" or "does this look right?". This
  skill provides domain-specific risk checklists that Claude won't apply without it: dependency
  upgrade risks, database migration rollback safety, CI/CD gate bypass detection, API contract
  breaking-change analysis, Terraform/IaC least-privilege review, and elevated-risk auth pattern
  detection. Outputs are severity-tiered (Blocker / Important / Nit) for actionable triage.
  Invoke whenever: PR review, sanity check on a diff, pre-merge approval feedback, "any issues
  with this PR?", or when a user shares a PR link and wants feedback.
  Does NOT invoke for: generating release notes/changelogs from a diff, refactoring tasks,
  writing new code, or debugging errors.
---

# PR Review

Single unified PR review skill. Read the full skill and apply only the sections relevant to what the PR touches.

## Before you start with the review

1. List the files changed in the PR (use `gh pr view --json files` or read the diff).
   Helper: `scripts/fetch_pr.sh <PR_NUMBER>` fetches the diff + file list via `gh`.
   Helper: `scripts/classify_sections.py /tmp/pr_files.txt` prints which sections to apply.
2. Use the file list to determine which conditional sections below apply.
3. Read the PR description and any linked issue for intent — use this to judge whether changes
   are in scope, and to avoid flagging intentional decisions as issues.
4. If the PR description is absent or too vague to understand intent, note it as a Nit.
5. Check PR size upfront. If the diff exceeds ~500 changed lines or ~20 files, state at the
   top of the review that coverage may be partial, and prioritise the highest-risk files.
   Suggest the author split the PR when scope warrants it — large PRs are harder to review
   accurately and context window limits can silently reduce coverage.
6. For changes in a domain you are unfamiliar with, or for any elevated-risk PR, check
   `CODEOWNERS` or use `git blame` on the most-changed files to identify the relevant domain
   expert. Mention their handle in the review summary so the author knows to request their
   review or approval — do not block the review on their availability.

**Conditional sections** — use the file list to determine which apply:

| Section | Apply when PR touches |
|---|---|
| API contracts | endpoints, DTOs, config keys, env vars, exit codes, output strings |
| Dependency bumps | pom.xml, requirements.txt, pyproject.toml, package.json, *.csproj, go.mod, build.sbt |
| CI/CD | .github/workflows/, Jenkinsfile, Justfile, Makefile (pipeline), deployment jobs |
| Infrastructure | *.tf, *.tfvars, CloudFormation, Helm, Dockerfiles, docker-compose.yml, iac/, infra/ |
| DB migrations | alembic/, flyway/, liquibase/, migrations/, *.sql, db/ |
| Skill definitions | skills/*/SKILL.md, any SKILL.md |

> A file may match multiple sections (e.g. a DB migration inside an IaC repo). Apply all matching sections — do not skip a section because another one already fired.

**Elevated risk** is not a conditional section like the ones above — it is a binary overlay.
Determine independently whether this PR qualifies:
- Touches auth config, security controls, or permission logic
- Touches infrastructure, secrets management, or external integrations

Notes on common edge cases that do **not** qualify:
- A pure DTO rename or API field rename — covered by the **API contracts section**.
- A DB migration — covered by the **DB migrations section**, which already handles data loss,
  locking, and rollback risks. Only apply elevated risk on top if the migration *also* touches
  auth tables, security controls, secrets management, or infrastructure/external integrations.
- Bumping a security/auth library (e.g. `python-jose`, `bcrypt`) — changing a version number in
  `requirements.txt` is not "touching auth controls". Elevated risk requires the PR to *modify
  code* that implements auth or security logic. Use the dependency bumps section for CVE/compat
  checks on security libraries.

If yes, apply the **Elevated risk checks** section _on top of_ all other sections that fired.

## Format every comment consistently

Every comment must include:
- **What** — one line
- **Why** — impact or risk
- **How to fix** — minimal actionable suggestion; prefer linking to existing repo patterns

Group all comments under: `Blocker` | `Important` | `Nit`

**Severity definitions:**
- **Blocker** — must be fixed before merge: correctness bug, security vulnerability, broken contract,
  quality gate bypassed, credentials in code, data loss risk
- **Important** — should be fixed soon but not a hard blocker: increases risk, missing test for
  changed logic, non-default that's hard to change later, code that will definitely cause problems
- **Nit** — minor polish: style, naming, optional improvement, non-urgent edge case

Rules:
- Short bullet points; reference file + line range where possible
- Keep comments short and targeted — a long audit report buries the real issues and
  discourages authors from engaging with the feedback.
- Avoid requesting refactors unrelated to the PR — scope creep in reviews erodes trust
  and makes PRs harder to merge without accumulating unrelated tech debt.
- If uncertain, ask a targeted question instead of assuming
- Do not flag style issues handled by a formatter or linter — those will be caught
  automatically and flagging them manually wastes the author's time.
- If a section has no findings, write `_None._` — shows you checked, not skipped.

**Before writing your first comment, read `references/output-template.md`.** It shows exactly how clean, multi-section, and elevated-risk reviews should look. Matching its format prevents the most common output problems (wrong heading style, missing `_None._` markers, verbose findings that bury real issues).
Start each review with a header in the form:
`## Applied sections: Standard · [additional sections separated by ·]`
followed by the files changed. This makes the review scope immediately visible to the author.

**The three severity groupings must always be formatted as bold text on their own line, not as markdown headings:**
```
**Blocker**
**Important**
**Nit**
```
Never use `### Blocker`, `## Important`, or any heading syntax for these groupings. The output-template.md examples show the correct format.

**Do not list "Trade-off analysis" in the Applied sections header.** Trade-off analysis is an internal elevated-risk check, not a named section. The header should only list: `Standard`, `API contracts`, `Dependency bumps`, `CI/CD`, `Infrastructure`, `DB migrations`, and `Elevated risk`.

## Apply standard review (always)

Priority order: correctness → security → tests → maintainability → style

**Correctness**
- Logic bugs, missing edge cases, regressions
- Contract changes: output strings, exit codes, env vars, API paths
- Swallowed exceptions (`except: pass`, empty `catch {}`) hide bugs — at minimum log with context
- Returning `null`/`None` where an exception or empty collection is the right contract pushes error handling onto every caller
- Error messages must include enough context to diagnose: what failed, with what input, and why

**Security**
- Unsafe input handling, secrets/tokens in code or logs
- Auth/authz issues, insecure defaults
- For elevated-risk or security-touching PRs, read `references/security-antipatterns.md` before reviewing — it lists patterns to actively scan for (hardcoded creds, injection, broken auth, weak crypto, PII in logs)

**Tests**
- Changed logic has tests covering success + failure paths
- No real external API/network calls in unit tests
- Tests must assert the specific behaviour changed — a test that passes without meaningful assertions is a false-positive shield
- One concept per test; a test asserting five unrelated things gives no signal about which invariant broke
- Tests must be deterministic: no `sleep()`, no real clock, no dependency on execution order
- Flag missing edge-case coverage for conditions identified in correctness checks above

**Maintainability**
- Unnecessary complexity, duplication, unclear naming
- No unrelated drive-by refactors
- Functions doing more than one thing at mixed abstraction levels — flag when a single function interleaves I/O, business logic, and formatting
- Deeply nested conditionals (>3 levels) — suggest early returns, guard clauses, or an extracted method
- Boolean parameters that silently change behaviour (e.g. `process(data, True, False)`) — suggest named constants, enums, or separate functions
- Magic numbers or strings in business logic — flag when intent is unclear without a named constant

**Performance**
- O(n²) or worse complexity in hot paths; flag when input is unbounded
- N+1 query patterns (individual queries inside a loop instead of a batch/join) — multiplies latency by row count
- New queries on large tables without index support cause full scans — flag when no supporting index or `EXPLAIN` commentary is provided
- Missing pagination on endpoints or functions returning collections
- Unbounded memory allocation (appending to list in a loop without a size cap)

**Style**
- Only flag if readability is reduced or repo conventions are broken

## Apply elevated risk checks (overlay — applies on top of all other sections that fired)

Additional checks on top of standard:
- Confirm prior review comments were addressed
- Re-check: auth, permissions, secrets, persistence, external calls, concurrency
- Hidden side effects: backward compat, rollout path, failure modes, retries/timeouts, idempotency
- Safe defaults: least privilege, secure logging, safe error messages, predictable behaviour on missing inputs
- If leaving a risk as-is: state what the risk is, why acceptable, and the mitigation (tests/monitoring/flag)

## Apply trade-off analysis (elevated-risk PRs only)

Elevated-risk PRs often make architectural decisions that are hard to reverse. Ask:

- **One-way or two-way door?** Schema migrations, public APIs, and durable data formats are one-way doors — they need explicit justification. Internal refactors behind a stable interface or feature-flagged changes are two-way doors and need less scrutiny.
- **Is this the established approach?** Research how the problem is typically solved (industry patterns, well-known libraries). If a simpler or more standard alternative achieves the same outcome, surface it concretely — don't just ask "were alternatives considered?", show one.
- **Does it hold at 10× scale?** Forces thinking about the next order of magnitude — unbounded loops, missing pagination, single-node bottlenecks, fan-out explosions.
- **Can this be deployed independently?** If the change requires coordinated rollout with another service or repo, a deployment plan must be documented in the PR.

## Check API contracts (when PR touches: endpoints, DTOs, config keys, env vars, exit codes, output strings, action inputs/outputs)

**REST & synchronous contracts**
- Renaming or removing an endpoint path breaks all clients immediately — add a deprecation alias first and remove only after confirming no active consumers.
- Adding a required field to a response breaks clients that do not expect it — make new fields optional or version the response schema.
- Must not rename fields or change types without a migration path.
- Renaming config keys or env vars without an alias silently breaks deployments — provide the old name as a backward-compatible alias with a deprecation warning.
- Existing failure exit codes must not change.
- Externally-visible strings must not change silently.
- Flag where a server-side change requires a coordinated client update.
- When standardizing field naming (e.g. migrating to camelCase), check migration is complete across **all** fields — a partially-migrated response is confusing and hard to document. Flag as Important.

**Event & message contracts**
- Schema changes must be backward-compatible (existing consumers can still deserialize new messages) *and* forward-compatible (old producers don't break new consumers) — brokers cannot version-route, so all consumers must handle all in-flight message versions.
- Switching encoding (JSON ↔ Avro ↔ Protobuf) or field encoding (string date → epoch) requires a coordinated producer/consumer rollout — flag as Blocker without a migration plan.
- If using a schema registry, confirm the compatibility mode (BACKWARD, FORWARD, FULL) permits the change.

**Idempotency & delivery guarantees**
- Any write triggered by an event, message, or webhook must be idempotent — messages can be delivered more than once. Flag upserts without a deduplication key or conditional write.
- Processing a message without acknowledgment means a crash before ack causes redelivery and duplicate processing — flag when ack is not deferred until after processing succeeds.

**Cache contracts**
- Cache writes without a corresponding invalidation strategy create stale-data bugs that are hard to reproduce — document or flag the invalidation path.
- New queues or caches without TTL, retention, or archival policy grow indefinitely — flag as Important.

**Query & storage performance**
- `SELECT *` or queries without `LIMIT` on user-facing paths — one large tenant can OOM the service.

Backward-compatibility decision guide:
- Additive (new optional field) → usually safe, document it
- Rename → breaking; add alias + deprecation notice
- Remove → breaking; deprecation cycle first
- Type change → breaking; version the API
- Default value change → assess all consumers
- Exit code change → must not change without a major version bump

## Check dependency bumps (when PR touches: pom.xml, requirements.txt, pyproject.toml, package.json, *.csproj, go.mod, build.sbt, Cargo.toml, Gemfile, composer.json, pubspec.yaml)

- Bump must have a stated reason: CVE / feature need / compatibility fix
- Platform-lock compatibility: Spark/EMR/Glue Hadoop (JVM), `engines` field (Node), target framework (.NET), runtime version (Python)
- Flag transitive upgrades that may silently change behaviour
- Must not introduce test-skipping profiles or flags
- Formatter, linter, and type-checker must still pass after the bump
- Must not add suppression of existing warnings to enable the bump

## Check CI/CD changes (when PR touches: .github/workflows/, Jenkinsfile, Justfile, Makefile used as pipeline entrypoint, deployment job configs)

- Do not skip or comment out quality gates — bypassing checks defeats the purpose of CI
  and can allow broken or insecure code to reach production undetected.
- Secrets must be referenced by secret name only — hardcoding a secret value, even
  temporarily, risks it being captured in logs or git history.
- Branch filters, path filters, and event triggers must be intentional.
- Widening a deploy trigger (e.g. from a specific branch to all pushes) without explicit
  approval gates is a **Blocker** — it can push untested changes to production on every
  commit, including feature branches that have never been reviewed for production readiness.
- Deployment jobs must require explicit approval — an auto-deploy trigger on the wrong
  branch filter can push untested changes to production without human review.
- Existing job/recipe names and behaviours must be preserved

## Check infrastructure as code (when PR touches: *.tf, *.tfvars, terragrunt.hcl, *.yaml, CloudFormation, Helm charts, Dockerfiles, docker-compose.yml, iac/, infra/)

- Flag force-new replacements and deletions — Terraform may silently destroy and recreate
  stateful resources (databases, queues) during a plan; authors must confirm this is intended.
- Do not hardcode regions or account IDs — environment-specific values baked into config
  make cross-environment deployments break silently.
- Wildcard `*` IAM actions or resources violate least-privilege and can be exploited if
  any resource in the scope is compromised — require explicit justification.
- Must not store secrets in plain text; use secret manager references
- Resources must be idempotent; re-applying must produce no unintended changes
- Do not use `latest` image tags in production — the image pulled at deploy time may differ
  from what was tested, introducing untested changes silently.
- Base image changes must not break the expected runtime layout

## Check DB migrations (when PR touches: alembic/, flyway/, liquibase/, migrations/, *.sql, db/)

- Migrations must be irreversible-safe: a failed deploy mid-migration must leave the database
  in a consistent state. Prefer additive changes (add column, add table) over destructive ones.
- Column/table removal should happen in a separate PR after the code no longer references it —
  dropping a column while old code is still running causes immediate errors.
- Adding a replacement column and dropping its source in the same migration without a backfill
  step destroys the existing data permanently — this is a **Blocker**. The safe sequence is:
  (1) add the new column, (2) backfill values from the old column in a separate step,
  (3) drop the original in a later migration once the backfill is confirmed complete.
- Must not lock tables for extended periods on large tables; use online schema change tools
  (pt-online-schema-change, gh-ost, pglogical, `ALGORITHM=INSTANT`) where supported.
- Default values added to existing columns must be valid for all existing rows.
- Migration filenames/versions must be monotonically increasing — gaps or reordering breaks
  migration runners on environments that haven't applied intermediate steps.
- Must include a rollback/down script or document that rollback is not safe and why.

## Check skill definitions (when PR touches: skills/*/SKILL.md, any SKILL.md)

- `name` is kebab-case, matches the directory name, and is ≤ 64 chars
- `description` covers both "what it does" AND "when to trigger" with explicit trigger keywords
- `description` is ≤ 1024 chars and not padded with filler
- SKILL.md body is < 500 lines, or uses progressive disclosure via `references/`
- No hardcoded credentials, secrets, or absolute internal paths in skill body or scripts
- Any bundled script in `scripts/` is referenced from SKILL.md with clear usage guidance
- The new or modified skill's description does not conflict with or shadow existing skills
