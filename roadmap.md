# Implementation Roadmap — Agentic Engineering Toolkit

> **Authored from:** `plugin-spec.md` (last reviewed 2026-05-21).
> The spec file has been removed from the repo; this document is the canonical delivery reference.
> **Last updated:** 2026-05-22

---

## Progress overview

| Step | Cluster | Agent(s) | Skills | Done | Remaining |
|---|---|---|---|---|---|
| 1 | Living Doc + BDD | `@living-doc-copilot` ✅ `@living-doc-bdd-copilot` ✅ | 11 / 11 ✅ | 13 files | 0 |
| 1b | Tutorial | `@living-doc-bdd-tutorial-copilot` ❌ | 0 / 1 | — | 2 files |
| 2 | SDET | `@sdet-copilot` ❌ | 0 / 7 | — | 8 files |
| 3 | Code Quality | `@quality-gate-copilot` ❌ | 0 / 7 | — | 8 files |
| 4 | Test Specialist | `@test-specialist-copilot` ❌ | 0 / 6 | — | 7 files |
| 4b | Test Quality | `@test-quality-copilot` ❌ | 0 / 4 | — | 5 files |
| 5 | Standalone | — | 0 / 3 | — | 3 files |
| **Total** | | **7 agents** | **40 skills** | **13** | **33** |

> **Constraint:** never merge a cluster without both the skill files AND the agent definition in the same PR.

---

## File layout

```
skills/
└── {skill-name}/
    ├── SKILL.md            ← required
    ├── scripts/            ← optional: executable logic
    ├── references/         ← optional: overflow docs (when body approaches 500 lines)
    ├── assets/             ← optional: templates, example files
    └── evals/              ← optional: trigger + assertion test prompts

.github/
└── agents/
    └── {agent-name}.agent.md
```

Skill source to migrate from: `/Users/ab024ll/.copilot/skills/{skill-name}/SKILL.md`  
Agent files: authored from scratch using the spec definitions below.

### Agent file format

```yaml
---
description: >
  <Purpose + explicit trigger phrases — sole activation signal, ≤ 1024 chars>
tools:
  - read_file
  - replace_string_in_file
  - create_file
  - grep_search
  - file_search
  - semantic_search
  # + run_in_terminal for agents with execute capability
  # + mcp_microsoft_pla_browser_* for @living-doc-bdd-copilot only
---

<System prompt: purpose, scope, Does NOT list with redirects, skills table with paths, handoff>
```

### Validation checklist (every skill before merge)

- [ ] Folder name matches `name` frontmatter exactly — lowercase kebab-case, ≤ 64 chars
- [ ] `description` ≤ 1024 chars; covers *what* and *when*; includes trigger keywords
- [ ] Body < 500 lines; use `references/` with a pointer in body if needed
- [ ] No hardcoded secrets, credentials, or absolute machine-local paths
- [ ] Scripts in `scripts/` are referenced from `SKILL.md` with usage instructions

---

## Step 1 — Living Doc + BDD Cluster

### Completed ✅

| File | Status |
|---|---|
| `.github/agents/living-doc-copilot.agent.md` | ✅ |
| `.github/agents/living-doc-bdd-copilot.agent.md` | ✅ |
| `skills/living-doc-create-feature/SKILL.md` | ✅ |
| `skills/living-doc-create-functionality/SKILL.md` | ✅ |
| `skills/living-doc-create-user-story/SKILL.md` | ✅ |
| `skills/living-doc-gap-finder/SKILL.md` | ✅ |
| `skills/living-doc-impact-analysis/SKILL.md` | ✅ |
| `skills/living-doc-update/SKILL.md` | ✅ |
| `skills/living-doc-pageobject-scan/SKILL.md` | ✅ |
| `skills/living-doc-scenario-creator/SKILL.md` | ✅ |
| `skills/gherkin-scenario/SKILL.md` | ✅ |
| `skills/gherkin-step/SKILL.md` | ✅ |
| `skills/gherkin-living-doc-sync/SKILL.md` | ✅ |

