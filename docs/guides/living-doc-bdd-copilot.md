# Living Doc BDD Copilot Agent

`@living-doc-bdd-copilot` orchestrates living documentation and BDD automation tasks — catalog management (User Stories, Features, Functionalities, AC updates, impact analysis, gap finding) and automation (webapp exploration, PageObjects, Gherkin scenarios, step definitions, and BDD suite maintenance).

---

## What it does

| Task | When to use |
|---|---|
| Explore a web app | Crawl and map UI surfaces; discover Features from the live application |
| Generate PageObjects | Create or update PageObject classes from discovered UI surfaces |
| Generate Gherkin scenarios | Cover User Story ACs with `.feature` files and linked step definitions |
| Sync Gherkin with living doc | Ensure traceability tags in feature files match catalog ACs |
| Heal automation after UI changes | Fix broken selectors, step definitions, and PageObjects (failing tests only) |
| Re-scan after refactor | Full re-crawl of all manifest paths plus active discovery of new routes; update scenarios |
| Remove deprecated feature automation | Clean up `.feature` files, steps, and PageObjects for removed features |
| Generate tutorial documents | Transform executed BDD scenarios into annotated walkthrough documents |

---

## How to trigger it

```
scan webapp
generate pageobjects for the login screen
explore the app at https://...
generate scenarios for US-42
heal pageobjects
sync gherkin to living doc
crawl the UI
living doc bdd copilot
BDD pipeline
create page objects
generate feature file from user story
```

---

## Before you start — setup files

The agent uses two persistent files:

| File | Purpose |
|---|---|
| `seed.yaml` | Business Seed — base URL, credentials (env refs), known routes, guided traversal steps |
| `manifest.json` | Exploration Manifest — all discovered surfaces with Feature name, URL, component IDs, and PageObject path |

These files can live anywhere in the repository. On each session start, the agent searches for them automatically:

1. Searches for `seed.yaml` containing an `app:` object with a `base_url` key.
2. Searches for `manifest.json` containing an object with a `routes` array.
3. If found, loads both files and resumes from the last known state — no re-crawl needed.
4. If not found, creates them at a sensible location (alongside your existing living doc catalog directory, or `.copilot/bdd/` if no catalog is present).

**On first discovery**, the agent will propose adding the file paths to `.github/copilot-instructions.md` so every future session can load them without searching:

```markdown
## BDD Artifacts
- **Business Seed:** `<relative-path>/seed.yaml`
- **Exploration Manifest:** `<relative-path>/manifest.json`
```

**Credential safety:** Credentials in `seed.yaml` must always use `env:VAR_NAME` — never literal values.

```yaml
app:
  name: My Application
  base_url: https://your-app.example.com
  auth_entry_path: /login
credentials_source: env:BDD_CREDENTIALS  # or .env.test file path
test_id_attribute: data-cy
business_domains:
  - name: Authentication
    route_prefix: /auth
    feature_id: FEAT-001
  - name: Dashboard
    route_prefix: /dashboard
    feature_id: FEAT-002
user_roles:
  - role: Admin
    description: Full access to all features
  - role: User
    description: Standard user access
guided_steps: []  # populated during guided traversal
```

---

## Pipeline

### Business Seed assembly

Collects sources A–E to build `seed.yaml`:

| Source | What the agent collects |
|---|---|
| A — Living doc catalog | Feature names, US titles, AC texts, route mappings |
| B — Sitemap / route config | URL paths from Angular router, React Router, or `sitemap.xml` |
| C — OpenAPI / Swagger spec | REST endpoint paths, mapped to UI screens where obvious |
| D — Existing PageObjects | Already-discovered surfaces from a previous manifest run |
| E — Guided traversal | Steps recorded live as the agent pauses to ask the user at decision points |

### Iterative exploration

The agent navigates the live application via MCP Playwright, snapshots pages, identifies UI surfaces, and builds `manifest.json`. Exploration continues until a coverage plateau — no new surfaces in the last full iteration.

If the agent hits an auth wall, multi-step wizard, CAPTCHA, or a form it cannot progress due to missing business knowledge (unknown valid input values, required lookup codes, business-specific field formats):

- It takes a screenshot and describes what it sees.
- It asks you what to do next.
- CAPTCHA: it pauses and waits for you to solve it manually in the browser.
- All guided steps are recorded in `seed.yaml` under `guided_steps:` for future re-runs.

### Scenario generation

After exploration:

1. Uses `living-doc-gap-finder` (bottom-up mode) to find `ACTIVE` ACs with no linked Gherkin scenario.
2. Generates `.feature` files with `Given/When/Then` scenarios — one scenario per AC, each with a `# AC:` traceability tag.
3. For each new step, checks for an existing reusable definition: first narrows scope to the relevant PageObject, then confirms the step's purpose matches (not just its text pattern). Reuses if it matches; writes a new stub only if no match exists.
4. Extends the relevant PageObject with any new UI interactions required by the new stubs.

### Maintenance

| Mode | When | What the agent does |
|---|---|---|
| **RE-SCAN** | New feature shipped or UI refactored | Full re-crawl of every manifest path plus active discovery of new routes (links, buttons, tabs, wizard steps); updates manifest; generates new scenarios for new ACs |
| **HEALING** | Tests failing due to selector drift | Scoped to failing tests only — navigates affected pages; identifies updated selectors; repairs PageObjects and step bindings; re-runs only the previously failing tests to confirm |
| **REMOVE** | Feature deprecated or deleted | Identifies linked `.feature` files, steps, and PageObjects; confirms before deleting; loads `living-doc-update` to complete catalog deprecation |

---

## Shared skill — `living-doc-gap-finder`

`living-doc-gap-finder` is used in two directions within the same agent:

| Direction | What it finds |
|---|---|
| **Top-down** (catalog operations) | Missing documentation entities (Features, User Stories, Functionalities not yet in the catalog) |
| **Bottom-up** (automation operations) | ACs that exist in the catalog but have no linked Gherkin scenario |

---

## Skills used

| Skill | Purpose |
|---|---|
| `living-doc-pageobject-scan` | Discover, create, and maintain PageObject classes; Business Seed assembly and webapp crawl; RE-SCAN and HEALING for selector drift |
| `living-doc-scenario-creator` | Generate full Gherkin feature files (header + scenarios + step bodies) from ACs |
| `living-doc-gap-finder` | Find catalog gaps (top-down) and ACs with no linked scenario (bottom-up) |
| `gherkin-step` | Implement step definitions |
| `gherkin-living-doc-sync` | Sync feature files and scenarios with living doc traceability links |
| `data-cy-instrument` | Resolve missing `data-cy` attributes end-to-end |
| `bdd-maintain` | Clean up deprecated features; dead code audit (unused steps, PageObject methods, components) |

---

## Handoff

No cross-agent handoffs needed. This agent owns both catalog and automation layers.

For concerns outside this agent's scope:

| Concern | Owner |
|---|---|
| Unit and integration tests | Your project's existing test tooling / test owners (not provided by this toolkit) |
| CI quality gates and linting | Your project's CI pipeline (not provided by this toolkit) |

---

## Installation

```bash
npx skills add https://github.com/AbsaOSS/agentic-toolkit -g
```

See [Getting Started](../getting-started.md) for the full install guide.
