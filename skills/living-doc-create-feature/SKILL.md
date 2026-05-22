---
name: living-doc-create-feature
description: >
  Define a system surface (UI screen or API endpoint group) as a Feature entity, enabling impact
  analysis and change-management traceability in the living documentation. Activate when
  documenting a new screen or API endpoint, mapping system surfaces to User Stories, enumerating
  which Functionalities a surface owns, or bootstrapping the structural layer between User Stories
  and atomic behaviors.
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

Before asking, **scan the conversation context** for a surface name, surface type, and owning team already stated by the user. If all three are present, propose the Feature directly and ask for confirmation rather than re-asking the questions.

Ask only for what is missing: *What system surface does this Feature represent?*

Select the surface type:

| Type | Examples |
|---|---|
| `UI` | A web page, modal, or named screen (e.g. Checkout Page, Login Screen) |
| `API` | A REST/GraphQL endpoint or endpoint group, including a backend service's public API contract (e.g. Orders API, Payment Gateway API) |

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

Output using the project's Storage Profile format. Canonical fields:

| Field | Required | Value |
|---|---|---|
| entity type | Yes | `Feature` |
| `id` | Yes | `FEAT-<nnn>` (e.g. `FEAT-001`) |
| `name` | Yes | Noun phrase (e.g. "Login Page") |
| `surface_type` | Yes | `UI` \| `API` |
| `purpose` | Yes | One-to-two sentence description in business language |
| `status` | Yes | `planned` \| `active` \| `deprecated` |
| `user_stories` | Yes | List of `US-<nnn>` IDs (can be `[]` for new Features) |
| `functionalities` | Yes | List of `FUNC-<nnn>` IDs (can be `[]` initially) |
| `owners` | Yes | Team name(s) |
| `external_dependencies` | No | Names of services or systems this Feature calls |

## Anti-patterns to flag

| Anti-pattern | Warning |
|---|---|
| Feature covers multiple unrelated screens | Split into one Feature per distinct screen |
| Feature name is a verb (e.g. "Process Payment") | Feature names should be nouns — name the surface. Verb phrases describe *what the surface does*, which belongs in a Functionality entity (use **living-doc-create-functionality**) |
| Feature has no User Stories and no Functionalities | Orphan Feature — link or delete |
| Shared utility library documented as a Feature | A third-party dependency is not a system surface — document it as `external_dependency` in the Features that consume it. Internal module-level behaviors belong in Functionality entities under the API Feature that owns the service contract. |
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
