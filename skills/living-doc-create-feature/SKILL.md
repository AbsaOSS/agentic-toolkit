---
name: living-doc-create-feature
description: >
  Define a system surface (UI screen, API endpoint, service, or module) as a Feature entity,
  enabling impact analysis and change-management traceability in the living documentation.
  Activate when documenting a new screen, API endpoint, service, or module; maintaining a
  Feature Registry; mapping system surfaces to User Stories; enumerating which Functionalities
  a surface owns; or bootstrapping the structural layer between User Stories and atomic behaviors.
  Triggers on: "document a new feature", "create a feature entity", "new screen documentation",
  "document an API endpoint", "feature registry", "what feature owns this", "map user story to
  feature", "create feature entity", "system surface documentation", "feature owners",
  "feature dependencies".
  Does NOT trigger for: creating User Stories (use living-doc-create-user-story), defining atomic
  behaviors (use living-doc-create-functionality), scanning a webapp for PageObjects
  (use living-doc-pageobject-scan), generating scenarios (use living-doc-scenario-creator).
license: Apache-2.0
compatibility: GitHub Copilot
---

# Living Doc — Create Feature

> **Key concepts:** Feature, Functionality, User Story, AC — see [living-doc-glossary](../references/living-doc-glossary.md) ([remote](https://github.com/AbsaOSS/agentic-toolkit/blob/master/skills/references/living-doc-glossary.md)).

## Step 1 — Identify the system surface

Before asking, **scan the conversation context** for a surface name, surface type, and owning team already stated by the user. If the prompt already gives enough information to draft the entity, infer the obvious details and propose the Feature directly instead of blocking on follow-up questions. Ask only for what is still missing or ambiguous.

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

## Step 6 — Output canonical Feature entity

Use a readable slug ID based on the business surface name: `FEAT-<kebab-name>` (for example `FEAT-checkout`, `FEAT-orders-api`, `FEAT-notifications-centre`). For UI names ending in generic words like `Page`, `Screen`, or `Modal`, you may omit that trailing UI noun in the ID when the shorter slug stays unambiguous.

Output the entity as a **single fenced `json` code block** whenever you have enough information to draft it. Keep any warnings or follow-up questions **outside** the code block. If the user gives a named surface but not all metadata, ask the missing questions and still include a starter draft in the same reply, using inferred purpose/surface type, `status: "planned"`, and `[]` for relationships that are still unknown. If the request explicitly asks to create the entity from the given details, emit the draft immediately.

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
| Scanning a webapp for PageObjects | **living-doc-pageobject-scan** |
