# Living Documentation — Shared Glossary

> **This file has moved.**
> The shared glossary is now at [skills/references/living-doc-glossary.md](https://github.com/AbsaOSS/agentic-toolkit/blob/master/skills/references/living-doc-glossary.md).
> Update any links pointing here to use the new path.


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
- Owns: end-to-end **Acceptance Criteria (AC)** written in Given-When-Then format
- Links to: one or more **Features** (system surfaces the User Story touches)
- Status: `draft | ready | in-progress | done | deprecated`

### Feature

A named system surface — the structural layer between User Stories and atomic behaviors.

- ID format: `FEAT-<kebab-name>` (e.g. `FEAT-checkout`)
- Surface types: `UI | API | Service | Module`
- Owns: one or more **Functionalities**
- Linked to: one or more **User Stories**
- Status: `active | candidate | deprecated`
- Registry: all Features are listed in `docs/FEATURE_REGISTRY.md`

**One PageObject ≈ one Feature** for UI surfaces.

### Functionality (FUNC)

An atomic, fast-testable behavior — a single verb phrase describing one responsibility.

- ID format: `FUNC-<kebab-name>` (e.g. `FUNC-apply-discount`)
- Belongs to: one parent **Feature**
- Owns: **Functionality-level Acceptance Criteria** (When/Then format, unit/integration-testable)
- Test type per AC: `unit | integration`
- Priority per AC: `critical | high | medium | low`

Functionalities differ from User Story ACs: they are atomic and fast-testable (unit/integration),
not end-to-end. A single User Story may trigger multiple Functionalities.

### Acceptance Criterion (AC)

A binary pass/fail statement that defines a verifiable condition.

**User Story AC format (end-to-end):**
```
Given: <pre-condition and system state>
When:  <action the user takes>
Then:  <observable outcome the user sees>
```

**Functionality AC format (atomic/fast):**
```
When: <input condition or system state>
Then: <output, return value, or side effect>
```

Each AC has:
- A unique ID: `<parent-id>-AC-<n>` (e.g. `US-001-AC-1`, `FUNC-apply-discount-AC-2`)
- A `priority`: `critical | high | medium | low`
- A `test_type` (Functionality ACs only): `unit | integration`

### PageObject

A class that encapsulates the selectors and actions of a single UI screen. Used by BDD step
definitions to interact with the application without embedding selectors in step code.

- Naming: `<ScreenName>Page` (e.g. `CheckoutPage`)
- One PageObject per distinct screen or significant modal
- Selector preference: `data-testid` > `aria-label`/role > CSS class (last resort)

---

## Relationship diagram

```
User Story (US)
  └── triggers / links to → Feature (FEAT)
                                └── owns → Functionality (FUNC)
                                                └── owns → Functionality ACs
                                                └── maps to → unit/integration tests
  └── owns → User Story ACs (Given/When/Then)
                  └── maps to → BDD Scenarios (.feature files)
                                    └── implemented by → Step Definitions
                                                            └── delegates to → PageObjects
```

---

## Living doc catalog

The **living doc catalog** is the collection of all canonical entity JSON files in the project.
Typically stored under `docs/living-doc/` or equivalent. Gap finder, scenario creator, and
tutorial creator all read from this catalog.

---

## What each skill creates or consumes

| Skill | Creates | Reads |
|---|---|---|
| `living-doc-create-user-story` | User Story JSON | Feature Registry |
| `living-doc-create-feature` | Feature JSON + FEATURE_REGISTRY.md entry | User Story list |
| `living-doc-create-functionality` | Functionality JSON | Feature JSON |
| `living-doc-pageobject-scan` | PageObject classes + Feature stubs | App URL or test suite |
| `living-doc-scenario-creator` | .feature files | User Story, PageObjects |
| `living-doc-tutorial-creator` | Tutorial markdown | .feature files, User Stories |
| `living-doc-gap-finder` | Gap report | All of the above |
