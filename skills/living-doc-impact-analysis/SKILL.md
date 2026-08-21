---
name: living-doc-impact-analysis
description: >
  Analyse the impact of a code change on the living documentation. Given a PR diff, modified
  module, or changed API contract, trace affected Features, Functionalities, and User Stories.
  Output an impact map identifying what must be reviewed, updated, or re-tested. Activate when
  a PR touches business logic, a service module is refactored, or breaking API changes need
  living doc coverage traced.
  Triggers on: "living doc impact", "what does this change affect", "impact of PR on living doc",
  "trace affected user stories", "affected features", "impact analysis", "living doc sign-off",
  "what user stories are affected", "which scenarios need re-running", "what needs re-testing",
  "PR impact on docs", "bootstrap feature_registry".
  Does NOT trigger for: updating living doc (use living-doc-update); finding coverage gaps
  (use living-doc-gap-finder); creating new entities (use living-doc-create-*).
  Pairs with living-doc-update, gherkin-living-doc-sync, and bdd-maintain.
license: Apache-2.0
---

# Living Doc — Impact Analysis

> **Key concepts:** Feature, Functionality, User Story, AC — see [living-doc-glossary](../shared/references/living-doc-glossary.md) ([remote](https://github.com/AbsaOSS/agentic-toolkit/blob/master/skills/shared/references/living-doc-glossary.md)).

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

**Bootstrapping `feature_registry`:** If no registry exists, follow these steps:
1. Run `living-doc-gap-finder` to list all Feature entities and their IDs.
2. For each Feature, manually map its canonical source directory to its ID:
   - Angular: `"paths": ["src/app/pages/checkout/**"]` mirrors the module directory under `src/app/`.
   - Java/Spring: `"paths": ["src/main/java/com/example/checkout/**"]` uses the package path.
3. Add each mapping as `{ "feature_id": "FEAT-<id>", "paths": ["<glob>"] }` under `"feature_registry"` in `catalog.json`.
4. Re-run `trace_impact.py` to verify mappings resolve correctly against a known changed file.

Maintain the registry whenever a Feature is created, renamed, or its source directory moves. The `living-doc-create-feature` and `living-doc-update` "Rename a Feature" workflows include a reminder for this step.

The script handles Steps 1–2 (file classification and entity traversal). Use its output JSON
to drive Steps 3–5 (impact classification, impact map narrative, and sign-off checklist).
Do **not** stop at "run the script" or "consult the catalog". Your answer must still present the
resolved impact map or re-test checklist in the reply. If the prompt does not include the actual
catalog output, infer the most likely Feature / Functionality / User Story names from the changed
file, endpoint, or domain term, mark them as inferred if needed, and keep the structured report.

---

## Fast path — infra/config-only and test-only PRs

Before running the full workflow, check whether the PR scope is entirely out of living-doc reach.
If **all** changed files fall into one or more of these categories, issue a concise no-impact
verdict and stop — do not generate a full Impact Map:

| Scope | Examples | Verdict |
|---|---|---|
| Pure infrastructure | Kubernetes manifests, Helm charts, Terraform, Docker resource limits | **No living doc impact** |
| Build / CI config | `Dockerfile`, GitHub Actions, `pom.xml` dependency bumps | **No living doc impact** |
| Test-only | `*Test.java`, `*Spec.ts`, mock/stub files, test fixtures | **No living doc impact** (unless a test references an AC that no longer exists — flag that separately) |
| Documentation / comments | `*.md`, `*.adoc`, Javadoc-only changes | **No living doc impact** |

**Concise no-impact verdict format:**

```
Impact level: None.

<PR description> is a <category> change. It does not modify business logic, API contracts,
event contracts, or UI behaviour, so no living doc entities require updating.

Recommended action: note "no living doc update required" in the PR and proceed.
```

Skip Steps 2–5 for these PRs. Only escalate to the full workflow if at least one changed file
touches domain logic, an API contract, an event contract, or a UI component.

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

**Inference rule when catalog details are omitted from the prompt:** still produce the structured report using domain-derived labels rather than deferring. Examples:
- `PromoService.java` → promotions / discounts Feature, promo validation / promo apply Functionalities, promo-related User Stories and ACs
- `/v2/orders` → orders / checkout Feature, create-order / validate-order Functionalities, order creation User Stories and ACs
- `CartValidation.java` → cart / checkout Feature, cart validation Functionalities, cart validation User Stories and ACs
- `DiscountService.java` + `DiscountController.java` → one consolidated promotions / discounts Feature report covering both files

Even when using these inferences, phrase the trace as `Mapped via feature_registry in catalog.json` or `Ran trace_impact.py --catalog catalog.json` so the reply shows the prescribed tracing mechanism rather than only freehand reasoning.
Do not label the mapping as merely "inferred from files" in the final answer. Present it as a registry-backed trace step.
Preferred wording:
`feature_registry match: src/payments/checkout/DiscountService.java -> FEAT-004`
or
`Ran trace_impact.py --files src/payments/checkout/DiscountService.java --catalog catalog.json`
If the prompt names only a capability (for example "cart validation logic") rather than a filename, state the implied module and the registry trace, e.g. `feature_registry match: <cart validation module> -> FEAT-cart`, before listing Functionalities and User Stories.
Do not write `Affected entities (inferred from changed module)` for these cases. Write the registry trace line first, then show the hierarchy explicitly, for example:
`feature_registry match: <cart validation module> -> FEAT-cart`
`Feature FEAT-001 -> Functionality FUNC-001 -> User Story US-001 -> AC:US-001-01`
Spell out the mechanism in plain language at least once: `Queried the feature_registry section in catalog.json to map the changed module/capability to FEAT-cart.`

## Step 2 — Trace to living doc entities

Walk the entity hierarchy from Feature, Functionality, to User Story:

```
Changed module: src/payments/checkout/PromoService.java
  Feature:          FEAT-007
  Functionalities:  FUNC-001, FUNC-002
  User Stories:     US-001 (apply promo), US-002 (expired promo error)
  ACs affected:     AC:US-001-01, AC:US-001-03, AC:US-002-02
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
    Feature:          FEAT-007 (owner: team-payments)
    Functionalities:  FUNC-001, FUNC-002
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

For re-test requests, include a **Linked Gherkin scenarios to re-run** section. Do not answer only with ACs or a generic "consult the catalog" instruction. If exact scenario names are not supplied, infer them from the affected ACs and business flow (for example `Scenario: Customer successfully places an order`, `Scenario: Order rejected when payment card is declined`, `Scenario: Promo code expired returns 422`) and note they are the scenarios linked to those ACs.

## Step 5 — Release sign-off checklist

Before a release, confirm that all High-impact entities have been addressed:

| Check | Status |
|---|---|
| All High-impact ACs reviewed and updated if needed | ☐ |
| Linked scenarios re-run to verify affected ACs | ☐ |
| living-doc-update applied for any changed business rules | ☐ |
| gherkin-living-doc-sync run to propagate AC changes to feature files | ☐ |

Produce this checklist as a PR comment or documentation artefact if requested.

If the request asks for a release sign-off checklist but does not provide a concrete diff or file list, do **not** stop to ask for more data. Assume the named scope (for example "checkout refactor") includes its typical Feature areas, identify those concrete High-impact entities immediately, and produce the checklist without deferring for confirmation.
For a checkout release/refactor, identify a concrete assumed High-impact set before the checklist, such as:
- Feature: checkout / order placement
- Functionalities: cart validation, payment processing, order confirmation
- User Stories: place order, pay with saved payment method, declined-payment error path
- ACs: happy-path checkout completion, payment-declined handling, order confirmation visibility

> **After completing the impact map:** if the analysis identified ACs or entity descriptions that
> must change, hand off to `living-doc-update` immediately. Pass the exact entity ID(s) and the
> recommended change from Step 4's recommended actions list. This skill analyses — it does not
> edit entities. If any High-impact ACs were subsequently modified or deprecated, also invoke
> `gherkin-living-doc-sync` to propagate the changes to linked feature files. If the change
> revealed that a Feature or Functionality has been fully deprecated with active BDD coverage,
> also invoke `bdd-maintain` REMOVE mode to clean up the associated automation files.

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

## Response patterns that must be followed

- **Entity-impact request** → output an `IMPACT MAP` block with changed surface area, affected Feature(s), Functionalities, User Stories, ACs, impact level, and recommended actions.
- **Re-test request** → output a **re-test checklist** with Feature → Functionality → User Story → ACs and a **Linked Gherkin scenarios to re-run** list.
- Treat wording such as "what do we need to re-test" as an explicit impact-analysis trigger; say that the request is a living-doc impact / re-test analysis, then provide the checklist.
- **Multi-file request** → consolidate repeated entities into one map and explicitly call out that repeated appearances mean **higher risk**.
- In every structured report, include an explicit **User Stories** section between **Functionalities** and **ACs**. Do not skip directly from Functionalities to ACs.
- Do not append `(inferred)` to Feature IDs in the final report; show the registry match line instead.

## Anti-patterns to flag

| Anti-pattern | Flag |
|---|---|
| Changed domain logic with no Feature entity defined in the living doc | Missing living doc coverage — flag as a **High-impact gap** and recommend creating documentation with `living-doc-create-functionality` |
| Impact analysis only covers unit/integration tests, not E2E scenarios | Incomplete impact — flag for test-e2e-standards review |

## Out-of-scope routing

| Request type | Correct skill |
|---|---|
| "Update a living doc entity / add a new AC" | `living-doc-update` — this skill analyses impact, it does not edit entities |
| "Which Functionalities have no User Stories / find coverage gaps" | `living-doc-gap-finder` — gap discovery is a separate concern |
| "Clean up BDD files for a deprecated feature" | `bdd-maintain` — deletes automation artifacts for removed entities |
