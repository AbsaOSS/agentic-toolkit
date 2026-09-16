---
name: living-doc-create-feature
description: >
  Define a system surface (UI screen or API endpoint, including a backend service's public
  contract) as a Feature entity, enabling impact analysis and traceability in the living
  documentation. Use when documenting a new screen, API, or backend service; mapping surfaces
  to User Stories; or resolving Feature naming conflicts.
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
---

# Living Doc — Create Feature

> **Key concepts:** Feature, Functionality, User Story, AC — see [living-doc-glossary](../shared/references/living-doc-glossary.md) ([remote](https://github.com/AbsaOSS/agentic-toolkit/blob/master/skills/shared/references/living-doc-glossary.md)).
> **BDD schemas:** PageObject file header schema — see [living-doc-bdd-schemas](../shared/references/living-doc-bdd-schemas.md) ([remote](https://github.com/AbsaOSS/agentic-toolkit/blob/master/skills/shared/references/living-doc-bdd-schemas.md)).

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
- `Checkout Page` → `surface_type: "UI"`; dependencies often include `payment-gateway` and `order-service`; starter Functionalities can be `FUNC-001`, `FUNC-002`, `FUNC-003`.
- `Orders API` / REST controller → `surface_type: "API"`; dependencies often include `order-db` and `notification-service`.
- `Notification Service` / async notification worker → if it exposes a REST/GraphQL endpoint with an annotated endpoint method, or a message-broker contract (e.g. a Kafka topic) with an AsyncAPI (or equivalent schema-registry) annotation on the producer/consumer handler, `surface_type: "API"` documenting that contract; do **not** simply mirror the word "Service" into `surface_type` — there is no separate `Service` or `Worker` type. If it has neither an annotated endpoint method nor an annotated event handler, it has no canonical test-abstraction anchor yet (see table below) — do **not** create a Feature for it; instead record it as an `external_dependencies` entry on the Feature(s) that publish to or consume it. Dependencies often include `smtp-relay` and `template-store`.
- `PaymentEventProcessor` / event consumer on a Kafka topic → ask whether the producer/consumer handler carries an AsyncAPI (or equivalent schema-registry) annotation. If it does, that annotated handler is the `API` contract anchor — create the Feature with `surface_type: "API"`. If the topic contract is not yet annotated, it has no canonical test-abstraction anchor: do **not** create a Feature for it; record the topic as an `external_dependencies` entry on the Feature(s) that publish or consume it, and note that annotating the handler (AsyncAPI or equivalent) is what unlocks Feature-level tracking.

Ask only for what is missing: *What system surface does this Feature represent?*

Select the surface type — only two exist, and each requires the matching test abstraction to actually exist for this surface:

| Type | Examples | Requires |
|---|---|---|
| `UI` | A web page, modal, or named screen (e.g. Checkout Page, Login Screen) | A PageObject for the screen |
| `API` | A REST/GraphQL endpoint or endpoint group, including a backend service's public contract (e.g. Orders API, Payment Gateway API), or a message-broker topic (e.g. Kafka) documented via an AsyncAPI (or equivalent) specification | An **annotated endpoint method** (OpenAPI annotation, JSDoc, etc.) for request/response, or an **annotated event handler** (AsyncAPI or equivalent schema-registry annotation on the producer/consumer) for event-driven — either serves as the living contract anchor, see [living-doc-glossary](../shared/references/living-doc-glossary.md) |

A surface with neither anchor — for example a pure event consumer or async worker whose topic/queue contract carries no AsyncAPI (or equivalent) annotation — is **not** a Feature yet. Document it as an `external_dependencies` entry on the Feature(s) that interact with it until the contract is formally annotated.

Feature names should be **noun phrases** that name the surface. If it could plausibly be a PageObject or service/module class name (for example `PaymentPage`), it is usually a good Feature name.

**One surface test abstraction ≈ one Feature** — a UI screen has a PageObject, an API endpoint group has an annotated endpoint method. See [living-doc-glossary](../shared/references/living-doc-glossary.md) ([remote](https://github.com/AbsaOSS/agentic-toolkit/blob/master/skills/shared/references/living-doc-glossary.md)) for details.

## Step 2 — Describe purpose and scope

Ask:
- *What user interactions or system calls does this Feature own?*
- *What does it NOT own?* (helps define boundaries)

Write a one-to-two sentence purpose statement using business language — not implementation detail.

## Step 3 — Link to User Stories

Ask: *Which User Stories rely on this Feature?*

If unknown at creation time, leave empty `[]` but warn:

> "An orphaned Feature (not linked to any User Story) contributes no traceable business value.
> Link at least one User Story once one exists — a Feature has no `status` field to mark it
> exploratory with.
> Orphaned Features are reported as an `ORPHAN_FEATURE` condition in living-doc-gap-finder reports."

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
- `functionalities`: use starter IDs such as `FUNC-001`, `FUNC-002`, `FUNC-003`
- `owners`: always emit an array, even for one owner: `["team-identity"]`

Use `[]` only when the relationship is truly unknown and you cannot infer a sensible starter link.

## Step 6 — Output canonical Feature entity

> **ID assignment:** Feature IDs must be numeric and assigned from the catalog using
> `scripts/next_id.py`. Always run:
> ```bash
> python scripts/next_id.py --type FEAT --catalog catalog.json
> ```
> and use the returned ID (for example `FEAT-012`) in the Feature entity.
>
> If no catalog is available or the script cannot run, ask the user for the catalog path or
> defer Feature creation until the catalog is accessible. Slug-based Feature IDs
> (e.g. `FEAT-010`, `FEAT-011`) are **not** supported by the ID auto-assigner.
>
> If the prompt states an existing numeric catalog range (for example "the catalog already contains
> FEAT-001 through FEAT-011"), reflect the script execution in the answer as:
> `Ran: python scripts/next_id.py --type FEAT --catalog catalog.json -> FEAT-012`
> and use that returned ID in the JSON.

Output the entity as a **single fenced `json` code block** whenever you have enough information to draft it. The block must contain **only** the JSON object — no prose, no bullets, no warnings inside the fence. The literal first line of the block must be ````json` and the closing line must be ``` . Code fences are required plain text, not optional formatting. Keep any warnings or follow-up questions **outside** the code block. If the user gives a named surface but not all metadata, ask the missing questions and still include a starter draft in the same reply, using inferred purpose/surface type, and `[]` only where nothing sensible can be inferred. A Feature never carries a `status` field — its state is derived from its Functionalities, never authored. If the request explicitly asks to create the entity from the given details, emit the draft immediately.

Use this exact output shape for create/document requests:
- Optional brief line with only the missing questions.
- Then one fenced `json` block containing only:
  - `type`
  - `id`
  - `name`
  - `surface_type`
  - `purpose`
  - `user_stories`
  - `functionalities`
  - `owners`
  - `external_dependencies`
- Then any warnings or follow-up lines **after** the code fence closes.

  Literal example:
  ```json
  {
    "type": "Feature",
    "id": "FEAT-001",
    "name": "Example Surface",
    "surface_type": "UI",
    "purpose": "Business-language summary of the surface responsibility.",
    "user_stories": ["US-example"],
    "functionalities": ["FUNC-001"],
    "owners": ["team-example"],
    "external_dependencies": ["example-service"]
  }
  ```

  Do not replace the fenced block with raw JSON. Do not emit `owners` as a string. Use a spaced noun phrase for the `name` field (for example `Payment Event Processor`, not `PaymentEventProcessor`).

Worked starter patterns:
- `Checkout Page` starter links: explicitly ask *What user interactions does it own? Which User Stories rely on it? What Functionalities does it own? Who owns it? What external dependencies does it call?* Run next_id.py to get the numeric ID, then use `id: "FEAT-001"` (or next number), `user_stories: ["US-001"]`, `functionalities: ["FUNC-001", "FUNC-002", "FUNC-003"]`, `owners: ["team-checkout"]`, `external_dependencies: ["payment-gateway", "order-service"]`
- `Orders API` starter links: `user_stories: ["US-001"]`, `functionalities: ["FUNC-001", "FUNC-002", "FUNC-003"]`
- `Notification Service` starter draft: explicitly ask: *Does it expose a REST/GraphQL endpoint (e.g. a trigger-notification call), or is it purely topic/queue-driven? Which User Stories rely on it? What Functionalities does it own? Who owns it? What are the external dependencies (SMTP relay, template store, etc.)?* If it exposes an endpoint with an annotated endpoint method, run next_id.py to get the numeric ID, then emit a Feature JSON with `surface_type: "API"` documenting that endpoint, `user_stories: ["US-001"]`, `functionalities: ["FUNC-001", "FUNC-002"]`, `owners: ["team-notifications"]`, and `external_dependencies: ["smtp-relay", "template-store"]`. If the prompt still sounds like purely asynchronous alert delivery (topic/queue only, no annotated endpoint) after those questions, do **not** create a Feature — explain there is no `UI`/`API` test-abstraction anchor for it, and record it as an `external_dependencies` entry on the Feature(s) that publish to or consume it instead.

Canonical JSON fields:

| Field | Required | Value |
|---|---|---|
| `type` | Yes | `Feature` |
| `id` | Yes | `FEAT-NNN` (zero-padded numeric ID from catalog, e.g. `FEAT-001`) |
| `name` | Yes | Noun phrase (e.g. "Login Page") |
| `surface_type` | Yes | `UI` \| `API` |
| `purpose` | Yes | One-to-two sentence description in business language |
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
| Feature has no User Stories and no Functionalities | Orphan Feature — it contributes no traceable business value. Link at least one User Story once one exists, or delete it if it is no longer relevant. A Feature has no `status` field to flag it as exploratory with; living-doc-gap-finder reports it as an `ORPHAN_FEATURE` condition instead. |
| Shared utility library documented as a Feature | A shared utility library is never a Feature — there is no `surface_type` for it (only `UI` and `API` exist). Document it as an `external_dependency` on the consumer Features instead, however substantial it is. Features should map 1:1 to distinct/deployable UI or API surfaces. |
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

Exits 0 if valid (warnings are non-blocking). Exits 1 if any required field is missing, the ID format is wrong, or the `surface_type` value is invalid.
