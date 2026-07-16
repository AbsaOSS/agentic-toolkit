# Living Documentation — BDD Schemas

Templates and schemas for BDD automation files. Load this file when writing or validating:
- The **Project Profile** (`.project-profile.yaml`) — the per-project config that supplies all conventions below
- US or Functionality **feature file headers**
- **PageObject file headers** (full header or cross-reference header)
- **seed.yaml** (Business Seed) and **manifest.json** (Exploration Manifest)

For entity definitions (IDs, status vocabulary, AC format, relationship diagram) see [living-doc-glossary](./living-doc-glossary.md).

**Schema reference:** For JSON schema validation, see [schemas/](./schemas/) directory:
- [project-profile.schema.json](./schemas/project-profile.schema.json) — Project Profile validation
- [seed.schema.json](./schemas/seed.schema.json) — seed.yaml validation  
- [manifest.schema.json](./schemas/manifest.schema.json) — manifest.json validation

---

## Project Profile (config-driven conventions)

**Every value a skill could otherwise hardcode — directory names, the test-id attribute,
state-casing, tag conventions — lives in one Project Profile file.** Skills read the profile at
session start and never assume defaults. This keeps the toolkit portable across projects that use
different directory layouts or naming.

**Location:** `<bdd_artifacts_dir>/.project-profile.yaml` (default `.copilot/bdd/.project-profile.yaml`).
The agent creates it on first run from the defaults below and confirms each value with the user.
If it already exists, load it and skip the prompt.

```yaml
# .copilot/bdd/.project-profile.yaml — defaults shown match the reference (AUL) project.
test_id_attribute: data-cy            # what page.getByTestId() resolves to (Playwright testIdAttribute)

feature_dirs:
  user_story:    features/liv_doc_us      # E2E User Story feature files
  functionality: features/liv_doc_func    # Functionality (system-test) feature files

paths:
  bdd_artifacts:  .copilot/bdd            # seed.yaml, manifest.json, breaking-changes.md
  pageobjects:    playwright/pages
  steps:          playwright/steps

# AC state vocabulary as written inside `# AC:` blocks and feature-file headers (lowercase with underscores).
ac_states: [planned, in_review, active, deprecated]

# PageObject header `status:` vocabulary (lowercase).
pageobject_statuses: [planned, candidate, active, deprecated]

# Scenario tagging conventions (see "Feature file tags" below).
scenario_conventions:
  feature_tag:        true     # @US_ID:<id> / @FUNC_ID:<id> on the Feature
  domain_tag:         true     # optional second feature-level tag, e.g. @domain_create
  suite_tags:         ["@Regression"]   # additional scenario-level tags allowed beside @AC:
  section_banners:    true     # "# *** Happy day scenarios ***" / "# *** Negative scenarios ***"

manifest_shape: object         # manifest is an object with routes array (see Manifest schema)
```

| Field | Used by | Default (AUL) |
|---|---|---|
| `test_id_attribute` | pageobject-scan, data-cy-instrument, gherkin-step | `data-cy` |
| `feature_dirs.user_story` | scenario-creator, gherkin-living-doc-sync, gap-finder, scripts | `features/liv_doc_us` |
| `feature_dirs.functionality` | scenario-creator, pageobject-scan, gap-finder, scripts | `features/liv_doc_func` |
| `paths.bdd_artifacts` | pageobject-scan, data-cy-instrument | `.copilot/bdd` |
| `paths.pageobjects` / `paths.steps` | pageobject-scan, gherkin-step | `playwright/pages` / `playwright/steps` |
| `ac_states` | all catalog skills, scenario-creator, gherkin-living-doc-sync | `active` etc. (lowercase with underscores) |
| `pageobject_statuses` | pageobject-scan | `active` etc. (lowercase) |
| `scenario_conventions` | scenario-creator, gherkin-living-doc-sync | as shown |

> **Casing rule:** AC states use **lowercase with underscores** inside `# AC:` blocks and entity files
> (e.g. `- active`, `- in_review`). PageObject header `status:` is also lowercase (`status: active`).
> Wherever this document or a skill shows `ACTIVE`/`PLANNED` in upper-case prose, it refers to the
> *logical* state; the *written* form is always lowercase with underscores.

