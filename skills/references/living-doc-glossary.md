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

The header comment block at the top of a US feature file holds all US metadata and is mined
during living documentation output generation.

```gherkin
# =============================================================================
# LIVING DOC — US-<n> · <US Title>
# =============================================================================
# source:          https://github.com/<org>/<repo>/issues/<n>    ← optional
# status:          planned | active | deprecated
# business_value:
#   - <bullet describing the business outcome>
# not_in_scope:                                                  ← optional
#   - <item excluded from this US>
# preconditions:                                                 ← optional
#   - <system state required before test>
#
# acceptance_criteria:
#
#   AC:US-<n>-01 (v<version> - <State>)
#     - <description of the AC>
#     - <Aspect>: <value1>, <value2>      ← optional; used for {placeholder} ACs
#
#   AC:US-<n>-02 (v<version> - <State>)
#     - <description of the AC>
# =============================================================================

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

**Header fields:**
| Field | Required | Purpose |
|---|---|---|
| `# source:` | Optional | Link to the original issue tracker entry or the pre-BDD living doc location |
| `# status:` | Yes | `planned` · `active` · `deprecated` |
| `# business_value:` | Yes | Why this User Story exists (bullets) |
| `# not_in_scope:` | Optional | Explicit exclusions |
| `# preconditions:` | Optional | System-level state required before test execution |
| `# acceptance_criteria:` | Yes | Full AC listing with IDs, versions, and states |
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

#### UI surface — PageObject file header

Every PageObject file opens with a living-doc header block that embeds the canonical Feature fields. Use this format so each file is self-describing and traceable without opening a separate registry.

**Required fields:**

| Field | Canonical values |
|---|---|
| `surface_type` | `UI` · `API` · `Service` · `Worker` · `Module` · `Library` |
| `route` | URL path — use `{param}` for dynamic segments |
| `owners` | Team name(s), comma-separated |
| `status` | `active` · `planned` · `candidate` · `deprecated` |
| `purpose` | One-to-two sentence description in business language |
| `user_stories` | `US-N` IDs, comma-separated — or `none` (triggers orphan warning in gap reports) |
| `functionalities` | `FUNC-N` IDs, comma-separated — or `none` (triggers a reminder to define FUNCs) |
| `external_dependencies` | Service or API names this surface calls — or `none` |
| `page-object` | Filename of this PageObject |

**Optional fields (for specific surface types):**

| Field | When |
|---|---|
| `wizard-steps` | Multi-step wizard UI — list the named steps in order |
| `stub-reason` | `status: candidate` — one-to-two sentence statement of **why** the surface is not yet fully instrumented; treated as tech-debt resolvable by instrumenting the template and re-scanning |

---

#### Two header formats: Full header vs Cross-reference header

A PageObject file uses one of two formats depending on whether it is the **primary surface owner** or a **secondary file** that implements part of a surface already owned elsewhere.

**When to use each:**

| Situation | Format |
|---|---|
| One PageObject = one distinct navigable surface (URL or modal) | **Full header** |
| Multiple PageObjects share one URL (e.g. wizard steps, sub-pages, dialogs) — one file is the primary owner, the others are implementation helpers | **Cross-reference header** — secondary files only |

**Rule:** exactly one file per Feature carries the full header. Every other file that contributes to the same Feature carries a cross-reference header with `parent-feat` pointing to the Feature ID. This keeps traceability fields (`user_stories`, `functionalities`, `external_dependencies`) in a single authoritative location.

**Wizard example:** FEAT-042 (Account Setup Wizard) lives at one URL. `AccountSetupWizardPage.ts` is the primary file and carries the full header. `AccountSetupWizardProfilePage.ts`, `AccountSetupWizardPreferencesPage.ts`, and the other step files each carry a cross-reference header pointing `parent-feat: FEAT-042`. Adding a wizard step never requires editing the Feature registry or duplicating traceability data.

---

**Full header required fields:**

