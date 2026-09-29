# Living Doc Create Feature Skill

The `living-doc-create-feature` skill helps you document a system surface (UI screen or API endpoint, including a backend service's public contract) as a Feature entity. It establishes ownership, enables impact analysis, and links User Stories to the surfaces they exercise.

---

## What it does

The skill produces a Feature entity:

| Output | Description |
|--------|-------------|
| **Feature definition** | Type, description, ownership |
| **Functionalities** | List of atomic behaviors in this Feature |
| **Dependencies** | External services, databases, APIs it depends on |
| **User Story links** | Which User Stories exercise this Feature |

---

## When to trigger it

```
document a new feature
create a feature entity
document a new screen
document an API endpoint
new service documentation
what feature owns this behavior?
feature ownership
feature dependencies
```

---

## Feature types

Only two surface types exist — each requires the matching test abstraction to actually exist for this surface:

| Type | Example | Eventual test-abstraction anchor |
|------|---------|------------------|
| **UI** | Login, Dashboard, Checkout | A PageObject for the screen (create together with the Feature if it doesn't exist yet, e.g. via `living-doc-pageobject-scan`) |
| **API** | POST /orders, GET /users/:id, including a backend service's public contract (REST/GraphQL or an annotated message-broker contract) | An annotated endpoint method, or an annotated event handler |

A worker, module, or service with neither anchor achievable is not a Feature yet — record it as an `external_dependencies` entry on the Feature(s) that interact with it. See [living-doc-glossary](../../skills/shared/references/living-doc-glossary.md) for details.

---

## Related skills

- [Living Doc Create User Story](./living-doc-create-user-story.md) — create User Stories for this Feature
- [Living Doc Create Functionality](./living-doc-create-functionality.md) — define behaviors in this Feature
- [Living Doc Update](./living-doc-update.md) — edit Feature ownership or dependencies
- [Living Doc PageObject Scan](./living-doc-pageobject-scan.md) — discover UI Features

---

## Helper scripts

One Python utility available in `skills/living-doc-create-feature/scripts/`:
- **next_id.py** — generate sequential Feature entity IDs (FEAT-XXX)

---

## Testing Evals

This skill has been validated with **17 test cases** covering:
- Feature entity creation
- Feature types (UI, API)
- Ownership and dependency tracking
- Feature Registry integration
- User Story linkage