---

## US Feature File Header

Header comment block at the top of every User Story feature file —
`<feature_dirs.user_story>/us-<nnn>-<kebab>.feature` (default `features/liv_doc_us/`).
Holds all US metadata and is mined during living documentation output generation.

```gherkin
# =============================================================================
# LIVING DOC — US-<n> · <US Title>
# =============================================================================
# source:          https://github.com/<org>/<repo>/issues/<n>    ← optional
# status:          active        ← one of profile `ac_states` (planned | in_review | active | deprecated)
# business_value:
#   - <bullet describing the business outcome>
# preconditions:                                                 ← optional; inherited by all ACs
#   - <system state required before test>
# not_in_scope:                                                  ← optional; inherited by all ACs
#   - <item excluded from this US>
#
# acceptance_criteria:
#
#   AC:US-<n>-01 (v<version> - <State>)
#     - <description of the AC>
#     - Aspect: <value1>, <value2>        ← optional; default keyword — no {placeholder} needed in AC text
#     preconditions:                      ← optional; extends feature-level preconditions for this AC only
#       - <AC-specific precondition>
#     not_in_scope:                       ← optional; extends feature-level not_in_scope for this AC only
#       - <AC-specific exclusion>
#
#   AC:US-<n>-02 (v<version> - <State>)
#     - <description of the AC with optional {placeholder-name} for parameterised variants>
#     - <placeholder-name>: <value1>, <value2>  ← optional; custom keyword — matches {placeholder-name} in AC text; ALL values must be covered
# =============================================================================
```

@US_ID:US-<n>
Feature: <US Title>
  As a <actor>, I can <capability>, so that <business outcome>.

  Background:                              ← optional
    Given <shared precondition>

  # AC:US-<n>-01 (v<version> - <State>) — <AC description>
  @AC:US-<n>-01
  Scenario: <scenario title>             ← single scenario = full AC coverage (no aspect split)
    ...

  # — when Aspect values are declared and need individual scenarios:
  @AC:US-<n>-01/aspect:<value1>
  Scenario: <scenario title for value1 branch>
    ...

  # — when a custom {placeholder-name} keyword is used (both US and Func):
  @AC:US-<n>-02/<placeholder-name>:<value1>
  Scenario: <scenario title for value1>
    ...

  @AC:US-<n>-02/<placeholder-name>:<value2>
  Scenario: <scenario title for value2>
    ...
```

**Header fields:**

| Field | Required | Purpose |
|---|---|---|
| `# source:` | Optional | Link to the original issue tracker entry or the pre-BDD living doc location |
| `# status:` | Yes | `planned` · `in_review` · `active` · `deprecated` (lowercase with underscores per profile `ac_states`) |
| `# business_value:` | Yes | Why this User Story exists (bullets) |
| `# preconditions:` | Optional | System-level state required before test execution; inherited and extended by all ACs |
| `# not_in_scope:` | Optional | Explicit exclusions at US level; inherited and extended by all ACs |
| `# acceptance_criteria:` | Yes | Full AC listing with IDs, versions, and states; each AC may extend inherited preconditions and not_in_scope |
| `@US_ID:US-<n>` tag | Yes | Machine-parseable User Story ID (feature-level tag) |

---

## Functionality Feature File Header

Header comment block at the top of every Functionality feature file —
`<feature_dirs.functionality>/func-<nnn>-<kebab>.feature` (default `features/liv_doc_func/`).

