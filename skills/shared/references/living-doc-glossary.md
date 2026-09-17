<!-- synced from AbsaOSS/living-doc@c22a95d4d7515e8db0ce5c08ab979d3313c7c218 — run scripts/sync-living-doc-glossary.sh c22a95d4d7515e8db0ce5c08ab979d3313c7c218 to refresh -->

# Living Doc Glossary

Core entity contracts: IDs, status vocabulary, relationships, and AC format. Every `living-doc-*` repo and `agentic-toolkit`'s `living-doc-bdd-copilot` agent operate on this canonical entity model.

For the file-header schemas that carry these entities (feature file headers, PageObject headers, Project Profile, seed.yaml, manifest.json), see [Living Doc Header Types](https://github.com/AbsaOSS/living-doc/blob/c22a95d4d7515e8db0ce5c08ab979d3313c7c218/docs/guides/living-doc-header-types.md).

> **Source of truth.** This page is the canonical definition of the entity model. `agentic-toolkit`'s `skills/shared/references/living-doc-glossary.md` is synced from it.

> **Worked examples & sync obligation.** A minimal, copyable example of each entity lives in
> [`docs/examples/`](https://github.com/AbsaOSS/living-doc/blob/c22a95d4d7515e8db0ce5c08ab979d3313c7c218/docs/examples/README.md). When a field or rule on this page changes, the matching
> example changes in the same PR.

---

## Contents

- [Core entities](#core-entities)
  - [User Story (US)](#user-story-us)
  - [Feature](#feature)
  - [Functionality (FUNC)](#functionality-func)
  - [Acceptance Criterion (AC)](#acceptance-criterion-ac)
  - [ID uniqueness](#id-uniqueness)
- [Relationship diagram](#relationship-diagram)
- [What each `living-doc-bdd-copilot` skill creates or consumes](#what-each-living-doc-bdd-copilot-skill-creates-or-consumes)

---

## Core entities

> **Tracker state is never entity status.** A GitHub issue being open or closed, or an Azure DevOps
> work item's `System.State`, says where the *work item* stands in a tracker. The entity status below
> is authored in the documentation itself and is the only status a living-doc document renders. A
> collector records the tracker value as provenance (`source_ref.tracker_state`) and never derives an
> entity status from it.

> **Where status and deprecation metadata are authored.** `## Status`, `## Deprecated At`,
> `## Deprecation Reason` and `## Superseded By` as headings in an issue body; `# status:`,
> `# deprecated_at:`, `# deprecation_reason:` and `# superseded_by:` as keys in a feature-file
> header. Of these only the status is required, and only on a User Story and a Functionality — a
> Feature has no authored status at all. See the
> [GitHub issue-body layout](https://github.com/AbsaOSS/living-doc/blob/c22a95d4d7515e8db0ce5c08ab979d3313c7c218/docs/examples/README.md#github-issue-body-layout-canonical) and
> [Living Doc Header Types](https://github.com/AbsaOSS/living-doc/blob/c22a95d4d7515e8db0ce5c08ab979d3313c7c218/docs/guides/living-doc-header-types.md).

### User Story (US)

A business-level requirement expressed from the perspective of a named actor.

```
As a <actor>,
I can <capability>,
so that <business outcome>.
```

- ID format: `US-<nnn>` (e.g. `US-001`)
- Name: short imperative title (e.g. "Customer Login")
- Owns: end-to-end **Acceptance Criteria (AC)**
- Links to: one or more **Features** (system surfaces the User Story touches)
- Status: **authored**, and required — `planned | in_review | active | deprecated` (lowercase with
  underscores per the Project Profile `ac_states`). Written as `## Status` in the issue body and
  `# status:` in the feature-file header.
- Deprecation metadata (optional; authored when `status: deprecated`):
  - `deprecated_at` — date the entity was deprecated
  - `deprecation_reason` — why it was deprecated
  - `superseded_by` — ID of the replacement entity

> Feature file template: see [Living Doc Header Types — User Story in a Gherkin Feature File](https://github.com/AbsaOSS/living-doc/blob/c22a95d4d7515e8db0ce5c08ab979d3313c7c218/docs/guides/living-doc-header-types.md#1-user-story-in-a-gherkin-feature-file).

### Feature

A named system surface — the structural layer between User Stories and atomic behaviors.

- ID format: `FEAT-<nnn>` (e.g. `FEAT-001`)
- Name: noun phrase identifying the surface (e.g. "Login Page")
- Surface types:

| Type | Description | Test abstraction |
|---|---|---|
| `UI` | A web page, modal, or named screen | **PageObject** design pattern — class encapsulating selectors and user interactions for one screen. Selector preference: `getByTestId()` (resolves to the Project Profile `test_id_attribute`, default `data-cy`) > `aria-label`/role > CSS class. |
| `API` | A request/response or event-driven service contract: a REST/GraphQL endpoint (or endpoint group), or a message-broker topic (e.g. Kafka) documented via an AsyncAPI (or equivalent) specification. A backend service or event producer/consumer is documented as an API Feature representing its public contract. | **Annotated endpoint method or annotated event handler** — for request/response, the endpoint method with its API documentation header (OpenAPI annotation, JSDoc, etc.); for event-driven, the producer/consumer handler with its AsyncAPI (or equivalent schema-registry) annotation. Either serves as the living contract anchor. |

- Owns: one or more **Functionalities**
- Links to: one or more **User Stories**
- `owners`: team or person responsible for this Feature
- Status: **derived from its Functionalities — never authored.** A Feature is the structural node
  that names a visible surface; the behaviour that can be planned, reviewed, shipped or retired lives
  in its Functionalities and their ACs. A hand-written Feature status can therefore only restate them
  or contradict them, so there is no place to write one: a Feature issue body carries no `## Status`
  heading, and a PageObject header carries no `status:` field. The pipeline computes the state and
  marks it `derived`.
- Deprecation metadata (optional; authored when the surface is retired — the *state* still follows
  the Functionalities):
  - `deprecated_at` — date the entity was deprecated
  - `deprecation_reason` — why it was deprecated
  - `superseded_by` — ID of the replacement entity
- Ownership change metadata (set when `owners` changes):
  - `owner_changed_at` — date of ownership transfer
  - `owner_change_reason` — reason for the transfer

> PageObject file header schemas (full header, cross-reference, operational notes, common mistakes): see [Living Doc Header Types — Feature in a PageObject File](https://github.com/AbsaOSS/living-doc/blob/c22a95d4d7515e8db0ce5c08ab979d3313c7c218/docs/guides/living-doc-header-types.md#2-feature-in-a-pageobject-file).

### Functionality (FUNC)

An atomic, fast-testable behavior — a single verb phrase describing one responsibility.

- ID format: `FUNC-<nnn>` (e.g. `FUNC-001`)
- Name: `<parent Feature name> - <behavior phrase>` (e.g. "Login Page - Validate Password Strength")
- Belongs to: one parent **Feature**
- Owns: **Functionality-level Acceptance Criteria** (atomic input to output statements)
- Test anchor: a **Functionality feature file** under `features/liv_doc_func/` — one file per
  Functionality, containing all AC-linked system-test scenarios once implemented.
  File name pattern: `func-<nnn>-<feature-name-kebab>-<behavior-kebab>.feature`
  e.g. `func-001-authentication-screen-credential-based-login.feature`
- Status: **authored**, and required — `planned | in_review | active | deprecated` (lowercase with
  underscores per the Project Profile `ac_states`). Written as `## Status` in the issue body and
  `# status:` in the feature-file header.
- Deprecation metadata (optional; authored when `status: deprecated`):
  - `deprecated_at` — date the entity was deprecated
  - `deprecation_reason` — why it was deprecated
  - `superseded_by` — ID of the replacement entity

Functionalities differ from User Story ACs: they are atomic and fast-testable, not end-to-end.
A single User Story may trigger multiple Functionalities.

#### User Story vs Functionality — decision boundary

| Dimension | User Story | Functionality |
|---|---|---|
| Perspective | End user observing a business outcome | Developer / component behavior |
| Scope | Full E2E flow across one or more surfaces | Single function, method, or UI behavior |
| AC example | "Order is confirmed and confirmation email is sent" | "Returns discounted total when a valid membership tier is applied" |
| Test type | E2E / integration scenario | Unit or fast system test |
| Trigger question | *"Would a product owner write this as a business requirement?"* → **User Story** | *"Would a developer write this as a function contract?"* → **Functionality** |

**When in doubt:** if the behavior is observable only by looking at the code or component output (not by a user clicking through the UI), it is a Functionality. If it describes what a user can do or see across one or more screens, it is a User Story.

If an AC belongs to the wrong entity type, redirect:
- AC too atomic / technical inside a US → move to a **Functionality**
- AC describes a full user journey inside a FUNC → move to a **User Story**

> Feature file template and `func_type` values: see [Living Doc Header Types — Functionality in a Gherkin Feature File](https://github.com/AbsaOSS/living-doc/blob/c22a95d4d7515e8db0ce5c08ab979d3313c7c218/docs/guides/living-doc-header-types.md#3-functionality-in-a-gherkin-feature-file).

### Acceptance Criterion (AC)

A binary pass/fail statement that defines a verifiable condition.

Each AC is:
- **Atomic** — one input condition, one observable outcome
- **Binary** — clear pass/fail; no "usually" or "typically"
- **Single placeholder** — at most ONE `{placeholder}` per AC statement. If two aspects vary independently, write a separate AC for each.

**AC identifier and state format** (in file header and entity files):

```
AC:<parent-id>-<nn> (v<version> - <state>)
   - <atomic description, with at most one {placeholder} for a variable value>
   - <Placeholder>: value1, value2, ...
   - Rationale: <business context, policy reference, or design decision>  ← optional
```

**States** — exactly four, lowercase with underscores (the Project Profile `ac_states`):

| State | Meaning |
|---|---|
| `planned` | Agreed, not built yet |
| `in_review` | Built on a branch, not yet accepted into `master` |
| `active` | Accepted, part of the shipped solution |
| `deprecated` | Shipped behaviour on its way out; carries a removal note |

**Version rule** — a version is required in every state except `planned`:

| Form | Meaning |
|---|---|
| `AC:<id> (v<x.y.z> - active)` | shipped in `v<x.y.z>` (same shape for `in_review`) |
| `AC:<id> (v<x.y.z> - planned)` | planned for the target version `v<x.y.z>` |
| `AC:<id> (planned)` | **backlog**: agreed, no target version yet |
| `AC:<id> (v<x.y.z> - deprecated - removal planned v<x.y.z>)` | deprecated; the removal note is required on a `deprecated` AC and valid on no other state |

An AC deferred out of the current scope keeps its `planned` state and gains no extra fields: drop the
target version so it reads `AC:<id> (planned)`, and record why in the AC's `Rationale` bullet.

> **Canonical form and normalisation.** The canon uses `-` (hyphen-minus) in every structural
> position — AC headers, AC bullets, entity names and the `# AC:` comment separator. Dash, letter-case
> and short-version variants an authoring tool may emit (`–` / `—` for `-`, `In Review` for
> `in_review`, `v1.1` for `v1.1.0`) are rewritten to the canonical form when a collector reads the
> input; they are never canon themselves. Every generated document shows the canonical form above.

**Scenario traceability:** living-doc scenarios (US and Functionality feature files) carry two
complementary annotations — a human-readable `# AC:` comment and a machine-readable `@AC:` tag:

```gherkin
# AC:US-1-01 (v1.0.0 - active) - customer places an order with a saved payment method
@AC:US-1-01
Scenario: Customer successfully places an order
  ...
```

When a scenario covers only **one aspect** of a multi-aspect AC, encode the aspect directly in
the `@AC:` tag using the `/param:value` param syntax, and mirror it in the comment:

```gherkin
# AC:US-1-01 (v1.0.0 - active) - displays {required field} on login screen | aspect: username input
@AC:US-1-01/aspect:username-input
Scenario: Login form shows the username input field
  ...
```

Multiple ACs — one comment + tag pair per AC:

```gherkin
# AC:US-1-01 (v1.0.0 - active) - invalid credentials show an error message
# AC:US-1-02 (v1.0.0 - active) - account lockout after 3 failed attempts
@AC:US-1-01
@AC:US-1-02
@Regression
Scenario: User is locked out after repeated failed logins
  ...
```

**Tag format:** `@AC:<id>[/param:value...]`

| Param | Purpose | Example |
|---|---|---|
| `/aspect:<kebab-value>` | Names the specific aspect of the AC this scenario covers | `@AC:US-1-01/aspect:username-input` |

Additional `/param:value` segments can be appended as needed — the format is open for extension.

- The `# AC:` comment is human-readable context: the canonical AC header, then ` - ` and the
  description, plus an optional `| aspect: <value>` suffix. The separator is a hyphen-minus, never an
  en or em dash.
- The `@AC:` Cucumber tag is machine-readable: drives script scanning, coverage reports, and sync checks.
- US scenarios: `@AC:US-<n>-<nn>` (e.g. `@AC:US-1-01`)
- Functionality scenarios: `@AC:FUNC-<nnn>-<nn>` (e.g. `@AC:FUNC-001-01`)
- Both annotations are required for living-doc feature files (`feature_dirs.user_story` and `feature_dirs.functionality`, defaults `features/liv_doc_us/` and `features/liv_doc_func/`).
- Feature files outside the living-doc directories (smoke tests, regression suites, exploratory probes,
  tutorial walkthroughs) do not require `@AC:` tags.
- **Tutorial walkthroughs** are long-run, feature-based walkthroughs kept for tutorial capture, not living
  documentation. They live in one or more folders *parallel* to the living-doc directories (named
  `tutorials/` or `tutorial_<group>/`), carry a `@tutorial` scenario flag, and are out of scope for every
  collector mode — no collector mines them (a post-v1 roadmap item).

**User Story AC examples** (in the `# Acceptance Criteria:` file header block):

```
AC:US-001-01 (v1.0.0 - active)
   - The login screen displays {required field}.
   - Required field: username input, password input, login button
   - Rationale: Accessibility standard — all interactive controls must be visible on load.

AC:US-001-02 (v1.1.0 - active)
   - An inline field validation message is shown when invalid credentials are submitted.

AC:US-001-03 (v2.1.0 - deprecated - removal planned v3.0.0)
   - A "Remember me" checkbox retains the session across browser restarts.
   - Rationale: Deprecated due to security policy change in v2.0 — persistent sessions no longer permitted.
```

**Functionality AC examples** (in the `# Acceptance Criteria:` file header block):

```
AC:FUNC-001-01 (v1.0.0 - active)
   - Returns valid=true when the password satisfies all complexity rules.

AC:FUNC-001-02 (v1.0.0 - active)
   - Raises {error code} when the credential check fails.
   - Error code: INVALID_PASSWORD, USER_NOT_FOUND, ACCOUNT_LOCKED
   - Rationale: Distinct error codes per failure reason, required by the global auth error contract.

AC:FUNC-001-03 (v1.0.0 - active)
   - Rejects passwords shorter than 8 characters.

AC:FUNC-001-04 (planned)
   - Rejects a password found in the breached-password list.
   - Rationale: Backlog — no target version; the breach-feed contract is not agreed yet.
```

### ID uniqueness

**One project, one pipeline, one documentation source.** A living-doc pipeline documents exactly one
project, and it mines the entities of that project from exactly one documentation source — one
collector mode over one configured set of repositories, or one Azure DevOps project. The test catalog
may come from elsewhere; the technical project may not.

Within that source, entity IDs (`US-`, `FEAT-`, `FUNC-`) and AC IDs are unique. **The same ID
appearing twice is always an input error**, reported as `DUPLICATE_ENTITY_ID` (or `DUPLICATE_AC_ID`)
listing every occurrence. There is no precedence rule and never will be: the pipeline does not pick a
winner, because either choice silently produces a document that is wrong.

Why: a coverage matrix joins the technical project to the test catalog on these IDs. That join is
only meaningful if an ID denotes the same entity everywhere it appears. Colliding IDs cannot be
reconciled after mining — the merge either collides records or silently mismatches a scenario to the
wrong AC, producing a coverage matrix that is wrong in a way no downstream tool can detect.

**Across projects**, identity is the pair `(project_id, entity_id)`. Two projects may each own a
`US-001`; they are different entities because `project_id` differs, and nothing joins them. Do not
prefix or namespace IDs per source to dodge a collision — a collision inside one project means that
project has two entities claiming one ID, and that is the thing to fix.

This mirrors the *coverage-matrix* prerequisites in [Living Doc Document Types](https://github.com/AbsaOSS/living-doc/blob/c22a95d4d7515e8db0ce5c08ab979d3313c7c218/docs/guides/living-doc-document-types.md#coverage-matrix)
and the `Data Flows & Schemas` spec §8 ("Multiple sources and multiple generators"). The toolkit
[`coverage_matrix` service README](https://github.com/AbsaOSS/living-doc-toolkit/blob/master/packages/services/coverage_matrix/README.md)
describes the false-gap failure mode when the two sides of the join do not describe the same system.

---

> `seed.yaml` and `manifest.json` schemas: see [Living Doc Header Types — manifest.json (Exploration Manifest)](https://github.com/AbsaOSS/living-doc/blob/c22a95d4d7515e8db0ce5c08ab979d3313c7c218/docs/guides/living-doc-header-types.md#manifestjson-exploration-manifest).

---

## Relationship diagram

```
User Story (US)
  └── links to: Feature (FEAT)
                    └── owns: Functionality (FUNC)
                                    └── owns: Functionality ACs
                                    └── maps to: Functionality feature file (system test)
                                    |              <feature_dirs.functionality>/func-<nnn>-<kebab>.feature
                                    |              @FUNC_ID tag + @AC:FUNC-nnn-nn tagged scenarios
                                    |              └── implemented by: Step Definitions
                                    └── can map to: unit/integration tests
  └── owns: User Story ACs (in # Acceptance Criteria: header block)
                  └── linked via: @AC:US-n-nn tags on Scenarios
                  └── can map to: E2E BDD Scenarios (<feature_dirs.user_story>/*.feature)
                                       @US_ID tag + @AC:US-n-nn tagged scenarios
                                       └── implemented by: Step Definitions
                                                               └── delegates to: PageObjects
                  └── can map to: API coverage / contract tests
```

---

## What each `living-doc-bdd-copilot` skill creates or consumes

| Skill | Creates | Reads |
|---|---|---|
| `living-doc-create-user-story` | User Story entity | Feature entities |
| `living-doc-create-feature` | Feature entity | User Story entities |
| `living-doc-create-functionality` | Functionality entity + Functionality feature file stub | Feature entity |
| `living-doc-pageobject-scan` | PageObject files + Functionality feature file stubs + fixture entries in `seed.yaml` | App URL or test suite; `seed.yaml form_fixtures` |
| `living-doc-scenario-creator` | E2E BDD scenario files (US) + Functionality feature files (FUNC) | US / FUNC entities, PageObjects |
| `living-doc-gap-finder` | Gap report | All of the above |