### Agent outline: `@living-doc-bdd-copilot`

**Frontmatter:**

```yaml
---
description: >
  Bridge living documentation to executable tests. Explore web apps via MCP Playwright,
  generate and maintain PageObjects, Gherkin scenarios, and step definitions.
  Handles Phase 0+1 (Business Seed + exploration), Phase 3 (scenario generation),
  Phase 6 maintenance (RE-SCAN, HEALING, REMOVE).
  Triggers: "scan webapp", "generate pageobjects", "heal pageobjects", "generate scenarios",
  "sync gherkin", "playwright crawl", "explore the app", "bdd copilot", "BDD pipeline".
tools:
  - read_file
  - replace_string_in_file
  - create_file
  - grep_search
  - file_search
  - semantic_search
  - run_in_terminal
  - mcp_microsoft_pla_browser_navigate
  - mcp_microsoft_pla_browser_snapshot
  - mcp_microsoft_pla_browser_click
  - mcp_microsoft_pla_browser_fill_form
  - mcp_microsoft_pla_browser_take_screenshot
  - mcp_microsoft_pla_browser_type
  - mcp_microsoft_pla_browser_wait_for
---
```

**Required body sections:**

1. **Phase 0 — Business Seed assembly**
   - Sources A–E with behaviour per source
   - Credential rule: `env:VAR_NAME` in `seed.yaml` always, never literal values
   - Output artifact: `.copilot/bdd/seed.yaml`

2. **Phase 1 — Iterative exploration**
   - Load `seed.yaml` + `manifest.json` (if present from prior run); absent manifest = first iteration
   - Crawl loop until coverage plateau (no new surfaces in last iteration)
   - Report unreachable areas → enrich seed → loop
   - Output artifact: `.copilot/bdd/manifest.json` (Feature name, URL, component IDs, PageObject path)

3. **Source E — Guided traversal protocol**
   - Pause at unknown decision points, take screenshot, ask user
   - Immediately append to `guided_steps:` in `seed.yaml`: `url`, `action`, `field`, `value` (`env:VAR` if sensitive), `note`
   - CAPTCHA rule: pause, wait for human to solve in browser, continue; still record the step

4. **Phase 3 — Scenario generation**: gap detection vs existing scenarios; generate via `living-doc-scenario-creator`; write step definitions; extend PageObjects

5. **Phase 6 — Maintenance**: RE-SCAN (new feature/refactor), HEALING (test failures/selector drift), REMOVE (deprecated feature) — triggers and behaviour per mode

6. **Scope** (10 bullets from spec):
   - Load Business Seed + Exploration Manifest before crawling
   - Crawl web app via MCP Playwright using manifest-guided navigation
   - Fill forms and traverse wizards using business-supplied test values
   - Identify Features from discovered UI surfaces
   - Detect scenario gaps (existing scenarios vs US ACs)
   - Generate Gherkin scenarios from User Story ACs
   - Write and extend step definitions
   - Heal PageObjects after UI changes (MCP Playwright drift detection)
   - Challenge US/AC validity when app behaviour has changed
   - Sync Gherkin feature files with living doc

7. **Does NOT**: create living doc entities (→ `@living-doc-copilot`); write unit/integration tests (→ `@sdet-copilot`); run quality gates (→ `@quality-gate-copilot`)

8. **Shared skill note**: `living-doc-gap-finder` is used bottom-up here (scenario coverage for known ACs) vs top-down in `@living-doc-copilot` (missing documentation)

9. **Skills** (6): `living-doc-pageobject-scan`, `living-doc-scenario-creator`, `living-doc-gap-finder`, `gherkin-scenario`, `gherkin-step`, `gherkin-living-doc-sync` — each with path `skills/{name}/SKILL.md`

10. **Handoff out** (two paths):
    - Feature list → `@living-doc-copilot` to document
    - After Phase 3: *"Feature files and steps generated. Call @sdet-copilot for unit tests."*

---