| Field | Canonical values |
|---|---|
| `surface_type` | `UI` · `API` · `Service` · `Worker` · `Module` · `Library` |
| `route` | URL path — use `{param}` for dynamic segments |
| `owners` | Team name(s), comma-separated |
| `status` | `active` · `planned` · `candidate` · `deprecated` |
| `purpose` | One-to-two sentence description in business language |
| `user_stories` | `US-N` IDs, comma-separated — or `none` (triggers orphan warning in gap reports) |
| `functionalities` | `FUNC-N` IDs, comma-separated — or `none` (triggers a reminder to define FUNCs) |
| `external_dependencies` | Service or API names this surface calls — or `none` |
| `page-object` | Filename of this PageObject |

**Full header example:**

```typescript
/* =============================================================================
 * LIVING DOC — FEAT-042 · Account Setup Wizard
 * =============================================================================
 * surface_type:          UI
 * route:                 /app/accounts/setup
 * owners:                Platform Team
 * status:                active
 * wizard-steps:          Profile · Preferences · Review · Confirm
 * purpose:               Multi-step wizard for creating and configuring a new account.
 * user_stories:          US-10, US-12
 * functionalities:       FUNC-005, FUNC-006
 * external_dependencies: accounts-api
 * page-object:           AccountSetupWizardPage.ts
 * ============================================================================= */
```

---

**Cross-reference header required fields:**

| Field | Canonical values |
|---|---|
| `parent-feat` | `FEAT-<nnn>` — ID of the primary Feature that owns this surface. **Required.** |
| `route` | URL path of this specific sub-surface — use `{param}` for dynamic segments |
| `owners` | Team name(s), comma-separated |
| `status` | `active` · `planned` · `candidate` · `deprecated` |
| `purpose` | One sentence: what this step or sub-surface does, in business language — no FEAT IDs, no internal references |
| `page-object` | Filename of this PageObject |

The following fields are **intentionally omitted** from the cross-reference header — they belong only on the primary Feature file: `surface_type`, `user_stories`, `functionalities`, `external_dependencies`.

**Cross-reference header example:**

```typescript
/* =============================================================================
 * LIVING DOC — FEAT-042 · Account Setup Wizard  [cross-reference]
 * =============================================================================
 * This file implements Step 1 (Profile) of the Account Setup Wizard.
 * The authoritative Feature header is in AccountSetupWizardPage.ts.
 *
 * parent-feat:  FEAT-042
 * route:        /app/accounts/setup  (wizard stays on this URL)
 * owners:       Platform Team
 * status:       active
 * purpose:      Step 1 (Profile) — user profile fields: display name, email address,
 *               and role selection.
 * page-object:  AccountSetupWizardProfilePage.ts
 * ============================================================================= */
```

---

#### Where operational notes belong

The PageObject **header block and class JSDoc are living-doc contracts** — they encode identity, traceability, and status. They are not a changelog, scan diary, or issue tracker.

| Information type | Correct location | NOT in |
|---|---|---|
| Missing `data-cy` attributes discovered during a scan | `manifest.json` → `coverage_gaps[]` | Header or class JSDoc |
| Reason a surface is not yet fully instrumented | Header field `stub-reason:` (one or two lines) | Free-text NOTE block |
| Proposed `data-cy` names for missing elements | `manifest.json` → `coverage_gaps[].suggestedDataCy` | Header or class body |
| Open issue reference (e.g. OI-08, P1) | `manifest.json` → `coverage_gaps[].note` | Header or class JSDoc |
| Scan date or scan session tag | `manifest.json` → `last_scanned` | Header or class JSDoc |
| `@stub` / `@pending` JSDoc tags on the class | — (use `status: candidate` + `stub-reason:`) | Class JSDoc |
| Implementation note explaining a locator strategy | Inline code comment on the locator or method | Header block |

**`status: candidate` and `stub-reason:` as resolvable tech-debt**

A `status: candidate` surface is **not a permanent state** — it is a living-doc tech-debt item. The surface is known, documented, and linked to User Stories; what is missing is template instrumentation (`data-cy` attributes) that would allow full PageObject locators to be written. The resolution path is always:

