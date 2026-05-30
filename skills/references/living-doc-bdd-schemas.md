# Living Documentation — BDD Schemas

Templates and schemas for BDD automation files. Load this file when writing or validating:
- US or Functionality **feature file headers** (`features/us/`, `features/functionalities/`)
- **PageObject file headers** (full header or cross-reference header)
- **ExplorationFixture** entries in `seed.yaml`
- **manifest.json** `field_constraints` entries

For entity definitions (IDs, status vocabulary, AC format, relationship diagram) see [living-doc-glossary](./living-doc-glossary.md).

---

## US Feature File Header

Header comment block at the top of every `features/us/us-<nnn>-<kebab>.feature` file.
Holds all US metadata and is mined during living documentation output generation.

```gherkin
# =============================================================================
# LIVING DOC — US-<n> · <US Title>
# =============================================================================
# source:          https://github.com/<org>/<repo>/issues/<n>    ← optional
# status:          PLANNED | IN_REVIEW | ACTIVE | DEPRECATED
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
| `# status:` | Yes | `PLANNED` · `IN_REVIEW` · `ACTIVE` · `DEPRECATED` |
| `# business_value:` | Yes | Why this User Story exists (bullets) |
| `# not_in_scope:` | Optional | Explicit exclusions |
| `# preconditions:` | Optional | System-level state required before test execution |
| `# acceptance_criteria:` | Yes | Full AC listing with IDs, versions, and states |
| `@US_ID:US-<n>` tag | Yes | Machine-parseable User Story ID (feature-level tag) |

---

## Functionality Feature File Header

Header comment block at the top of every `features/functionalities/<feat-kebab>/func-<nnn>-<kebab>.feature` file.

```gherkin
# =============================================================================
# LIVING DOC — FUNC-<nnn> · <Feature Name> — <Functionality Name>
# =============================================================================
# source:    https://github.com/<org>/<repo>/issues/<n>          ← optional
# status:    PLANNED | IN_REVIEW | ACTIVE | DEPRECATED
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
| `# status:` | Yes | `PLANNED` · `IN_REVIEW` · `ACTIVE` · `DEPRECATED` |
| `# parent:` | Yes | Parent Feature ID (`FEAT-<nnn>`) |
| `# func_type:` | Yes | Category of behavior this Functionality represents (see table below) |
| `# rationale:` | Optional | **Why** this FUNC is scoped the way it is — business context, a deliberate design decision, or a constraint that explains the boundary. Not for implementation notes. |
| `# not_in_scope:` | Optional | Explicit exclusions |
| `# acceptance_criteria:` | Yes | Full AC listing in business language — do not include `data-cy` IDs or implementation names in AC text |
| `@FUNC_ID:FUNC-<nnn>` tag | Yes | Machine-parseable Functionality ID (feature-level tag) |
| Feature description (below `Feature:`) | Optional | One-to-two sentence purpose in business language. Use when the title alone is not self-explanatory. |

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

---

## PageObject File Header

Every PageObject file opens with a living-doc header block. Use this format so each file is self-describing and traceable without opening a separate registry.

### Required fields

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

**Optional fields:**

| Field | When |
|---|---|
| `wizard-steps` | Multi-step wizard UI — list the named steps in order |
| `stub-reason` | `status: candidate` — one-to-two sentence statement of **why** the surface is not yet fully instrumented; treated as tech-debt resolvable by instrumenting the template and re-scanning |

### Two header formats: Full vs Cross-reference

A PageObject file uses one of two formats depending on whether it is the **primary surface owner** or a **secondary file** that implements part of a surface already owned elsewhere.

| Situation | Format |
|---|---|
| One PageObject = one distinct navigable surface (URL or modal) | **Full header** |
| Multiple PageObjects share one URL (e.g. wizard steps, sub-pages, dialogs) — one file is the primary owner, the others are implementation helpers | **Cross-reference header** — secondary files only |

**Rule:** exactly one file per Feature carries the full header. Every other file that contributes to the same Feature carries a cross-reference header with `parent-feat` pointing to the Feature ID. This keeps traceability fields (`user_stories`, `functionalities`, `external_dependencies`) in a single authoritative location.

**Wizard example:** FEAT-042 (Account Setup Wizard) lives at one URL. `AccountSetupWizardPage.ts` is the primary file and carries the full header. `AccountSetupWizardProfilePage.ts`, `AccountSetupWizardPreferencesPage.ts`, and the other step files each carry a cross-reference header pointing `parent-feat: FEAT-042`. Adding a wizard step never requires editing the Feature registry or duplicating traceability data.

---

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
| `purpose` | One sentence: what this step or sub-surface does, in business language — no FEAT IDs |
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

### Where operational notes belong

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

A `status: candidate` surface is **not a permanent state**. The surface is known, documented, and linked to User Stories; what is missing is template instrumentation (`data-cy` attributes). Resolution path:

1. Instrument the component template with the `data-cy` values listed in `manifest.json` `coverage_gaps[]` (use the `data-cy-instrument` skill).
2. Re-scan — the scan session updates the PageObject locators.
3. Promote `status: candidate` → `status: active` and remove `stub-reason:`.

`stub-reason:` records the factual state at time of discovery (≤ two lines). Must not contain: internal tool or file references, data-cy attribute names, action items, or scan session tags except as a factual date anchor.

### Common mistakes

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
| `page-object:` omitted from cross-reference file | `page-object:` is required in both formats |
| `user_stories:` duplicated in cross-reference file | These fields live only on the primary Feature file |
| Multiple files claiming the same Feature without `[cross-reference]` tag | Only one file carries the full header |
| NOTE block in header about missing `data-cy` or open issues | Move to `manifest.json` `coverage_gaps[]`; keep only `stub-reason:` in the header |
| `@stub` or `@pending` on the class JSDoc | Use `status: candidate` + `stub-reason:` in the header instead |
| `purpose:` contains FEAT IDs | `purpose` must not contain FEAT IDs — ID is already in the title line and `parent-feat` |
| `purpose:` contains "NOT a …" or "Accessed via …" | Purpose describes what the surface does; exclude defensive statements and navigation instructions |
| `route:` contains a `data-cy` attribute name | `route:` is a URL path; locator IDs belong in the PageObject body |
| `wizard-steps:` contains `[scan: …]` tag | `wizard-steps:` is a clean ordered list; scan provenance belongs in `manifest.json` |
| Non-spec field added to header | Only use fields defined in the Required or Optional tables |
| Cross-reference prose mentions FUNC IDs or file names | Keep to one human-readable sentence: which step/sub-surface this file implements and where the authoritative header lives |
| `stub-reason:` contains action items or internal tool refs | `stub-reason:` states only the factual reason (≤ two lines) |

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

Scan the form after each probe to capture `data-cy` error messages, character counters, and validation banners that are only visible during invalid input. These become source material for `field_validation` Functionality stubs.

### seed.yaml schema

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