### Issue 1.A — Complete remaining Step 1 skills

**Title:** `[Step 1] Migrate remaining living-doc BDD + gherkin skills`

**Body:**

```
## Summary

Six skills remain from the Living Doc + BDD cluster. Must ship in the same PR as Issue 1.B
(spec rule: never transfer skills without the agent definition).

## Files to create

| Destination | Source |
|---|---|
| `skills/living-doc-pageobject-scan/SKILL.md` | `.copilot/skills/living-doc-pageobject-scan/SKILL.md` |
| `skills/living-doc-scenario-creator/SKILL.md` | `.copilot/skills/living-doc-scenario-creator/SKILL.md` |
| `skills/gherkin-scenario/SKILL.md` | `.copilot/skills/gherkin-scenario/SKILL.md` |
| `skills/gherkin-step/SKILL.md` | `.copilot/skills/gherkin-step/SKILL.md` |
| `skills/gherkin-living-doc-sync/SKILL.md` | `.copilot/skills/gherkin-living-doc-sync/SKILL.md` |

## Acceptance criteria

- [ ] All 6 folder names match their `name` frontmatter fields exactly
- [ ] All `description` fields ≤ 1024 chars and include trigger keywords
- [ ] `living-doc-gap-finder` description (already migrated) notes dual shared-skill usage
       — verify it covers both top-down (@living-doc-copilot) and bottom-up (@living-doc-bdd-copilot)
- [ ] `gherkin-scenario` description notes optional @sdet-copilot usage at unit level
- [ ] All bodies < 500 lines (use `references/` with pointer if needed)
- [ ] No hardcoded credentials or absolute local paths
- [ ] Closed in same PR as Issue 1.B

## Reference

Spec → Agent Catalog → @living-doc-bdd-copilot skills table
```

---

### Issue 1.B — Create @living-doc-bdd-copilot agent

**Title:** `[Step 1] Create @living-doc-bdd-copilot agent definition`

**Body:**

```
## Summary

Author `.github/agents/living-doc-bdd-copilot.agent.md` — automation-layer agent for web app
exploration (Phases 0+1), BDD scenario generation (Phase 3), and maintenance (Phase 6).

## File to create

`.github/agents/living-doc-bdd-copilot.agent.md`

## Required frontmatter

See roadmap.md → Step 1 → Agent outline: @living-doc-bdd-copilot for full frontmatter block.
Key requirement: all mcp_microsoft_pla_browser_* tools must be listed.

## Required body sections

1. Phase 0 — Business Seed assembly (Sources A–E; credential safety; seed.yaml output)
2. Phase 1 — Iterative exploration (load seed + manifest; plateau detection; manifest.json output)
3. Partial state — seed.yaml present but manifest.json absent = treat as first Phase 1 run
4. Source E — Guided traversal (pause/screenshot/ask/execute/write guided_steps; CAPTCHA rule)
5. Phase 3 — Scenario generation with gap detection
6. Phase 6 — Maintenance (RE-SCAN / HEALING / REMOVE)
7. Scope — 10 bullets
8. Does NOT — with redirect targets
9. Shared skill note for living-doc-gap-finder
10. Skills table — 7 entries with paths
11. Handoff out — two paths; prompts verbatim from spec

## Acceptance criteria

- [ ] All MCP Playwright tools listed in frontmatter
- [ ] Sources A–E documented with exact behaviour per source
- [ ] Credential safety rule present (env:VAR_NAME, never literal)
- [ ] Partial state handling documented
- [ ] Guided traversal protocol includes CAPTCHA pause-and-wait
- [ ] Phase 6 all three maintenance modes documented
- [ ] All 7 skills referenced as `skills/{name}/SKILL.md`
- [ ] Handoff prompt exact: "Feature files and steps generated. Call @sdet-copilot for unit tests."
- [ ] Closed in same PR as Issue 1.A
```

---

### Planned agent: `@living-doc-bdd-tutorial-copilot`