1. Instrument the component template with the `data-cy` values listed in `manifest.json` `coverage_gaps[]` (use the `data-cy-instrument` skill).
2. Re-scan — the scan session updates the PageObject locators.
3. Promote `status: candidate` → `status: active` and remove `stub-reason:`.

`stub-reason:` records the factual state at time of discovery (≤ two lines). The value must be free of:
- internal tool or file references (e.g. `issue-missing-data-cy.md`)
- data-cy attribute names or implementation detail
- action items ("raise with dev team", "will resolve once…")
- scan session tags except as a factual date anchor (e.g. `discovered [scan: 2026-05-28-b]`)

**`@pending` JSDoc on an individual locator property** is acceptable — it explains why that specific locator uses a fallback strategy and what resolves it. It is implementation-level, not an operational note on the surface as a whole.

---

**Common mistakes:**

| Anti-pattern | Correct |
|---|---|
| `type: screen` | `surface_type: UI` |
| `owner: Team` | `owners: Team` (plural key) |
| `status: ACTIVE` | `status: active` (lowercase) |
| `status: STUB` | `status: candidate` + `stub-reason:` field |
| `functionalities:` omitted | `functionalities: none` |
| `user_stories:` omitted | `user_stories: none` |
| `external_dependencies:` omitted | `external_dependencies: none` |
| `parent-feat:` omitted from cross-reference file | Every secondary file for a shared Feature must declare `parent-feat` |
| `page-object:` omitted from cross-reference file | `page-object:` is required in both formats — it names the file being read |
| `user_stories:` duplicated in cross-reference file | These fields live only on the primary Feature file; omit from cross-references |
| Multiple files claiming the same Feature without `[cross-reference]` tag | Only one file carries the full header; all others must use `[cross-reference]` format |
| NOTE block in header about missing `data-cy` or open issues | Move to `manifest.json` `coverage_gaps[]`; keep only `stub-reason:` in the header |
| `@stub` or `@pending` on the class JSDoc | Use `status: candidate` + `stub-reason:` in the header instead |
| `purpose: Step 1 of FEAT-006 — ...` | `purpose` must not contain FEAT IDs — use `Step 1 (About) — ...` instead; the ID is already in the title line and `parent-feat` |
| `purpose:` contains "NOT a …" or "Accessed via …" | Purpose describes what the surface does; exclude defensive statements and navigation instructions |
| `route:` contains a `data-cy` attribute name (e.g. `btn-import-domain`) | `route:` is a URL path or "modal overlay — no dedicated URL"; locator IDs belong in the PageObject body |
| `wizard-steps:` contains `[scan: …]` tag | `wizard-steps:` is a clean ordered list; scan provenance belongs in `manifest.json` |
| Non-spec field added to header (e.g. `query_params:`) | Only use fields defined in the Required or Optional tables; extra fields are ignored by miners and silently dropped |
| Cross-reference prose mentions FUNC IDs or file names | Cross-reference prose is mined as-is — keep it to one human-readable sentence: which step/sub-surface this file implements and where the authoritative header lives |
| `stub-reason:` contains action items, internal tool refs, or data-cy names | `stub-reason:` states only the factual reason (≤ two lines); action items go in `manifest.json` `coverage_gaps[]` |

### Functionality (FUNC)

An atomic, fast-testable behavior — a single verb phrase describing one responsibility.

- ID format: `FUNC-<nnn>` (e.g. `FUNC-001`)
- Name: `<parent Feature name> – <behavior phrase>` (e.g. "Login Page – Validate Password Strength")
- Belongs to: one parent **Feature**
- Owns: **Functionality-level Acceptance Criteria** (atomic input to output statements)
- Test anchor: a **Functionality feature file** under `features/liv_doc_func/` — one file per
  Functionality, containing all AC-linked system-test scenarios once implemented.
  File name pattern: `func-<nnn>-<feature-name-kebab>-<behavior-kebab>.feature`
  e.g. `func-001-authentication-screen-credential-based-login.feature`
