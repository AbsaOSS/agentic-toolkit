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

**US feature file header format** (as used in `features/us/us-<nnn>-<kebab>.feature`):

The header comment block at the top of a US feature file holds all US metadata. This data is
collected during the living documentation output generation process (data mining).

```gherkin
# Source: https://github.com/<org>/<repo>/issues/<n>

# Business Value:
#   - <bullet describing the business outcome>

# Not in scope:                           ← optional
#   - <item excluded from this US>

# Preconditions:                          ← optional
#   - <system state required before test>

# Acceptance Criteria:
#
#   AC:US-<n>-01 (v<version> - <State>)
#     - <description of the AC>
#     - <Aspect>: <value1>, <value2>       ← optional; used for {placeholder} ACs
#
#   AC:US-<n>-02 (v<version> - <State>)
#     - <description of the AC>

@US_ID:US-<n>
Feature: <US Title>
  As a <actor>, I can <capability>, so that <business outcome>.

  Background:                              ← optional
    Given <shared precondition>

  # AC:US-<n>-01 (v<version> - <State>) — <AC description>
  @AC:US-<n>-01
  Scenario: <scenario title>
    ...
```

**Header sections:**
| Section | Required | Purpose |
|---|---|---|
| `# Source:` | Optional | Link to the original issue tracker entry or the pre-BDD living doc location — primarily useful during migration from a legacy format |
| `# Business Value:` | Yes | Why this User Story exists (bullets) |
| `# Not in scope:` | Optional | Explicit exclusions |
| `# Preconditions:` | Optional | System-level state required before test execution |
| `# Acceptance Criteria:` | Yes | Full AC listing with IDs, versions, and states |
| `@US_ID:US-<n>` tag | Yes | Machine-parseable User Story ID (feature-level tag) |

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
- Owns: **Functionality-level Acceptance Criteria** (atomic input to output statements)
- Test anchor: a **Functionality feature file** (`func-<kebab>.feature`) under
  `features/functionalities/<feature-kebab-name>/` — one file per Functionality, containing
  all AC-linked system-test scenarios once implemented.
- Status: `planned | active | deprecated`
- Deprecation metadata (set when `status: deprecated`):
  - `deprecated_at` — date the entity was deprecated
  - `deprecation_reason` — why it was deprecated
  - `superseded_by` — ID of the replacement entity (optional)

Functionalities differ from User Story ACs: they are atomic and fast-testable, not end-to-end.
A single User Story may trigger multiple Functionalities.

**Functionality feature file header format** (draft — exact spec TBD, follows US conventions):

```gherkin
# Source: https://github.com/<org>/<repo>/issues/<n>

# Rationale:                              ← optional (replaces Business Value for atomic behaviors)
#   - <why this behavior exists>

# Not in scope:                           ← optional
#   - <exclusion>

# Acceptance Criteria:
#
#   AC:FUNC-<nnn>-01 (v<version> - <State>)
#     - <description>
#
#   AC:FUNC-<nnn>-02 (v<version> - <State>)
#     - <description>

@FUNC_ID:FUNC-<nnn>
Feature: <Feature Name> — <Functionality Name>
  # No scenarios yet — uncovered ACs flagged by coverage_report.py.
  # When adding scenarios: include both # AC:<id> comment and @AC:<id>[/param:value] tag above each Scenario.
```

**Header sections:**
| Section | Required | Purpose |
|---|---|---|
| `# Source:` | Optional | Link to the original issue tracker entry or the pre-BDD living doc location — primarily useful during migration from a legacy format |
| `# Rationale:` | Optional | Why this atomic behavior exists |
| `# Not in scope:` | Optional | Explicit exclusions |
| `# Acceptance Criteria:` | Yes | Full AC listing with IDs, versions, and states |
| `@FUNC_ID:FUNC-<nnn>` tag | Yes | Machine-parseable Functionality ID (feature-level tag) |

### Acceptance Criterion (AC)

A binary pass/fail statement that defines a verifiable condition.

Each AC is:
- **Atomic** — one input condition, one observable outcome
- **Binary** — clear pass/fail; no "usually" or "typically"
- **Single placeholder** — at most ONE `{placeholder}` per AC statement. If two aspects vary independently, write a separate AC for each.

**AC identifier and state format** (in file header and entity files):

```
AC:<parent-id>-<nn> (v<version> - <State>)
   - <atomic description, with at most one {placeholder} for a variable value>
   - <Placeholder>: value1, value2, ...
   - Rationale: <business context, policy reference, or design decision>  ← optional
```

State values: `Planned | Implemented | Active | Deprecated`