```gherkin
# =============================================================================
# LIVING DOC — FUNC-<nnn> · <Feature Name> — <Functionality Name>
# =============================================================================
# source:    https://github.com/<org>/<repo>/issues/<n>          ← optional
# status:    planned | in_review | active | deprecated
# parent:    FEAT-<nnn>
# func_type: component_state | component_action | button_action |
#            field_validation | calculation | visibility | navigation_rule
# rationale:                                                     ← optional
#   - <why this FUNC is scoped this way — business or design decision context>
# preconditions:                                                 ← optional; inherited by all ACs
#   - <system state required before test>
# not_in_scope:                                                  ← optional; inherited by all ACs
#   - <exclusion>
#
# acceptance_criteria:
#
#   AC:FUNC-<nnn>-01 (v<version> - <State>)
#     - <description in business language — no data-cy IDs in AC text>
#     - Aspect: <value1>, <value2>        ← optional; default keyword — no {placeholder} needed
#     preconditions:                      ← optional; extends feature-level preconditions for this AC only
#       - <AC-specific precondition>
#     not_in_scope:                       ← optional; extends feature-level not_in_scope for this AC only
#       - <AC-specific exclusion>
#
#   AC:FUNC-<nnn>-02 (v<version> - <State>)
#     - <description — may contain a {placeholder-name} for parameterised variants>
#     - <placeholder-name>: <value1>, <value2>  ← optional; custom keyword — matches {placeholder-name} in AC text; ALL values must be covered
# =============================================================================
```

@FUNC_ID:FUNC-<nnn>
Feature: <Feature Name> — <Functionality Name>
  <Purpose: one-to-two sentences describing what this FUNC covers, in business
  language. Present only when purpose adds context beyond the title.>   ← optional

  # No scenarios yet — uncovered ACs flagged by coverage_report.py.
  # When adding scenarios: include # AC:<id> comment and @AC:<id> or @AC:<id>/<placeholder-name>:<value> tag above each Scenario.
  # ACs with a {placeholder-name}: one scenario per declared value is required — partial coverage is a gap.
```

**Header fields:**

| Field | Required | Purpose |
|---|---|---|
| `# source:` | Optional | Link to the original issue tracker entry or the pre-BDD living doc location |
| `# status:` | Yes | `planned` · `in_review` · `active` · `deprecated` (lowercase with underscores per profile `ac_states`) |
| `# parent:` | Yes | Parent Feature ID (`FEAT-<nnn>`) |
| `# func_type:` | Yes | Category of behavior this Functionality represents (see table below) |
| `# rationale:` | Optional | **Why** this FUNC is scoped the way it is — business context, a deliberate design decision, or a constraint that explains the boundary. Not for implementation notes. |
| `# preconditions:` | Optional | System-level state required before test execution; inherited and extended by all ACs |
| `# not_in_scope:` | Optional | Explicit exclusions at FUNC level; inherited and extended by all ACs |
| `# acceptance_criteria:` | Yes | Full AC listing in business language — do not include `data-cy` IDs or implementation names in AC text; each AC may extend inherited preconditions and not_in_scope |
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

## seed.yaml (Business Seed)

`seed.yaml` lives at `<paths.bdd_artifacts>/seed.yaml` (default `.copilot/bdd/seed.yaml`). It is the
durable, human-curated input to every scan session: app entry point, business domains → routes,
known entities for parameterised routes, test-user roles, and pre-declared form values. **Re-read it
in full at the start of every scan session.** The agent appends to it as it discovers entities.

```yaml
# .copilot/bdd/seed.yaml
# Business Seed — last verified <date> (app <version>)

app:
  name: <App Name>
  base_url: https://<host>
  auth_entry_path: /auth/dashboard        # landing route after auth

credentials_source: <path/to/.env>        # file holding TEST_USERID / TEST_PASSWORD etc.

test_id_attribute: data-cy                # mirrors the Project Profile value

business_domains:                         # business surface → route → Feature entity
  - name: Authentication
    route_prefix: /login
    feature_id: FEAT-001
  - name: Create Domain Wizard
    route_prefix: /auth/all-domains/create-domain/about
    feature_id: FEAT-006
  - name: Edit Domain
    route_prefix: /auth/all-domains/{domainId}/{version}/edit-domain
    feature_id: FEAT-UNKNOWN              # no Feature yet — flagged for living-doc-create-feature
    note: "RE-SCAN [<date>]. Reuses the shared stepper in edit mode."

user_roles:
  - role: standard_user
    description: Default E2E test user — covers most flows
    note: Items that do not navigate for this role

# known_entities — real entity IDs observed during scans. Copyable values for
# parameterised routes ({domainId}/{version}) and form fields. Never store prod IDs.
known_entities:
  domains:
    - id: <uuid>
      version: 1
      name: "E2E Domain ..."
      status: Draft
      owner: <test-user>
      note: "Primary owned domain for the test user."
      next_scan_targets:                  # optional: queued sub-routes/tabs to scan next
        - tab: Version management
          url: /auth/all-domains/<uuid>/1/about
          action: "Click 'Version management' tab — scan for data-cy elements."
      data_feeds:                         # optional nested entities
        - id: <uuid>
          version: 1
          name: "test csv"

# form_fixtures — pre-declared field values for form/wizard traversal, keyed by route path.
# The agent reads these before falling back to the sourcing cascade.
form_fixtures:
  /auth/all-domains/create-domain/about:
    - field: domain-name
      value: "E2E Test Domain"
      source: seed_declared               # seed_declared | user_provided | agent_observed
      note: "Append a timestamp suffix at runtime to avoid duplicate rejection."
    - field: cost-center
      value: "SA345678"
      source: seed_declared
      note: "HEALED [<date>] — format must be 2 alpha + 6 digits per component validator."
```

