# BDD Maintain Skill

The `bdd-maintain` skill removes deprecated BDD artifacts (feature files, step definitions, PageObjects) and audits your test suite for dead code. It works downstream of [Living Doc Update](./living-doc-update.md) after you deprecate an entity.

---

## What it does

The skill identifies and removes or reports on artifacts:

| Task | Output |
|------|--------|
| **REMOVE** | Safely delete all files linked to a deprecated entity |
| **DEAD CODE AUDIT** | Find unused steps, PageObject methods, unused PageObject classes |

---

## When to trigger it

```
remove feature files
delete feature after deprecation
find unused steps
dead code audit
cleanup page objects
unused steps
dead pageobject methods
unused po methods
dead po components
```

---

## Helper scripts

Three Python utilities available in `skills/bdd-maintain/scripts/`:
- **find_unused_steps.py** — audit step definitions with no matching scenarios
- **find_unused_po_methods.py** — identify PageObject methods never called by steps
- **find_unused_po_components.py** — report PageObject classes never instantiated

---

## Related skills

- [Living Doc Update](./living-doc-update.md) — deprecate the entity first
- [Gherkin ↔ Living Doc Sync](./gherkin-living-doc-sync.md) — tag scenarios `@deprecated` before removal
- [Living Doc PageObject Scan](./living-doc-pageobject-scan.md) — maintain PageObjects

---

## Testing Evals

This skill has been validated with **10 test cases** covering:
- REMOVE mode: deprecated entity cleanup
- DEAD CODE AUDIT mode: unused artifact detection
- File deletion verification
- Traceability validation