The tutorial generation capability (previously `living-doc-tutorial-creator` skill) will ship as
a dedicated agent rather than as part of `@living-doc-bdd-copilot`. It will own the full
tutorial authoring pipeline: transform executed BDD scenarios into annotated tutorial documents,
SSML narration scripts, and onboarding walkthroughs.

| Attribute | Value |
|---|---|
| Agent file | `.github/agents/living-doc-bdd-tutorial-copilot.agent.md` |
| Skill | `skills/living-doc-tutorial-creator/SKILL.md` — migrate from `.copilot/skills/` |
| Inbound trigger | Executed `.feature` files + optional screenshots |
| Output | Annotated tutorial `.md`, SSML narration script |
| Step | Separate step (not yet scheduled) |

---

## Step 2 — SDET Cluster

### Files to create

| File | Type |
|---|---|
| `skills/tdd-workflow/SKILL.md` | Skill — migrate from `.copilot/skills/` |
| `skills/test-unit-write/SKILL.md` | Skill — migrate |
| `skills/test-unit-review/SKILL.md` | Skill — migrate |
| `skills/test-unit-standards/SKILL.md` | Skill — migrate |
| `skills/test-case-design/SKILL.md` | Skill — migrate |
| `skills/test-data-management/SKILL.md` | Skill — migrate |
| `skills/test-mocking-patterns/SKILL.md` | Skill — migrate |
| `.github/agents/sdet-copilot.agent.md` | Agent — author from spec |

### Agent outline: `@sdet-copilot`

**Frontmatter:**

```yaml
---
description: >
  Daily developer test-engineering companion. Use for: TDD red-green-refactor, writing
  unit and integration tests, reviewing existing test files, designing test case tables,
  managing test data and fixtures, choosing test doubles. Phase 4 of the engineering
  pipeline. Triggers: "write tests", "TDD", "review my tests", "test doubles",
  "test data", "red-green-refactor", "sdet copilot", "write unit tests",
  "add tests for", "design test cases", "add coverage for".
tools:
  - read_file
  - replace_string_in_file
  - create_file
  - grep_search
  - file_search
  - semantic_search
---
```

**Required body sections:**

1. **Technology-neutral escalation constraint** (4-step): express guidance language-agnostic first; if language-specific tooling required ask *"What is your target technology / language?"*; recommend escalating to `@quality-gate-copilot` with the matching language skill (`qa-python`, `qa-java`, `qa-scala`, `qa-typescript`, `qa-dotnet`); if no match, provide generic guidance and note the gap

2. **Scope** (6 bullets): TDD workflow; write unit and integration test code; review and audit test files; design test case tables; manage test data; choose test doubles

3. **Does NOT**: run CI quality gates (→ `@quality-gate-copilot`); write Gherkin/BDD *as standalone BDD pipeline deliverables* (→ `@living-doc-bdd-copilot`; `gherkin-scenario` available optionally at unit level); handle specialised test types — accessibility, security, E2E, API (→ `@test-specialist-copilot`); improve test quality depth — mutation, property-based, flakiness (→ `@test-quality-copilot`)

4. **Skills** (7): `tdd-workflow`, `test-unit-write`, `test-unit-review`, `test-unit-standards`, `test-case-design`, `test-data-management`, `test-mocking-patterns`; note `gherkin-scenario` as optional 8th when team uses BDD at unit level

5. **Handoff out**: *"Tests written. Run @quality-gate-copilot to enforce the gate."*

---

### Issue 2.1 — SDET cluster (skills + agent)

**Title:** `[Step 2] SDET cluster — migrate 7 skills and create @sdet-copilot agent`

**Body:**