- Status: `planned | active | deprecated`
- Deprecation metadata (set when `status: deprecated`):
  - `deprecated_at` — date the entity was deprecated
  - `deprecation_reason` — why it was deprecated
  - `superseded_by` — ID of the replacement entity (optional)

Functionalities differ from User Story ACs: they are atomic and fast-testable, not end-to-end.
A single User Story may trigger multiple Functionalities.

**Functionality feature file header format:**

```gherkin
# =============================================================================
# LIVING DOC — FUNC-<nnn> · <Feature Name> — <Functionality Name>
# =============================================================================
# source:    https://github.com/<org>/<repo>/issues/<n>          ← optional
# status:    planned | active | deprecated
# parent:    FEAT-<nnn>
# func_type: component_state | component_action | button_action |
#            field_validation | calculation | visibility | navigation_rule
# rationale:                                                     ← optional
#   - <why this FUNC is scoped this way — business or design decision context>
# not_in_scope:                                                  ← optional
#   - <exclusion>
#
# acceptance_criteria:
#
#   AC:FUNC-<nnn>-01 (v<version> - <State>)
#     - <description in business language — no data-cy IDs in AC text>
#
#   AC:FUNC-<nnn>-02 (v<version> - <State>)
#     - <description>
# =============================================================================

@FUNC_ID:FUNC-<nnn>
Feature: <Feature Name> — <Functionality Name>
  <Purpose: one-to-two sentences describing what this FUNC covers, in business
  language. Present only when purpose adds context beyond the title.>   ← optional

  # No scenarios yet — uncovered ACs flagged by coverage_report.py.
  # When adding scenarios: include both # AC:<id> comment and @AC:<id>[/param:value] tag above each Scenario.
```

**Header fields:**
| Field | Required | Purpose |
|---|---|---|
| `# source:` | Optional | Link to the original issue tracker entry or the pre-BDD living doc location |
| `# status:` | Yes | `planned` · `active` · `deprecated` |
| `# parent:` | Yes | Parent Feature ID (`FEAT-<nnn>`) |
| `# func_type:` | Yes | Category of behavior this Functionality represents (see table below) |
| `# rationale:` | Optional | **Why** this FUNC is scoped the way it is — business context, a deliberate design decision, or a constraint that explains the boundary. Not for implementation notes (how something works internally). |
| `# not_in_scope:` | Optional | Explicit exclusions |
| `# acceptance_criteria:` | Yes | Full AC listing in business language — do not include `data-cy` IDs or implementation names in AC text |
| `@FUNC_ID:FUNC-<nnn>` tag | Yes | Machine-parseable Functionality ID (feature-level tag) |
| Feature description (below `Feature:`) | Optional | One-to-two sentence purpose in business language. Use when the title alone is not self-explanatory. Replaces `# purpose:` — not a header field. |

**`func_type` values:**

| Value | What it documents | PageObject anchor |
|---|---|---|
| `component_state` | Visible state of elements on load (presence, enabled/disabled, default text) AND what a data-bound component renders per data state (populated, empty, error) | `constructor` locators, data-bearing locators |
| `component_action` | Observable response within a self-contained component to an internal interaction — no discrete button, no system-level side effect (e.g. live search, autocomplete, accordion, carousel, tab content) | Component input/state locators |
| `button_action` | Observable outcome(s) after a specific discrete control is triggered — may span multiple resulting steps (e.g. redirect, entity created, dialog opened) | `btn-*` locators |
| `field_validation` | Rule enforced on a single field's value — inline error, enabled state, accepted/rejected input | `input-*` locators |
| `calculation` | Value computed and displayed from one or more inputs, independent of form submission | Display-only locators |
| `visibility` | Element presence, content, or enabled state conditional on a runtime state — condition is optional context and may be role, prior action, data presence, or config (e.g. owner sees action buttons, section appears after step complete) | Any conditional locator |
| `navigation_rule` | When and where the app routes, driven by action or system state — only when routing has a distinct precondition or business rule | Route assertion |

