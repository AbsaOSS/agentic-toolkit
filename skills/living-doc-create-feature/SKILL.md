---
name: living-doc-create-feature
description: >
  Define a system surface (UI screen, API endpoint, service, or module) as a Feature entity,
  enabling impact analysis and traceability in the living documentation. Use when documenting
  a new screen, API, service, or module; mapping surfaces to User Stories; or resolving
  Feature naming conflicts.
  Triggers on: "document a new feature", "create a feature entity", "new screen documentation",
  "document an API endpoint", "feature registry", "what feature owns this", "map user story to
  feature", "system surface documentation", "feature owners", "feature dependencies",
  "duplicate feature name", "resolve feature naming", "rename feature".
  Does NOT trigger for: creating User Stories (use living-doc-create-user-story); defining
  behaviors (use living-doc-create-functionality); scanning PageObjects (use
  living-doc-pageobject-scan); deprecating (use living-doc-update).
  Pairs with living-doc-create-functionality and living-doc-create-user-story.
  After creating, add a feature_registry entry for living-doc-impact-analysis.
license: Apache-2.0
compatibility: GitHub Copilot
---

# Living Doc — Create Feature

> **Key concepts:** Feature, Functionality, User Story, AC — see [living-doc-glossary](../../shared/references/living-doc-glossary.md) ([remote](https://github.com/AbsaOSS/agentic-toolkit/blob/master/skills/shared/references/living-doc-glossary.md)).
> **BDD schemas:** PageObject file header schema — see [living-doc-bdd-schemas](../references/living-doc-bdd-schemas.md) ([remote](https://github.com/AbsaOSS/agentic-toolkit/blob/master/skills/references/living-doc-bdd-schemas.md)).

## Step 1 — Identify the system surface

Before asking, **scan the conversation context** for a surface name, surface type, and owning team already stated by the user. If the prompt already gives enough information to draft the entity, infer the obvious details and propose the Feature directly instead of blocking on follow-up questions. Ask only for what is still missing or ambiguous.

If the user asks to **create/document/add** a named Feature, do **both** in the same reply:
1. Ask only the missing follow-up questions.
2. Still emit a **starter Feature draft immediately** — never stop at questions only.

When information is missing, phrase the discovery as a short numbered checklist that explicitly covers every missing category:
1. purpose/scope (*what does it own / not own?*)
2. User Story links
3. Functionalities
4. owners
5. external dependencies
6. surface type, if still ambiguous

When details are missing but the surface name makes the domain obvious, infer a sensible starter draft instead of blocking. If the prompt does **not** explicitly say the links are unknown, seed provisional `US-...` / `FUNC-...` references instead of leaving both arrays empty. Common examples:
- `Checkout Page` → `surface_type: "UI"`, use the shorter slug `FEAT-checkout`, dependencies often include `payment-gateway` and `order-service`; starter Functionalities can be `FUNC-validate-cart`, `FUNC-apply-promo`, `FUNC-confirm-order`.
- `Orders API` / REST controller → `surface_type: "API"`; dependencies often include `order-db` and `notification-service`.
- `Notification Service` / notification worker → default to `surface_type: "Worker"` (or `API` if it is clearly a synchronous contract surface); do **not** simply mirror the word "Service" into `surface_type`; dependencies often include `smtp-relay` and `template-store`.
- `PaymentEventProcessor` / event consumer → `surface_type: "Worker"`; include the Kafka topic or event stream in `external_dependencies`.

Ask only for what is missing: *What system surface does this Feature represent?*

Select the surface type:

| Type | Examples |
|---|---|
| `UI` | A web page, modal, or named screen (e.g. Checkout Page, Login Screen) |
| `API` | A REST/GraphQL endpoint or endpoint group, including a backend service's public API contract (e.g. Orders API, Payment Gateway API) |
| `Service` | A named backend/service surface with its own contract (e.g. Customer Profile Service) |
| `Worker` | An asynchronous/background processor (e.g. Notification Worker) |
| `Module` | A distinct internal module with a stable contract or bounded responsibility |
| `Library` | A substantial shared internal library that is intentionally tracked as its own surface |

Feature names should be **noun phrases** that name the surface. If it could plausibly be a PageObject or service/module class name (for example `PaymentPage`), it is usually a good Feature name.

**One surface test abstraction ≈ one Feature** — a UI screen has a PageObject, an API endpoint group has an annotated endpoint method. See [living-doc-glossary](../references/living-doc-glossary.md) ([remote](https://github.com/AbsaOSS/agentic-toolkit/blob/master/skills/references/living-doc-glossary.md)) for details.

## Step 2 — Describe purpose and scope

Ask:
- *What user interactions or system calls does this Feature own?*
- *What does it NOT own?* (helps define boundaries)

Write a one-to-two sentence purpose statement using business language — not implementation detail.

## Step 3 — Link to User Stories

Ask: *Which User Stories rely on this Feature?*

If unknown at creation time, leave empty `[]` but warn:

> "An orphaned Feature (not linked to any User Story) contributes no traceable business value.
> Link at least one User Story or mark this as exploratory with status: 'candidate'.
> Orphaned Features are surfaced as gaps in living-doc-gap-finder reports."

## Step 4 — Enumerate Functionalities

Ask: *What atomic behaviors (Functionalities) does this Feature implement?*

Functionalities can be empty at creation time — they are built out as development proceeds.
Add as `"functionalities": ["FUNC-<name>"]` references only when the Functionality has been
formally defined. If they are described as informal notes or candidates (not yet registered as
FUNC entries), leave the array as `[]` and add a warning:
> "Candidate Functionalities must be formally defined using **living-doc-create-functionality**
> before being linked here."

## Step 5 — Identify owners and dependencies

| Field | What to capture |
|---|---|
| `owners` | Team name(s) or individual(s) responsible for this surface |
| `external_dependencies` | Services or systems this Feature calls (e.g. payment-gateway, order-service) |

For starter drafts, prefer **provisional inferred values** over empty strings when the domain is obvious:
- `user_stories`: use starter IDs such as `US-checkout`, `US-order-management`, `US-payment-processing`
- `functionalities`: use starter IDs such as `FUNC-validate-cart`, `FUNC-apply-promo`, `FUNC-confirm-order`
- `owners`: always emit an array, even for one owner: `["team-identity"]`

Use `[]` only when the relationship is truly unknown and you cannot infer a sensible starter link.

## Step 6 — Output canonical Feature entity

> **ID assignment:** If `catalog.json` is available and `scripts/next_id.py` can run, **always**
> run `python scripts/next_id.py --type FEAT --catalog catalog.json` first and use the returned
> numeric ID (for example `FEAT-012`). Do **not** invent a numeric ID or prefer a slug when the
> catalog-backed script is available.
>
> If no catalog is available (or the script cannot run because the catalog is missing), fall back
> to a readable slug ID derived from the surface name (for example `FEAT-checkout`,
> `FEAT-orders-api`, `FEAT-notifications-centre`) and explicitly warn:
> **"No catalog available — using slug ID FEAT-<kebab-name>. Verify this ID does not conflict with existing entities before saving."**
>
> If the prompt states an existing numeric catalog range (for example "the catalog already contains
> FEAT-001 through FEAT-011"), reflect the script execution in the answer as:
> `Ran: python scripts/next_id.py --type FEAT --catalog catalog.json -> FEAT-012`
> and use that returned ID in the JSON.

Output the entity as a **single fenced `json` code block** whenever you have enough information to draft it. The block must contain **only** the JSON object — no prose, no bullets, no warnings inside the fence. The literal first line of the block must be ````json` and the closing line must be ``` . Code fences are required plain text, not optional formatting. Keep any warnings or follow-up questions **outside** the code block. If the user gives a named surface but not all metadata, ask the missing questions and still include a starter draft in the same reply, using inferred purpose/surface type, `status: "planned"`, and `[]` only where nothing sensible can be inferred. If the request explicitly asks to create the entity from the given details, emit the draft immediately.

Use this exact output shape for create/document requests:
- Optional brief line with only the missing questions.
- Then one fenced `json` block containing only:
  - `type`
  - `id`
  - `name`
  - `surface_type`
  - `purpose`
  - `status`
  - `user_stories`
  - `functionalities`
  - `owners`
  - `external_dependencies`
- Then any warnings or follow-up lines **after** the code fence closes.

  Literal example:
  ```json
  {
    "type": "Feature",
    "id": "FEAT-example-surface",
    "name": "Example Surface",
    "surface_type": "UI",
    "purpose": "Business-language summary of the surface responsibility.",
    "status": "planned",
    "user_stories": ["US-example"],
    "functionalities": ["FUNC-example-behaviour"],
    "owners": ["team-example"],
    "external_dependencies": ["example-service"]
  }
  ```

  Do not replace the fenced block with raw JSON. Do not emit `owners` as a string. Use a spaced noun phrase for the `name` field (for example `Payment Event Processor`, not `PaymentEventProcessor`).

Worked starter patterns:
- `Checkout Page` starter links: explicitly ask *What user interactions does it own? Which User Stories rely on it? What Functionalities does it own? Who owns it? What external dependencies does it call?* and use `id: "FEAT-checkout"`, `user_stories: ["US-checkout"]`, `functionalities: ["FUNC-validate-cart", "FUNC-apply-promo", "FUNC-confirm-order"]`, `owners: ["team-checkout"]`, `external_dependencies: ["payment-gateway", "order-service"]`
- `Orders API` starter links: `user_stories: ["US-order-management"]`, `functionalities: ["FUNC-create-order", "FUNC-get-order", "FUNC-list-orders"]`
- `Notification Service` starter draft: emit a Feature JSON even when the user asks "where do I start?", but explicitly ask: *What type of surface is it (API, Worker, or UI)? Which User Stories rely on it? What Functionalities does it own? Who owns it? What are the external dependencies (SMTP relay, template store, etc.)?* If the prompt still sounds like asynchronous alert delivery after those questions, use `id: "FEAT-notification-service"`, default `surface_type: "Worker"`, `user_stories: ["US-notification-delivery"]`, `functionalities: ["FUNC-render-notification", "FUNC-dispatch-notification"]`, `owners: ["team-notifications"]`, and `external_dependencies: ["smtp-relay", "template-store"]`

Canonical JSON fields:

| Field | Required | Value |
|---|---|---|
| `type` | Yes | `Feature` |
| `id` | Yes | `FEAT-<kebab-name>` |
| `name` | Yes | Noun phrase (e.g. "Login Page") |
| `surface_type` | Yes | `UI` \| `API` \| `Service` \| `Worker` \| `Module` \| `Library` |
| `purpose` | Yes | One-to-two sentence description in business language |
| `status` | Yes | `planned` \| `active` \| `candidate` \| `deprecated` |
| `user_stories` | Yes | List of `US-<...>` IDs (use `[]` if unknown) |
| `functionalities` | Yes | List of `FUNC-<...>` IDs (use `[]` if unknown or still only candidates) |
| `owners` | Yes | Team name(s) |
| `external_dependencies` | Yes | Names of services or systems this Feature calls |

If `user_stories` is `[]`, repeat the orphan warning from Step 3 outside the JSON. If `functionalities` is `[]` because they are still just candidate notes, repeat the formal-definition warning from Step 4 outside the JSON.

## Anti-patterns to flag

| Anti-pattern | Warning |
|---|---|
| Feature covers multiple unrelated screens | Split into one Feature per distinct screen |
| Feature name is a verb (e.g. "Process Payment") | Feature names should be nouns — name the surface. Verb phrases describe *what the surface does*, which belongs in a Functionality entity (use **living-doc-create-functionality**). If it could be a PageObject or service/module class name, it is usually a better Feature name. |
| Feature has no User Stories and no Functionalities | Orphan Feature — it contributes no traceable business value. Link at least one User Story, mark it as `candidate` if it is still exploratory, or delete it if it is no longer relevant. Orphan Features will be surfaced as gaps in living-doc-gap-finder reports. |
| Shared utility library documented as a Feature | By default, a shared utility library is not a Feature — document it as an `external_dependency` on the consumer Features. Only create a standalone Feature when the library is substantial enough to be treated as a distinct shared surface; in that case use `surface_type: "Library"` and mark it as a shared internal dependency. Features should map 1:1 to distinct/deployable surfaces. |
| Feature name encodes implementation technology (e.g. "React Login Component", "Spring Payment Controller") | Feature names describe the business surface, not the stack. Use "Login Screen" (UI) or "Payment API" (API) — technology choice is an implementation detail that changes without the surface changing. |
| `surface_type` is `UI` for a backend REST controller or service | A REST endpoint group is an `API` surface. `UI` is reserved for screens a human interacts with directly. Misclassification breaks impact analysis routing between frontend and backend changes. |
| Feature shares a name with an existing Feature | Check for duplicates before creating. Identical names indicate a merge candidate or a scope overlap — clarify the boundary before proceeding. |
| `functionalities` field contains User Story IDs (US-nnn) | `functionalities` takes `FUNC-<nnn>` IDs. User Stories are linked under `user_stories`, not here. |

## Out-of-scope routing

| Request type | Use instead |
|---|---|
| Creating a User Story | **living-doc-create-user-story** |
| Defining an atomic behavior (Functionality) | **living-doc-create-functionality** |

## Next steps after creation

| Action | Skill |
|---|---|
| Define atomic behaviors for this Feature | **living-doc-create-functionality** |
| Link to an existing User Story | **living-doc-update** (add Feature to the User Story's `features` list) |
| Generate BDD PageObjects for a UI Feature | **living-doc-pageobject-scan** |
| Update feature_registry for impact traceability | **living-doc-impact-analysis** (see Feature registry format in that skill) |

> **Renaming a Feature:** Changing a Feature's `id` or `name` requires cascading updates. Load `living-doc-update` and follow the "Rename a Feature" workflow there. The minimum cascade is: (1) update the Feature entity itself, (2) update every linked Functionality `feature_id`, (3) update the `feature_registry` entry, (4) update `manifest.json`, (5) update `seed.yaml`, (6) update PageObject file headers, (7) update Gherkin feature file `# Feature:` headers, then run **living-doc-gap-finder** to confirm no orphan references remain.

## Script — `validate_entity.py`

After outputting the entity, validate it against the canonical schema before saving to the catalog. Do not save the entity if the script exits with code 1.

```bash
# Validate the output (run from the toolkit root)
python skills/living-doc-update/scripts/validate_entity.py entity.json

# With referential integrity checks against the full catalog
python skills/living-doc-update/scripts/validate_entity.py entity.json --catalog catalog.json

# Enforce the project's AC state vocabulary (reads `ac_states` from the Project Profile)
python skills/living-doc-update/scripts/validate_entity.py entity.json --profile .copilot/bdd/.project-profile.yaml
```

Exits 0 if valid (warnings are non-blocking). Exits 1 if any required field is missing, the ID format is wrong, or the status or `surface_type` value is invalid.