```
## Summary

Migrate 7 SDET skills and author the @sdet-copilot agent definition as a single PR.

## Files to create

skills/tdd-workflow/SKILL.md, skills/test-unit-write/SKILL.md,
skills/test-unit-review/SKILL.md, skills/test-unit-standards/SKILL.md,
skills/test-case-design/SKILL.md, skills/test-data-management/SKILL.md,
skills/test-mocking-patterns/SKILL.md, .github/agents/sdet-copilot.agent.md

## Acceptance criteria — skills

- [ ] `tdd-workflow` body references SPEC.md-first pattern in the red-green-refactor cycle
- [ ] `test-unit-standards`, `test-unit-write`, and `test-unit-review` cross-reference each other
       correctly (rule set vs procedural write vs procedural review distinction)
- [ ] All bodies < 500 lines; all descriptions ≤ 1024 chars
- [ ] All folder names match `name` frontmatter exactly

## Acceptance criteria — agent

- [ ] Escalation path says "recommend @quality-gate-copilot", not "load qa-* skill internally"
- [ ] Gherkin Does NOT entry is qualified: "standalone BDD pipeline deliverable";
       optional unit-level exception noted
- [ ] All 7 skills referenced by path `skills/{name}/SKILL.md`
- [ ] Handoff prompt exact: "Tests written. Run @quality-gate-copilot to enforce the gate."

## Reference

Spec → Agent Catalog → @sdet-copilot
```

---

## Step 3 — Code Quality Cluster

### Files to create

| File | Type |
|---|---|
| `skills/qa-python/SKILL.md` | Skill — migrate from `.copilot/skills/` |
| `skills/qa-java/SKILL.md` | Skill — migrate |
| `skills/qa-scala/SKILL.md` | Skill — migrate |
| `skills/qa-typescript/SKILL.md` | Skill — migrate |
| `skills/qa-dotnet/SKILL.md` | Skill — migrate |
| `skills/qa-terraform/SKILL.md` | Skill — migrate |
| `skills/test-coverage-gate/SKILL.md` | Skill — migrate |
| `.github/agents/quality-gate-copilot.agent.md` | Agent — author from spec |

### Agent outline: `@quality-gate-copilot`

**Frontmatter:**

```yaml
---
description: >
  Enforce code quality standards — diagnose and fix CI quality gate failures across all
  languages and stacks. Use for: linting, formatting, static analysis violations, coverage
  thresholds, Javadoc, type annotations, and logging standards. Phase 5 of the pipeline.
  Triggers: "quality gate", "CI failing", "coverage below", "lint error", "scalafmt",
  "pylint", "quality gate copilot", "fix linting", "coverage threshold", "SpotBugs",
  "ESLint violation", "dotnet format", "tflint failure".
tools:
  - read_file
  - grep_search
  - file_search
  - semantic_search
  - run_in_terminal
---
```

**Required body sections:**

1. **Scope** (5 bullets): run/fix linting and formatting; fix static analysis violations; configure and enforce coverage thresholds; diagnose CI gate failures per language; apply logging/Javadoc/type annotation standards

2. **Language routing table** — maps language/stack to skill and path:

   | Language | Skill | Path |
   |---|---|---|
   | Python | `qa-python` | `skills/qa-python/SKILL.md` |
   | Java | `qa-java` | `skills/qa-java/SKILL.md` |
   | Scala | `qa-scala` | `skills/qa-scala/SKILL.md` |
   | TypeScript / JS | `qa-typescript` | `skills/qa-typescript/SKILL.md` |
   | C# / .NET | `qa-dotnet` | `skills/qa-dotnet/SKILL.md` |
   | HCL / Terraform | `qa-terraform` | `skills/qa-terraform/SKILL.md` |
   | All (coverage) | `test-coverage-gate` | `skills/test-coverage-gate/SKILL.md` |

3. **Does NOT**: write test code (→ `@sdet-copilot`); handle mutation testing strategy (→ `@test-quality-copilot`); author IaC modules (→ `cps-iac` in `cps-agentic-skills`, not this repo)

4. **Skills** (7): language column + intent label + path

---

### Issue 3.1 — Code Quality cluster (skills + agent)

**Title:** `[Step 3] Code Quality cluster — migrate 7 skills and create @quality-gate-copilot agent`

**Body:**