**Scenario traceability:** living-doc scenarios (US and Functionality feature files) carry two
complementary annotations — a human-readable `# AC:` comment and a machine-readable `@AC:` tag:

```gherkin
# AC:US-1-01 (v1.0.0 - Active) — customer places an order with a saved payment method
@AC:US-1-01
Scenario: Customer successfully places an order
  ...
```

When a scenario covers only **one aspect** of a multi-aspect AC, encode the aspect directly in
the `@AC:` tag using the `/param:value` param syntax, and mirror it in the comment:

```gherkin
# AC:US-1-01 (v1.0.0 - Active) — displays {required field} on login screen | aspect: username input
@AC:US-1-01/aspect:username-input
Scenario: Login form shows the username input field
  ...
```

Multiple ACs — one comment + tag pair per AC:

```gherkin
# AC:US-1-01 (v1.0.0 - Active) — invalid credentials show an error message
# AC:US-1-02 (v1.0.0 - Active) — account lockout after 3 failed attempts
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

- The `# AC:` comment is human-readable context: AC ID, version, state, description, optional aspect.
- The `@AC:` Cucumber tag is machine-readable: drives script scanning, coverage reports, and sync checks.
- US scenarios: `@AC:US-<n>-<nn>` (e.g. `@AC:US-1-01`)
- Functionality scenarios: `@AC:FUNC-<nnn>-<nn>` (e.g. `@AC:FUNC-001-01`)
- Both annotations are required for living-doc feature files (`features/us/` and `features/functionalities/`).
- Feature files outside the living-doc directories (smoke tests, regression suites, exploratory probes)
  do not require `@AC:` tags.

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

**User Story AC examples** (in the `# Acceptance Criteria:` file header block):

```
AC:US-001-01 (v1.0.0 - Active)
   - The login screen displays {required field}.
   - Required field: username input, password input, login button
   - Rationale: Accessibility standard — all interactive controls must be visible on load.

AC:US-001-02 (v1.1.0 - Active)
   - An inline field validation message is shown when invalid credentials are submitted.

AC:US-001-03 (v2.1.0 - Deprecated - removal planned v3.0.0)
   - A "Remember me" checkbox retains the session across browser restarts.
   - Rationale: Deprecated due to security policy change in v2.0 — persistent sessions no longer permitted.
```

**Functionality AC examples** (in the `# Acceptance Criteria:` file header block):

```
AC:FUNC-001-01 (v1.0.0 - Active)
   - Returns valid=true when the password satisfies all complexity rules.

AC:FUNC-001-02 (v1.0.0 - Active)
   - Raises {error code} when the credential check fails.
   - Error code: INVALID_PASSWORD, USER_NOT_FOUND, ACCOUNT_LOCKED
   - Rationale: Distinct error codes per failure reason, required by the global auth error contract.

AC:FUNC-001-03 (v1.0.0 - Active)
   - Rejects passwords shorter than 8 characters.
```

---

## Relationship diagram

```
User Story (US)
  └── links to: Feature (FEAT)
                    └── owns: Functionality (FUNC)
                                    └── owns: Functionality ACs
                                    └── maps to: Functionality feature file (system test)
                                    |              features/functionalities/<feat>/<func>.feature
                                    |              @FUNC_ID tag + @AC:FUNC-nnn-nn tagged scenarios
                                    |              └── implemented by: Step Definitions
                                    └── can map to: unit/integration tests
  └── owns: User Story ACs (in # Acceptance Criteria: header block)
                  └── linked via: @AC:US-n-nn tags on Scenarios
                  └── can map to: E2E BDD Scenarios (features/us/*.feature)
                                       @US_ID tag + @AC:US-n-nn tagged scenarios
                                       └── implemented by: Step Definitions
                                                               └── delegates to: PageObjects
                  └── can map to: API coverage / contract tests
```

---

## What each skill creates or consumes

| Skill | Creates | Reads |
|---|---|---|
| `living-doc-create-user-story` | User Story entity | Feature entities |
| `living-doc-create-feature` | Feature entity | User Story entities |
| `living-doc-create-functionality` | Functionality entity + Functionality feature file stub | Feature entity |
| `living-doc-pageobject-scan` | PageObject files + Functionality feature file stubs | App URL or test suite |
| `living-doc-scenario-creator` | E2E BDD scenario files (US) + Functionality feature files (FUNC) | US / FUNC entities, PageObjects |
| `living-doc-tutorial-creator` | Tutorial documents | BDD scenario files, User Story entities |
| `living-doc-gap-finder` | Gap report | All of the above |
