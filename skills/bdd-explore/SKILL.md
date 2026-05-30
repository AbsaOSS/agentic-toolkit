---
name: bdd-explore
description: >
  Business Seed assembly, iterative UI crawl, PageObject generation, and guided traversal
  for the @living-doc-bdd-copilot agent. Activate for any webapp exploration or first-time
  scan session. Covers seed.yaml assembly (Sources A–E), MCP Playwright crawl loop, entity
  harvesting, ExplorationFixture sourcing cascade, custom component interaction rules,
  parameterised route resolution, Source E guided traversal, and manifest.json output.
  Triggers on: "scan webapp", "crawl UI", "explore the app", "discover routes",
  "business seed", "seed.yaml", "manifest.json", "build pageobjects", "first scan",
  "assemble seed", "guided traversal", "explore routes", "bdd explore".
  Does NOT trigger for: standalone PageObject generation from a pre-built manifest without a
  live webapp crawl (use living-doc-pageobject-scan); BDD maintenance after UI changes or
  test failures (use bdd-maintain).
license: Apache-2.0
compatibility: GitHub Copilot
---

# BDD Explore — Business Seed Assembly & Iterative Crawl

> **Glossary:** Feature, Functionality, User Story — see [living-doc-glossary](../references/living-doc-glossary.md) ([remote](https://github.com/AbsaOSS/agentic-toolkit/blob/master/skills/references/living-doc-glossary.md)).
> **BDD schemas:** ExplorationFixture taxonomy, seed.yaml schema, manifest field_constraints — see [living-doc-bdd-schemas](../references/living-doc-bdd-schemas.md) ([remote](https://github.com/AbsaOSS/agentic-toolkit/blob/master/skills/references/living-doc-bdd-schemas.md)).

---

## Business Seed Assembly

Before crawling, assemble the Business Seed file at `.copilot/bdd/seed.yaml`.

Sources A–E — collect from whichever are available:

| Source | Behaviour |
|---|---|
| **A — Living documentation** | Extract Feature names, US titles, and AC texts. Map each Feature to its primary URL/route if known. |
| **B — Sitemap or route config** | Parse route definitions (Angular router, React Router, `sitemap.xml`) to enumerate URL paths. |
| **C — OpenAPI / Swagger spec** | Extract endpoint paths; map REST resources to UI screens where obvious. |
| **D — Existing PageObjects** | Load current `.copilot/bdd/manifest.json` if present — treat known surfaces as already discovered. |
| **E — Guided traversal** | See Source E protocol below. |

**Credential safety rule:** Never store literal credentials in `seed.yaml`. Always use `env:VAR_NAME` as the value, e.g.:

```yaml
credentials:
  username: env:BDD_USERNAME
  password: env:BDD_PASSWORD
```

**Artifact location:** BDD artifacts can live anywhere in the repository. On session start, discover them:

1. Search for `seed.yaml` containing a `base_url:` key.
2. Search for `manifest.json` containing an array with `pageobject_path` entries.
3. If found, load both files and record their paths for this session.
4. If NOT found, create them at a sensible location (e.g. alongside the existing living documentation directory if one exists, otherwise `.copilot/bdd/`).
5. **On first discovery:** propose adding their locations to `.github/copilot-instructions.md` so every future agent session can load them without searching:

```markdown
## BDD Artifacts
- **Business Seed:** `<relative-path>/seed.yaml` — webapp routes, credentials (env refs), guided traversal steps
- **Exploration Manifest:** `<relative-path>/manifest.json` — discovered UI surfaces, component IDs, PageObject paths
```

Committing both files means every subsequent session resumes from the last known state — no re-crawl required.

**Output artifact:** `seed.yaml` (path discovered or chosen above)

```yaml
base_url: https://...
credentials:
  username: env:BDD_USERNAME
  password: env:BDD_PASSWORD
known_routes:
  - path: /login
    feature: Authentication
  - path: /dashboard
    feature: Dashboard
guided_steps: []    # populated during Source E traversal
form_fixtures: {}   # keyed by route path; populated during form traversal (ExplorationFixture schema)
```

---

## Iterative Exploration

**On session start:** Load `seed.yaml`. If `.copilot/bdd/manifest.json` is present, load it — treat all listed surfaces as already discovered and resume from there. If manifest is absent, treat this as the first run (clean slate).

**Partial state rule:** `seed.yaml` present but `manifest.json` absent = first exploration run. Begin crawl from `base_url`; do not assume any surfaces have been discovered.

**Crawl loop:**

1. Navigate to each known route from `seed.yaml` using MCP Playwright.
2. Snapshot the page; identify interactive elements, forms, navigation links, and significant UI surfaces.
3. Follow links and expand navigation to discover new routes not in the manifest.
4. For each new surface discovered: add an entry to `manifest.json` (Feature name, URL, component IDs, PageObject path).
5. Repeat until coverage plateau — no new surfaces found in the last full iteration.
5a. **Entity harvesting** — whenever a domain ID, version, feed ID, or other parameterised entity is read from the DOM (URLs, card text, table rows), record it under `known_entities` in `seed.yaml` if not already present. Fields: `id`, `version`, `name`, `status`, `owner`, `note`. These values feed the sourcing cascade for parameterised routes in subsequent sessions.
6. For each form, wizard, or dialog on a visited page, attempt to fill and progress using the **ExplorationFixture sourcing cascade** (see [living-doc-bdd-schemas](../references/living-doc-bdd-schemas.md#explorationfixture)): (1) pre-declared values in `seed.yaml form_fixtures` — use the `default`-labelled value for the happy path and explore alternate `values[]` branches to reach different form sections or sub-routes; (2) values read from an existing entity in the app — copy verbatim (`copyable`) or append a suffix to avoid duplicate rejection (`derived`); (3) inferred `fake` values from label + placeholder + tooltip text; (4) user-assist pause for `real-world` fields with no resolvable value. Skip `condition`-gated fields until the controlling field holds the required value. After a successful submission, probe each text input for: special characters (`<>'"&\`), oversized input (200+ chars), wrong type, and duplicate values — run the core scan after each probe to capture `data-cy` validation elements visible only in error state. Record findings as `field_constraints` in the manifest `navigation_context`. Report any still-unreachable flows (auth walls, CAPTCHA, deep data dependencies) and offer to enrich `seed.yaml`. **Dismiss rule — after scanning any modal dialog or overlay, always close it (Cancel button → × close button → Escape key, in that order) before navigating to the next route or triggering the next action. Never leave a dialog open while scanning a subsequent page.**

**Component interaction rules — use these instead of `fill()` for custom components:**

| Component | Correct interaction |
|---|---|
| `cps-radio-group` | `browser_click` the inner `<label>` or `<span>` whose text matches the desired option. Do NOT use `fill()`. |
| `cps-select` | `browser_click` the component to open the dropdown portal, then `browser_click` the matching `<li>` option by text. |
| `cps-autocomplete` | Type into the inner `<input>` using `browser_type`, wait for the dropdown to appear, then `browser_click` the matching option. |
| `cps-switch` / `cps-checkbox` | `browser_click` the component wrapper. |
| `app-text-editor` (rich text) | `browser_click` the `contenteditable` child, then `browser_type` the value. |
| `cps-button` | `browser_click` the inner `<button>` (e.g. via `evaluate`: `el.querySelector('button').click()`). |
| `input[type=file]` | Use `mcp_browser_file_upload` or `page.setInputFiles()` with a fixture file path from `seed.yaml form_fixtures`. |

After interacting with a required field (especially `cps-radio-group`), re-check whether a gated button (e.g. Continue, Save) has become enabled before proceeding.

**Parameterised route resolution — use `known_entities` before prompting the user:**

Before navigating to any parameterised route (e.g. `/auth/all-domains/{domainId}/{version}/...`), first check `seed.yaml known_entities` for a matching entity with `owner` equal to the current test user. Substitute the `id` and `version` values directly. Only fall back to the user-assist pause if no matching entity exists.

For domain detail tab scans (Schema, Run history, Access, Version management): always navigate using the first `known_entities` domain owned by the current test user, then click each tab in turn and run the core scan. These tabs are reachable by tab click alone — no additional data state is required to open them.

**PageObject generation rule:** For every new or changed UI surface, load `living-doc-pageobject-scan` — `Create` mode for first-time generation and `Maintain` mode for selector drift. Generated PageObjects must use a file-level `living-doc: FEAT-<nnn> | /route` header comment, prefer `data-testid` selectors, keep selector constants in `ALL_CAPS`, accept `page` in `__init__` / `constructor`, and expose method stubs for each interactive element. Flag any positional CSS selector as `FRAGILE`. If no matching Feature exists in the living documentation, hand the surface to `@living-doc-copilot`; do not create entities here.

**Output artifact:** `.copilot/bdd/manifest.json`

The manifest records per-route exploration state. Schema matches the `living-doc-pageobject-scan` skill definition:

```json
{
  "version": "1.0",
  "routes": {
    "/login": {
      "pageobject_path": "aul-ui/playwright/pages/LoginPage.ts",
      "feature_id": "FEAT-001",
      "last_scanned": "2026-05-26T10:30:00Z",
      "elements": [
        { "data_cy": "username-input", "tag": "input" },
        { "data_cy": "password-input", "tag": "input" },
        { "data_cy": "login-btn", "tag": "cps-button" }
      ],
      "coverage_gaps": [],
      "navigation_context": {
        "prerequisites": null,
        "navigation_steps": "Navigate directly to /login.",
        "data_requirements": null,
        "auth_role": "unauthenticated",
        "notes": null,
        "field_constraints": []
      }
    }
  }
}
```

---

## Source E — Guided Traversal Protocol

Use when automated crawling cannot proceed — unknown decision points, multi-step wizards, auth flows, role-gated screens, or forms blocked by missing business knowledge (required field values, valid lookup codes, business-specific input formats).

**Protocol:**

1. Take a screenshot; show the user what the agent sees.
2. Ask: *"I've reached a decision point at [URL]. What should I do next? (e.g. click X, fill field Y with Z, log in as role R, provide the valid value for field F)"*
3. Wait for the user's answer. Execute the described action via MCP Playwright.
4. Immediately append to `guided_steps:` in `seed.yaml`:

```yaml
guided_steps:
  - url: /checkout/payment
    action: fill
    field: card-number
    value: env:TEST_CARD_NUMBER
    note: "Test Visa card for payment flow"
```

5. Continue crawl from the new state.

**CAPTCHA rule:** If a CAPTCHA is encountered, pause and ask the user to solve it manually in the browser. Do not attempt automated bypass. Once the user confirms it is solved, continue and record the step with `action: captcha_solved`.