```
## Summary

Migrate 7 code quality skills and author the @quality-gate-copilot agent as a single PR.

## Files to create

skills/qa-python/SKILL.md, skills/qa-java/SKILL.md, skills/qa-scala/SKILL.md,
skills/qa-typescript/SKILL.md, skills/qa-dotnet/SKILL.md, skills/qa-terraform/SKILL.md,
skills/test-coverage-gate/SKILL.md, .github/agents/quality-gate-copilot.agent.md

## Acceptance criteria — skills

- [ ] `qa-scala` body covers JMF filter requirement for JaCoCo
- [ ] `test-coverage-gate` distinguishes baseline measurement (no CI block) from
       new-code gate (hard fail)
- [ ] Each `qa-*` description includes language-specific trigger keywords
- [ ] All folder names match `name` frontmatter exactly; all descriptions ≤ 1024 chars

## Acceptance criteria — agent

- [ ] Language routing table covers all 5 languages + HCL + cross-language coverage
- [ ] `run_in_terminal` present in tools (this agent executes commands)
- [ ] IaC redirect points to `cps-iac` in `cps-agentic-skills`, not this plugin
- [ ] All 7 skills referenced by path

## Reference

Spec → Agent Catalog → @quality-gate-copilot
```

---

## Step 4 — Test Specialist Cluster

### Files to create

| File | Type |
|---|---|
| `skills/test-accessibility/SKILL.md` | Skill — migrate from `.copilot/skills/` |
| `skills/test-api-standards/SKILL.md` | Skill — migrate |
| `skills/test-e2e-standards/SKILL.md` | Skill — migrate |
| `skills/test-integration-standards/SKILL.md` | Skill — migrate |
| `skills/test-ui-standards/SKILL.md` | Skill — migrate |
| `skills/test-security/SKILL.md` | Skill — migrate |
| `.github/agents/test-specialist-copilot.agent.md` | Agent — author from spec |

### Agent outline: `@test-specialist-copilot`

**Frontmatter:**

```yaml
---
description: >
  Apply specialised testing for specific test types beyond standard unit tests.
  Use for: accessibility (axe-core, WCAG 2.1 AA), API and Pact contract tests,
  cross-service E2E, Testcontainers integration isolation, Angular/React/Cypress UI
  tests, and SAST/DAST security scanning. Triggers: "a11y test", "Pact",
  "E2E standards", "security scan", "Cypress", "Testcontainers", "accessibility",
  "contract test", "test specialist copilot", "UI tests", "integration isolation".
tools:
  - read_file
  - replace_string_in_file
  - create_file
  - grep_search
  - file_search
  - semantic_search
  - run_in_terminal
---
```

**Required body sections:**

1. **Specialisation routing table**:

   | Concern | Skill | Path |
   |---|---|---|
   | Accessibility / WCAG | `test-accessibility` | `skills/test-accessibility/SKILL.md` |
   | REST + contract (Pact) | `test-api-standards` | `skills/test-api-standards/SKILL.md` |
   | Cross-service E2E | `test-e2e-standards` | `skills/test-e2e-standards/SKILL.md` |
   | Testcontainers / DB isolation | `test-integration-standards` | `skills/test-integration-standards/SKILL.md` |
   | Angular / React / Cypress | `test-ui-standards` | `skills/test-ui-standards/SKILL.md` |
   | SAST / DAST / dep scanning | `test-security` | `skills/test-security/SKILL.md` |

2. **Scope** (6 bullets from spec)

3. **Does NOT**: write standard unit tests (→ `@sdet-copilot`); run language-specific quality gates (→ `@quality-gate-copilot`); write BDD scenarios (→ `@living-doc-bdd-copilot`); improve test quality depth (→ `@test-quality-copilot`)

4. **Skills** (6): Specialisation column + path

---

### Issue 4.1 — Test Specialist cluster (skills + agent)

**Title:** `[Step 4] Test Specialist cluster — migrate 6 skills and create @test-specialist-copilot agent`

**Body:**

