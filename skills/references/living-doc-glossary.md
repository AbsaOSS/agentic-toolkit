# Living Documentation — Shared Glossary

All living-doc-* skills operate on the same canonical entity model.
Use these definitions consistently across all skill invocations.

---

## Core entities

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
- Status: `planned | active | deprecated`
- Deprecation metadata (set when `status: deprecated`):
  - `deprecated_at` — date the entity was deprecated
  - `deprecation_reason` — why it was deprecated
  - `superseded_by` — ID of the replacement entity (optional)

### Feature

A named system surface — the structural layer between User Stories and atomic behaviors.

- ID format: `FEAT-<nnn>` (e.g. `FEAT-001`)
- Name: noun phrase identifying the surface (e.g. "Login Page")
- Surface types:

| Type | Description | Test abstraction |
|---|---|---|
| `UI` | A web page, modal, or named screen | **PageObject** design pattern — class encapsulating selectors and user interactions for one screen. Selector preference: `data-testid` > `aria-label`/role > CSS class. |
| `API` | A REST/GraphQL endpoint or endpoint group. A backend service is documented as an API Feature representing its public contract. | **Annotated endpoint method** — the endpoint method with its API documentation header (OpenAPI annotation, JSDoc, etc.) serves as the living contract anchor. |

- Owns: one or more **Functionalities**
- Links to: one or more **User Stories**
- `owners`: team or person responsible for this Feature
- Status: `planned | active | deprecated`
- Deprecation metadata (set when `status: deprecated`):
  - `deprecated_at` — date the entity was deprecated
  - `deprecation_reason` — why it was deprecated
  - `superseded_by` — ID of the replacement entity (optional)
- Ownership change metadata (set when `owners` changes):
  - `owner_changed_at` — date of ownership transfer
  - `owner_change_reason` — reason for the transfer

### Functionality (FUNC)

An atomic, fast-testable behavior — a single verb phrase describing one responsibility.

- ID format: `FUNC-<nnn>` (e.g. `FUNC-001`)
- Name: `<parent Feature name> – <behavior phrase>` (e.g. "Login Page – Validate Password Strength")
- Belongs to: one parent **Feature**
- Owns: **Functionality-level Acceptance Criteria** (atomic input → output statements)
- Status: `planned | active | deprecated`
- Deprecation metadata (set when `status: deprecated`):
  - `deprecated_at` — date the entity was deprecated
  - `deprecation_reason` — why it was deprecated
  - `superseded_by` — ID of the replacement entity (optional)

Functionalities differ from User Story ACs: they are atomic and fast-testable, not end-to-end.
A single User Story may trigger multiple Functionalities.

### Acceptance Criterion (AC)

A binary pass/fail statement that defines a verifiable condition.

Each AC is:
- **Atomic** — one input condition, one observable outcome
- **Binary** — clear pass/fail; no "usually" or "typically"
- **Single placeholder** — at most ONE `{placeholder}` per AC statement. If two aspects vary independently, write a separate AC for each.

**AC identifier and state format:**

```
AC:<parent-id>-<nn> (v<version> – <State>)
   – <atomic description, with at most one {placeholder} for a variable value>
   – <Placeholder>: value1, value2, ...
   – Rationale: <business context, policy reference, or design decision>  ← optional
```

State values: `Planned | Implemented | Active | Deprecated`

Deprecated ACs include a removal note:

```
AC:<parent-id>-<nn> (v<version> – Deprecated – removal planned v<version>)
```

**Descoped ACs** (deferred mid-sprint — state stays `Planned`):

```
AC:<parent-id>-<nn> (v<version> – Planned)
   – <description>
   – descoped_at: <date>           ← date AC was deferred out of the current sprint
   – descoped_reason: <text>
   – future_release: <sprint/tag>  ← optional; target sprint or release
```

**User Story AC examples — end-to-end, written from the user's perspective:**

```
AC:US-001-01 (v1.0.0 – Active)
   – The login screen displays {required field}.
   – Required field: username input, password input, login button
   – Rationale: Accessibility standard — all interactive controls must be visible on load.

AC:US-001-02 (v1.1.0 – Active)
   – An inline field validation message is shown when invalid credentials are submitted.

AC:US-001-03 (v2.1.0 – Deprecated – removal planned v3.0.0)
   – A "Remember me" checkbox retains the session across browser restarts.
   – Rationale: Deprecated due to security policy change in v2.0 — persistent sessions no longer permitted.
```

**Functionality AC examples — atomic input → output:**

```
AC:FUNC-001-01 (v1.0.0 – Active)
   – Returns valid=true when the password satisfies all complexity rules.

AC:FUNC-001-02 (v1.0.0 – Active)
   – Raises {error code} when the credential check fails.
   – Error code: INVALID_PASSWORD, USER_NOT_FOUND, ACCOUNT_LOCKED
   – Rationale: Distinct error codes per failure reason, required by the global auth error contract.

AC:FUNC-001-03 (v1.0.0 – Active)
   – Rejects passwords shorter than 8 characters.
```

---

## Relationship diagram

```
User Story (US)
  └── links to → Feature (FEAT)
                    └── owns → Functionality (FUNC)
                                    └── owns → Functionality ACs
                                    └── can map to → unit/integration tests
  └── owns → User Story ACs
                  └── can map to → BDD Scenarios (.feature files)
                                       └── implemented by → Step Definitions
                                                               └── delegates to → Feature test abstractions
                  └── can map to → API coverage / contract tests
```

---

## What each skill creates or consumes

| Skill | Creates | Reads |
|---|---|---|
| `living-doc-create-user-story` | User Story entity | Feature entities |
| `living-doc-create-feature` | Feature entity | User Story entities |
| `living-doc-create-functionality` | Functionality entity | Feature entity |
| `living-doc-pageobject-scan` | Surface wrapper classes + Feature stubs | App URL or test suite |
| `living-doc-scenario-creator` | BDD scenario files (.feature) | User Story entities, Feature test abstractions |
| `living-doc-tutorial-creator` | Tutorial documents | BDD scenario files, User Story entities |
| `living-doc-gap-finder` | Gap report | All of the above |
