---
name: living-doc-impact-analysis
description: >
  Analyse the impact of a code change on the living documentation. Given a PR diff,
  modified module, or changed API contract, trace which Features, Functionalities, and User Stories
  are affected. Output an impact map that identifies what must be reviewed,
  updated, or re-tested. Activate when a PR touches business logic and you need to know what
  living doc entities are affected, when a service module is refactored, or when breaking API
  changes need living doc coverage traced.
  Triggers on: "living doc impact", "what does this change affect", "impact of PR on living doc",
  "trace affected user stories", "affected features", "impact analysis", "living doc sign-off",
  "what user stories are affected", "PR impact on docs".
  Does NOT trigger for: updating living doc (use living-doc-update), finding coverage gaps
  (use living-doc-gap-finder), creating new entities (use living-doc-create-* skills).

license: Apache-2.0
compatibility: GitHub Copilot
---

# Living Doc — Impact Analysis

> **Key concepts:** Feature, Functionality, User Story, AC — see [living-doc-glossary](../references/living-doc-glossary.md) ([remote](https://github.com/AbsaOSS/agentic-toolkit/blob/master/skills/references/living-doc-glossary.md)).

## Script — `scripts/trace_impact.py`

Run this script to trace changed files to living doc entities before producing the impact map.
The catalog JSON must include a `feature_registry` section mapping path patterns to Feature IDs.

```bash
# Trace from an explicit file list
python scripts/trace_impact.py --files src/payments/PromoService.java --catalog catalog.json --summary

# Trace from a unified git diff
python scripts/trace_impact.py --diff changes.diff --catalog catalog.json --output impact.json
```

Feature registry format (add to your catalog JSON):
```json
{
  "feature_registry": [
    { "feature_id": "FEAT-001", "paths": ["src/auth/**", "src/security/login*"] }
  ]
}
```

The script handles Steps 1–2 (file classification and entity traversal). Use its output JSON
to drive Steps 3–5 (impact classification, impact map narrative, and sign-off checklist).

---

## Step 1 — Identify the changed surface area

Start from the code change (PR diff, renamed module, deleted endpoint):

1. List the changed files and classify each:
   - **Domain logic** (service, repository, domain model)
   - **API contract** (controller, route, OpenAPI spec)
   - **Event contract** (schema, Avro, Protobuf)
   - **UI component** (page, form, component)
   - **Configuration / infrastructure** (no living doc impact unless it changes a business flow)

2. Map changed files to modules/services using the project structure.

3. For each changed module, identify the corresponding Feature by traversing entity relationships:
   - Which Feature owns this module? (check the Feature's `functionalities` links or ask the owning team)
   - Which Functionalities does this module implement?
   - If the module has no matching `feature_registry` entry, treat it as missing living doc coverage for impact-analysis purposes: flag a **High-impact gap**, recommend `living-doc-create-functionality`, and note that the registry mapping must be added.

## Step 2 — Trace to living doc entities

Walk the entity hierarchy from Feature, Functionality, to User Story:

```
Changed module: src/payments/checkout/PromoService.java
  Feature:          FEAT-promotions
  Functionalities:  FUNC-promo-validate, FUNC-promo-apply
  User Stories:     US-042 (apply promo), US-067 (expired promo error)
  ACs affected:     AC:US-042-01, AC:US-042-03, AC:US-067-02
```

Repeat for every changed module. Consolidate entities that appear more than once — they are
higher-risk and need priority review.

**Shared utility classes:** If the changed file is a shared utility used by multiple modules
(e.g. `MoneyUtils`, `DateHelper`), fan out the trace to **every** Feature that imports or
depends on that utility. Classify each as **High impact** — a shared utility change propagates
to all consumers and each consumer's ACs must be reviewed. Produce a consolidated impact map
that covers all affected Feature areas.

## Step 3 — Classify the impact level

| Impact level | Criteria | Action required |
|---|---|---|
| **High** | AC or business rule directly changed or deleted | Must update living doc and re-run linked tests |
| **Medium** | Module changed but business rule unchanged (refactor/rename) | Update living doc if method names referenced; confirm tests still pass |
| **Low** | Config / infra change that alters a business flow | Update living doc if the flow change is documented; note in PR |
| **None** | Pure infrastructure change (resource limits, scaling, deployment config) with no business flow impact; or test files, mocks, build scripts only | No living doc update needed |

## Step 4 — Output the impact map

Emit a structured impact map for the PR or change set:

```
IMPACT MAP — PR #217: "Refactor promo validation to support stacked discounts"
  Surface area: src/payments/checkout/PromoService.java (domain logic — High)
                src/payments/checkout/PromoController.java (API contract — High)

  Affected entities:
    Feature:          FEAT-promotions (owner: team-payments)
    Functionalities:  FUNC-promo-validate, FUNC-promo-apply
    User Stories:     US-042 (high impact), US-067 (high impact), US-089 (medium impact)

  ACs requiring review:
    AC:US-042-01  — Happy path: single promo applied correctly
    AC:US-042-03  — Stacked promos applied in priority order  ← NEW BEHAVIOUR
    AC:US-067-02  — Expired promo returns 422

  Recommended actions:
    1. Update living-doc: add AC for stacked discount priority order (AC:US-042-03 is new)
       Invoke living-doc-update
    2. Re-run E2E journeys: US-042 and US-067 critical path scenarios
       Invoke test-e2e-standards
```

If the request is framed as **"what needs re-testing"**, present Step 4 as a compact **re-test checklist**: group by Feature / Functionality / User Story and list the affected ACs.

## Step 5 — Release sign-off checklist

Before a release, confirm that all High-impact entities have been addressed:

| Check | Status |
|---|---|
| All High-impact ACs reviewed and updated if needed | ☐ |
| living-doc-update applied for any changed business rules | ☐ |

Produce this checklist as a PR comment or documentation artefact if requested.

## Code-level impact report format

When the change is a **method signature change** or **API contract change**, produce a
code-level impact report with four sections:

**Direct callers** — classes or methods that call the changed method directly (markdown list).

**Downstream dependents** — components that use the return value or depend on the changed
contract (markdown list).

**Required changes** — concrete call-site updates needed (markdown list; include the old and
new signatures in fenced code blocks).

**Test coverage required** — tests that must be added or updated to cover the new contract
(markdown list).

Do not include speculative changes beyond the described scope.

## Anti-patterns to flag

| Anti-pattern | Flag |
|---|---|
| Changed domain logic with no Feature entity defined in the living doc | Missing living doc coverage — flag as a **High-impact gap** and recommend creating documentation with `living-doc-create-functionality` |
| Impact analysis only covers unit/integration tests, not E2E scenarios | Incomplete impact — flag for test-e2e-standards review |

## Out-of-scope redirects

| Request type | Correct skill |
|---|---|
| "Update a living doc entity / add a new AC" | `living-doc-update` — this skill analyses impact, it does not edit entities |
| "Which Functionalities have no User Stories / find coverage gaps" | `living-doc-gap-finder` — gap discovery is a separate concern |