```
## Summary

Migrate 6 Test Specialist skills and author the @test-specialist-copilot agent as a single PR.

## Files to create

skills/test-accessibility/SKILL.md, skills/test-api-standards/SKILL.md,
skills/test-e2e-standards/SKILL.md, skills/test-integration-standards/SKILL.md,
skills/test-ui-standards/SKILL.md, skills/test-security/SKILL.md,
.github/agents/test-specialist-copilot.agent.md

## Acceptance criteria — skills

- [ ] `test-accessibility` covers axe-core, jest-axe, cypress-axe, WCAG 2.1 AA
- [ ] `test-api-standards` covers Pact consumer-driven contracts
- [ ] `test-e2e-standards` is clearly distinguished from `test-ui-standards`
       (cross-service boundary vs UI-only)
- [ ] `test-integration-standards` covers Testcontainers and isolation/cleanup rules
- [ ] `test-security` covers SAST (Bandit/Semgrep), DAST (ZAP), dep scanning (Snyk/pip-audit)
- [ ] All folder names match `name` frontmatter; all descriptions ≤ 1024 chars

## Acceptance criteria — agent

- [ ] Specialisation routing table covers all 6 concerns
- [ ] Does NOT list distinguishes from all four other test agents
- [ ] All 6 skills referenced by path

## Reference

Spec → Agent Catalog → @test-specialist-copilot
```

---

## Step 4b — Test Quality Cluster

### Files to create

| File | Type |
|---|---|
| `skills/test-mutation/SKILL.md` | Skill — migrate from `.copilot/skills/` |
| `skills/test-property-based/SKILL.md` | Skill — migrate |
| `skills/test-flakiness-diagnosis/SKILL.md` | Skill — migrate |
| `skills/test-observability/SKILL.md` | Skill — migrate |
| `.github/agents/test-quality-copilot.agent.md` | Agent — author from spec |

### Agent outline: `@test-quality-copilot`

**Frontmatter:**

```yaml
---
description: >
  Improve depth and reliability of existing tests — the quality improvement layer applied
  after baseline tests are in place. Use for: mutation score improvement (mutmut, PIT,
  Stryker), property-based testing (Hypothesis, ScalaCheck, fast-check), flaky test
  diagnosis and repair, and observability test assertions (logs, metrics, OTel traces).
  Triggers: "mutation", "Hypothesis", "flaky test", "test logs", "test metrics",
  "surviving mutants", "property-based", "test quality copilot", "improve test quality".
tools:
  - read_file
  - replace_string_in_file
  - create_file
  - grep_search
  - file_search
  - semantic_search
  - run_in_terminal
---
```

**Required body sections:**

1. **Prerequisite note**: called after `@sdet-copilot` has baseline coverage; this is a depth-improvement layer, not a test-writing starter

2. **Scope** (4 bullets): mutation testing; property-based testing; flaky test diagnosis and repair; observability assertions

3. **Does NOT**: write new test suites from scratch (→ `@sdet-copilot`); enforce CI quality gates (→ `@quality-gate-copilot`); handle specialised test types (→ `@test-specialist-copilot`)

4. **Skills** (4): `test-mutation`, `test-property-based`, `test-flakiness-diagnosis`, `test-observability` — Specialisation column + path each

5. **Handoff out**: None — this agent is terminal. Quality improvements are applied in place; no downstream phase requires a handoff.

---

### Issue 4b.1 — Test Quality cluster (skills + agent)

**Title:** `[Step 4b] Test Quality cluster — migrate 4 skills and create @test-quality-copilot agent`

**Body:**

