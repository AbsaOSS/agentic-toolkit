# Living Doc Gap Finder Skill

The `living-doc-gap-finder` skill audits your living documentation catalog for coverage gaps—undocumented features, orphan tests, untested acceptance criteria, and broken traceability links. It produces a prioritized gap report with remediation routing.

---

## What it does

The skill scans your catalog and reports gaps:

| Output | Description |
|--------|-------------|
| **Gap categories** | UNTESTED_AC, UNDOCUMENTED_SURFACE, ORPHAN_TEST, ORPHAN_FEATURE, STALE_REFERENCE, etc. |
| **Prioritization** | Ranks by business impact (critical flows first) |
| **Remediation routing** | Points to the right skill to fix each gap |
| **Coverage metrics** | Percentage of Features, Functionalities, ACs with scenarios |

---

## When to trigger it

```
find what's not documented
living doc gaps
orphan tests
untested AC
documentation coverage
gap report
what's not covered by scenarios
audit living doc
```

---

## Two modes

| Mode | When |
|------|------|
| **AUDIT** | Full inventory of what's missing; periodic review |
| **PLAN** | Bootstrap new coverage from UI surfaces (via PageObject scan) |

---

## Related skills

- [Living Doc Create Feature](./living-doc-create-feature.md) — document undiscovered surfaces
- [Living Doc Create Functionality](./living-doc-create-functionality.md) — define undocumented behaviors
- [Living Doc Scenario Creator](./living-doc-scenario-creator.md) — write scenarios for untested ACs
- [Living Doc PageObject Scan](./living-doc-pageobject-scan.md) — discover surfaces
- [Living Doc Update](./living-doc-update.md) — fix broken links and orphaned entities

---

## Helper scripts

One Python utility available in `skills/living-doc-gap-finder/scripts/`:
- **compute_gaps.py** — analyze catalog and compute missing coverage with prioritization

---

## Testing Evals

This skill has been validated with **16 test cases** covering:
- AUDIT mode: full gap inventory
- PLAN mode: bootstrap from UI surfaces
- Gap categorization and prioritization
- Remediation routing accuracy
- Coverage metrics computation
