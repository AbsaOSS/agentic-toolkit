# Data-Cy Instrument Skill

The `data-cy-instrument` skill resolves missing `data-cy` (or `data-testid`) attributes in templates. It audits coverage gaps, adds test IDs, syncs PageObjects to use `getByTestId()`, and promotes Functionalities when gaps close.

---

## What it does

The skill updates templates and PageObjects:

| Output | Description |
|--------|-------------|
| **Gap audit** | Find all elements missing test IDs |
| **Template instrumentation** | Add `data-cy`/`data-testid` attributes |
| **PageObject sync** | Update selectors to `getByTestId()` |
| **Functionality promotion** | Mark Functionalities `active` once test IDs exist |

---

## When to trigger it

```
add missing data-cy
instrument templates
fix data-cy gaps
add test IDs to templates
data-cy audit
missing test ids
fix playwright selectors
coverage gaps
```

---

## Supported frameworks

| Framework | Test ID | Scope |
|-----------|---------|-------|
| **Angular** | `data-cy` | Full: template + host binding |
| **React** | `data-testid` | Template + PageObject sync |
| **Vue** | `data-test` | Template + PageObject sync |

---

## Related skills

- [Living Doc PageObject Scan](./living-doc-pageobject-scan.md) — discover missing test IDs
- [Living Doc Scenario Creator](./living-doc-scenario-creator.md) — write scenarios once test IDs exist
- [Living Doc Create Functionality](./living-doc-create-functionality.md) — define behaviors
- [Living Doc Update](./living-doc-update.md) — promote Functionalities to `active`
- [Gherkin Step Definitions](./gherkin-step.md) — use `getByTestId()` in steps

---

## Testing Evals

This skill has been validated with **11 test cases** covering:
- Gap audit workflows
- Angular/React/Vue template instrumentation
- PageObject selector updates
- Functionality promotion scenarios