**Top-level keys:**

| Key | Required | Purpose |
|---|---|---|
| `app` | Yes | `name`, `base_url`, `auth_entry_path` |
| `credentials_source` | Yes | Path to the env file holding test credentials — **never inline literals** |
| `test_id_attribute` | Yes | Mirrors the Project Profile (`data-cy` by default) |
| `business_domains[]` | Yes | `name`, `route_prefix`, `feature_id` (+ optional `note`). Use `FEAT-UNKNOWN` when no Feature entity exists yet |
| `user_roles[]` | Yes | `role`, `description` (+ optional `note`) |
| `known_entities` | No | Real IDs harvested during scans for parameterised routes; `domains[]` with `id/version/name/status/owner/note`, optional `next_scan_targets[]` and nested `data_feeds[]` |
| `form_fixtures` | No | Map of `route → [ {field, value, source, note?} ]`. `source`: `seed_declared` \| `user_provided` \| `agent_observed` |

**Credential rule:** credentials are referenced via `credentials_source` (an env file) or `env:VAR_NAME`
placeholders. A literal credential value anywhere in `seed.yaml` is a **security violation** — refuse to
proceed until it is replaced.

### form_fixtures sourcing cascade (how the agent resolves a field value)

1. **`seed.yaml form_fixtures`** — pre-declared (`source: seed_declared`) or written in a prior session (`agent_observed`).
2. **Existing app entities** — navigate to the entity list; read a real field value; copy it, or derive (e.g. append a suffix to avoid duplicate rejection).
3. **Field context inference** — read label + placeholder + tooltip → infer a plausible value (`"Domain name"` → `"E2E Test Domain"`, `email` → `"test@example.com"`).
4. **User-assist pause** — for a value that must exist in the real environment and none of the above suffices → show the user the form, request the value, record it back with `source: user_provided`.

> **Optional advanced fields.** For complex forms a fixture entry may also carry `value_class`
> (`copyable` / `derived` / `fake` / `real-world`), a `values[]` array of labelled traversal branches
> (each `{label, value, source}`, `label: default` = happy path), or a `condition`
> (`{when_field, when_value}`) that gates the fill. These are optional extensions to the base
> `{field, value, source}` shape — omit them unless the form requires branch exploration or conditional fields.

### Input validation probing

After a successful form fill and submission, probe each text input and scan the form after each probe
to capture error `data-cy` elements visible only in the invalid state:

| Probe | Input | What to observe |
|---|---|---|
| Special characters | `<>'"&\` | Inline error, silent strip, or truncation |
| Oversized input | 200+ characters | Character counter, truncation, or rejection message |
| Wrong type | Text in a numeric/date field | Inline validation message or rejection |
| Duplicate detection | A known existing entity name | Duplicate-rejected error and its `data-cy` |

Findings become source material for `field_validation` Functionality stubs and are recorded in the
manifest route's optional `field_constraints[]` (see Manifest schema below).

---

## manifest.json (Exploration Manifest)

`manifest.json` lives at `<paths.bdd_artifacts>/manifest.json` (default `.copilot/bdd/manifest.json`).
It is the machine record of every scanned surface. The manifest is a JSON object; **`routes` is a JSON array** of route objects
(profile `manifest_shape: object`). Load targeted entries by route during a session; load the full file
only for a RE-SCAN.

The manifest uses **normalized test_id keys** (not attribute-specific). The root-level `test_id_attribute` metadata
tells downstream generators (PageObject, data-cy-instrument) how to map these normalized keys to the actual HTML attribute.

```json
{
  "generated": "2026-06-08T12:00:00Z",
  "scan_version": "v1.9.2-36-g6660993",
  "test_id_attribute": "data-cy",
  "routes": [
    {
      "url": "/login",
      "title": "App - Login",
      "pageobject_path": "playwright/pages/LoginPage.ts",
      "feature_id": "FEAT-001",
      "last_scanned": "2026-05-28T13:32:00Z",
      "note": "Optional scan provenance.",
      "elements": [
        { "test_id": "input-username", "tag": "cps-input",  "label": "Username" },
        { "test_id": "btn-login",      "tag": "cps-button", "label": "Login", "note": "NEW [scan: ...]" }
      ],
      "coverage_gaps": [
        { "tag": "button", "ariaLabel": "Collapse sidebar", "suggested_test_id": "btn-collapse-sidebar", "note": "no test-id" }
      ],
      "open_actions_menu": {
        "owned_domain": ["View data feeds", "Grant access", "Edit domain"],
        "note": "Optional — menu contents per context."
      },
      "navigation_context": "Default landing page after login.",
      "field_constraints": [
        { "field": "domain-name", "max_length": 100, "special_chars": "rejected", "duplicate": "rejected-with-error", "duplicate_error_test_id": "domain-name-duplicate-error" }
      ]
    }
  ]
}
```

**Route object fields:**

| Field | Required | Purpose |
|---|---|---|
| `url` | Yes | Route path; use `{param}` for dynamic segments. `modal:<host-route>` for dialog-only surfaces |
| `title` | Yes | Document/page title at scan time |
| `pageobject_path` | Yes | Repo-relative path to the PageObject file |
| `feature_id` | Yes | Living-doc Feature ID, or `FEAT-UNKNOWN` |
| `last_scanned` | Yes | ISO 8601 timestamp; surfaces stale entries |
| `elements[]` | Yes | Discovered test-id elements: `{ "test_id": <id>, "tag": <html-tag>, "label": <text\|null>, "note"?: <scan note> }`. `test_id` is normalized and maps to root `test_id_attribute` downstream. |
| `coverage_gaps[]` | Yes | Interactive elements lacking a test-id: `{ "tag", "text"\|"ariaLabel"\|"role"\|"type", "suggested_test_id", "note"? }`. Empty array = fully instrumented. `suggested_test_id` is normalized. |
| `navigation_context` | Yes | **String** — how to reach the route (prose). Reused across sessions |
| `note` | No | Scan provenance for the route as a whole |
| `open_actions_menu` | No | Context-menu contents keyed by context (e.g. owned vs non-owned) |
| `field_constraints[]` | No | Per-field validation findings: `{ field, max_length?, special_chars?, duplicate?, duplicate_error_test_id?, allowed_format?, real_world_required? }` |

> **Normalized test_id keys:** The manifest uses `test_id` (not `data-cy`) and `suggested_test_id` (not `suggestedDataCy`)
> as fixed, attribute-agnostic keys. The root-level `test_id_attribute` (mirrors Project Profile) tells downstream
> generators what HTML attribute these keys map to (e.g., `data-cy`, `data-testid`, or a custom attribute).
> PageObject generators read this metadata and emit the correct attribute; the manifest shape remains consistent
> regardless of the configured attribute.

### Lifecycle

| Event | What happens |
|---|---|
| First form encountered | Agent applies the sourcing cascade; fills the form; probes validation |
| `real-world` value missing | User-assist pause → value saved to `form_fixtures` with `source: user_provided` |
| Validation probe finds a new `data-cy` | Added to the route `elements[]`; flagged as a `field_validation` Functionality candidate |
| Next scan session | Agent reads `form_fixtures`; skips the cascade for pre-declared fields |
| Constraint changes (e.g. max length) | Agent updates `field_constraints`; flags the change in `breaking-changes.md` |
| Element missing on re-scan | Flag `BREAKING CHANGE`; never auto-delete the locator |