**Scoping rules:**

- **One FUNC, one cause.** If two behaviors share a trigger, they are one FUNC with two ACs. If two behaviors have different triggers, they are two FUNCs.
- **`component_state`** — scope to a logical group, not individual elements. "Login form controls on load" is one FUNC. Do not write one FUNC per locator. For data-bound components, each distinct data state (populated / empty / error) is an AC on the same FUNC, not a separate FUNC.
- **`component_action`** — one FUNC per distinct component behavior. If the same component has multiple independent internal behaviors (live search AND column sort), they are separate FUNCs.
- **`button_action`** — one FUNC per distinct button. A button that produces multiple observable steps is still one FUNC; the steps become multiple ACs. Two buttons = two FUNCs. Form submission is `button_action` — the trigger is the submit control.
- **`field_validation`** — one FUNC per distinct validation rule, not one per field. The same rule applied to multiple fields = one FUNC with a `{field}` placeholder AC.
- **`calculation`** — only when the derived value is observable independently of a submission. If the result only appears after a form submit, it is an AC on the `button_action` FUNC.
- **`visibility`** — use when an element's presence or state depends on a condition. The condition is descriptive context in the AC, not a required field. Distinct from `component_state` (always-true on load) and `component_action` (response to interaction).
- **`navigation_rule`** — only for routing behaviors with a distinct precondition or business rule. A redirect that is always the result of a button action is an AC on that `button_action` FUNC, not a separate `navigation_rule`.

> `test_type` (unit vs integration vs system) is NOT a FUNC header field — it belongs at scenario level as a tag (e.g. `@test_type:system`).

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

## ExplorationFixture

An **ExplorationFixture** is a named set of field→value declarations attached to a specific route in `seed.yaml`. It tells the exploration agent how to fill forms so it can enter wizards, open dialogs, and discover UI surfaces that are otherwise unreachable by passive observation.

### value_class taxonomy

| Class | Meaning | How the agent sources it |
|---|---|---|
| `copyable` | Value can be reused verbatim across runs — taken from an existing entity in the app | Navigate to the entity list; read an actual field value; replay it |
| `derived` | Must be transformed from an existing entity — e.g. append `-copy` to a domain name to avoid duplicate rejection | Read existing value; apply a known transformation rule |
| `fake` | Any syntactically valid value — real-world existence not required (e.g. a description, an email address) | Generate locally from label + placeholder + field type |
| `real-world` | Must exist in the real environment for submission to succeed (e.g. a Glue table name, a tenant ID, an AWS account ID) | Sourced from `seed.yaml form_fixtures` or user-provided via Source E pause |

### Sourcing cascade (applied in priority order)

1. **`seed.yaml form_fixtures`** — pre-declared by user or written by the agent in a prior session.
2. **Existing app entities** — navigate to the entity list for this surface type; read a sample entity's actual field values; copy or derive.
3. **Field context inference** — read label + placeholder + tooltip + adjacent validation hint text → infer a plausible `fake` value (`"Domain name"` → `"E2E Test Domain"`, `email` field → `"test@example.com"`).
4. **User-assist pause** — none of the above is sufficient for a `real-world` field → show user the form, request the value, record it back to `form_fixtures` with `source: user_provided`.

### Input validation probing

After a successful form fill and submission, the agent probes validation behaviour on each text input:

| Probe | Input | What to observe |
|---|---|---|
| Special characters | `<>'"&\` | Inline error, silent strip, or truncation |
| Oversized input | 200+ random characters | Character counter, truncation at max length, or rejection message |
| Wrong type | Alphabetic text in a numeric or date field | Inline validation message or field rejection |
| Duplicate detection | Identical value to a known existing entity name | Duplicate-rejected error message and its `data-cy` |

Scan the form after each probe — run the core scan and elements-without-data-cy scripts to capture `data-cy` error messages, character counters, and validation banners that are only visible during invalid input. These become source material for `field_validation` Functionality stubs.

### seed.yaml schema

A fixture entry uses either a single `value` shorthand (simple fields) or a `values[]` array
(multi-branch fields). A `condition` restricts the field to a specific traversal context.

```yaml
form_fixtures:
  /auth/all-domains/create-domain/about:

    # Simple single value
    - field_data_cy: domain-name
      value_class: fake
      value: "E2E Exploration Domain"
      source: inferred          # inferred | user_provided | env_var | existing_entity

    # Multiple values — agent treats each as a separate traversal branch.
    # The first (label: default) is used for the happy path; labelled alternates
    # are explored afterwards and may open different form sections or sub-routes.
    - field_data_cy: domain-type
      value_class: copyable
      values:
        - label: default
          value: "BATCH"
          source: existing_entity
        - label: streaming-path   # explores different form section
          value: "STREAMING"
          source: existing_entity

    # Conditional field — only filled when another field holds a specific value.
    # Useful for fields that appear or become mandatory based on a prior selection.
    - field_data_cy: stream-endpoint
      value_class: real-world
      value: env:TEST_STREAM_ENDPOINT
      source: env_var
      condition:
        when_field: domain-type
        when_value: STREAMING

    # Real-world field resolved via user-assist pause
    - field_data_cy: tenant-id
      value_class: real-world
      value: env:TEST_TENANT_ID
      source: env_var
```

**Field reference:**

| Key | Required | Purpose |
|---|---|---|
| `field_data_cy` | Yes | `data-cy` attribute of the target input element |
| `value_class` | Yes | `copyable` / `derived` / `fake` / `real-world` |
| `value` | One of `value` or `values` | Shorthand for a single fill value |
| `values[]` | One of `value` or `values` | Array of labelled values; agent explores each as a separate traversal branch |
| `values[].label` | Yes (when `values` used) | Branch identifier; `default` marks the happy-path value |
| `values[].value` | Yes | The actual fill value |
| `source` | Yes | `inferred` \| `user_provided` \| `env_var` \| `existing_entity` |
| `condition` | No | Restricts the fill to a specific context |
| `condition.when_field` | Yes (when `condition` used) | `data-cy` of the controlling field |
| `condition.when_value` | Yes (when `condition` used) | Value the controlling field must hold |

### manifest field_constraints schema

Validation findings are stored per-field in the manifest `navigation_context.field_constraints` for the route:

```json
"field_constraints": [
  {
    "field_data_cy": "domain-name",
    "max_length": 100,
    "special_chars": "rejected",
    "duplicate": "rejected-with-error",
    "duplicate_error_data_cy": "domain-name-duplicate-error"
  },
  {
    "field_data_cy": "tenant-id",
    "allowed_format": "alphanumeric",
    "real_world_required": true
  }
]
```

### Lifecycle

| Event | What happens |
|---|---|
| First form encountered | Agent applies sourcing cascade; fills form using `default` values; explores labelled alternate branches for multi-value fields; probes validation |
| `condition` field not yet visible | Agent skips the field until the controlling field holds the required `when_value` |
| `real-world` field has no resolvable value | User-assist pause → user provides value → saved to `form_fixtures` with `source: user_provided` |
| Validation probe discovers new `data-cy` | Added to manifest `elements`; flagged as candidate for `field_validation` Functionality |
| Next scan session | Agent reads `form_fixtures` from `seed.yaml`; skips sourcing cascade for pre-declared fields |
| Constraint changes (e.g. max length increased) | Agent detects mismatch on re-probe; updates `field_constraints`; flags in `breaking-changes.md` |

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
| `living-doc-pageobject-scan` | PageObject files + Functionality feature file stubs + `ExplorationFixture` entries in `seed.yaml` | App URL or test suite; `seed.yaml form_fixtures` |
| `living-doc-scenario-creator` | E2E BDD scenario files (US) + Functionality feature files (FUNC) | US / FUNC entities, PageObjects |
| `living-doc-tutorial-creator` | Tutorial documents | BDD scenario files, User Story entities |
| `living-doc-gap-finder` | Gap report | All of the above |
