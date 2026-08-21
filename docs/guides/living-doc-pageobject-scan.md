# Living Doc PageObject Scan Skill

The `living-doc-pageobject-scan` skill discovers your webapp's UI surfaces, generates Playwright PageObject classes, and heals selector drift in failing tests.

---

## What it does

The skill produces PageObject classes and a manifest:

| Output | When |
|--------|------|
| **PageObject classes** | One per screen/page, with element selectors and action methods |
| **manifest.json** | Inventory of routes, linked Features, element status |
| **Selector fixes** | Ranked by reliability: `getByTestId()` → `getByRole()` → CSS |
| **Reports** | Missing `data-cy` attributes, elements requiring manual fixes |

---

## When to trigger it

```
scan this webapp
generate page objects
crawl the UI
first scan
bootstrap pageobjects
re-scan
refresh manifest
heal failing tests
failing tests
selector drift
test failures
```

---

## Three scopes

| Scope | Time | When |
|-------|------|------|
| **CREATE** | 30–45 min | First scan; bootstrap all PageObjects |
| **RE-SCAN** | 20–30 min | UI changed; new Feature shipped |
| **HEALING** | 10–15 min | Tests failing; fix broken selectors only |

---

## Related skills

- [Data-Cy Instrument](./data-cy-instrument.md) — add missing test IDs to templates
- [Living Doc Create Feature](./living-doc-create-feature.md) — document discovered surfaces
- [Living Doc Scenario Creator](./living-doc-scenario-creator.md) — create scenarios using PageObjects
- [Gherkin Step Definitions](./gherkin-step.md) — wire PageObjects into step code
- [BDD Maintain](./bdd-maintain.md) — clean up PageObjects after features are deprecated

---

## Helper scripts

Two Python utilities available in `skills/living-doc-pageobject-scan/scripts/`:
- **manifest_diff.py** — compare before/after manifests to track route and element changes
- **validate_artifacts.py** — verify PageObject classes and manifest schema compliance

---

## Testing Evals

This skill has been validated with **15 test cases** covering:
- CREATE mode: bootstrap PageObjects from scratch
- RE-SCAN mode: refresh manifest after UI changes
- HEALING mode: fix selector drift in failing tests
- Element harvesting and selector ranking