```
## Summary

Migrate 4 Test Quality skills and author the @test-quality-copilot agent as a single PR.
This is a depth-improvement layer; call after @sdet-copilot has established baseline coverage.

## Files to create

skills/test-mutation/SKILL.md, skills/test-property-based/SKILL.md,
skills/test-flakiness-diagnosis/SKILL.md, skills/test-observability/SKILL.md,
.github/agents/test-quality-copilot.agent.md

## Acceptance criteria — skills

- [ ] `test-mutation` covers mutmut (Python), PIT (Java/Scala), Stryker (JS/TS)
- [ ] `test-property-based` covers Hypothesis, ScalaCheck, fast-check
- [ ] `test-flakiness-diagnosis` covers async timing, shared state, CI environment differences
- [ ] `test-observability` covers structured log assertions, prometheus_client fake registry,
       InMemorySpanExporter for OTel spans
- [ ] All folder names match `name` frontmatter; all descriptions ≤ 1024 chars

## Acceptance criteria — agent

- [ ] Prerequisite note present: depth-improvement layer, not starter
- [ ] Handoff out section present and states this agent is terminal (no downstream phase)
- [ ] All 4 skills referenced by path

## Reference

Spec → Agent Catalog → @test-quality-copilot
```

---

## Step 5 — Standalone Skills

No agent file — these 3 skills are below the 3-skill minimum for a dedicated agent per governance rules.

### Files to create

| File | Type |
|---|---|
| `skills/pr-review/SKILL.md` | Skill — migrate from `.copilot/skills/` |
| `skills/contract-openapi/SKILL.md` | Skill — migrate |
| `skills/contract-schema-registry/SKILL.md` | Skill — migrate |

> **Future note:** `contract-openapi` + `contract-schema-registry` are candidates for a
> `@devops-copilot` agent when IaC skills are consolidated here. Until then, standalone.

---

### Issue 5.1 — Standalone skills

**Title:** `[Step 5] Migrate standalone skills: pr-review, contract-openapi, contract-schema-registry`

**Body:**

```
## Summary

Migrate 3 standalone skills — final migration step. No agent file required.

## Files to create

| Destination | Source |
|---|---|
| `skills/pr-review/SKILL.md` | `.copilot/skills/pr-review/SKILL.md` |
| `skills/contract-openapi/SKILL.md` | `.copilot/skills/contract-openapi/SKILL.md` |
| `skills/contract-schema-registry/SKILL.md` | `.copilot/skills/contract-schema-registry/SKILL.md` |

## Acceptance criteria

- [ ] `pr-review` description states it is language-agnostic
- [ ] `contract-openapi` description explicitly distinguishes from `contract-schema-registry`
       (REST/OpenAPI vs event schema registry)
- [ ] `contract-schema-registry` description explicitly distinguishes from `test-api-standards`
       (schema registry vs Pact consumer-driven contracts)
- [ ] All folder names match `name` frontmatter; all descriptions ≤ 1024 chars
- [ ] No hardcoded internal paths or credentials

## Reference

Spec → Standalone Skills section; Governance Rules → Agent scope (Skills < 3 → standalone)
```

---

## Post-implementation checklist

After all steps are merged:

- [ ] Update `docs/README.md` — add rows to the Skill Guides table for each skill that has a companion guide
- [ ] Update `README.md` — add the full skill catalog and agent roster
- [ ] Verify summary totals: 40 unique skill files, 7 agent files
- [ ] Add evals for at least one skill per cluster under `skills/{name}/evals/` (see `docs/testing/skill-testing.md`)
- [ ] Run trigger accuracy test for shared skills (`living-doc-gap-finder`, `gherkin-scenario`) to verify correct agent activates for each intent
- [ ] Confirm `@living-doc-bdd-copilot` MCP Playwright tools are available in the target deployment environment
- [ ] Cross-check all agent handoff prompts match each other:
  - `@living-doc-bdd-copilot (explore)` → *"Surfaces mapped. Call @living-doc-copilot to document them."*
  - `@living-doc-copilot` → *"US and ACs are ready. Call @living-doc-bdd-copilot to generate scenarios."*
  - `@living-doc-bdd-copilot` → *"Feature files and steps generated. Call @sdet-copilot for unit tests."*
  - `@sdet-copilot` → *"Tests written. Run @quality-gate-copilot to enforce the gate."*
  - `@quality-gate-copilot` → *"Gate green. Pipeline complete."*
  - `@test-quality-copilot` → terminal (no handoff)
