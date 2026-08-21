# Living Doc Create User Story Skill

The `living-doc-create-user-story` skill helps you author User Stories with business-level Acceptance Criteria ready for E2E scenario generation. It guides narrative structure (As-a/I-can/so-that), AC definition, Feature linking, and status progression.

---

## What it does

The skill produces a complete User Story:

| Output | Description |
|--------|-------------|
| **Narrative** | As-a/I-can/so-that structure with business context |
| **ACs** | Well-formed acceptance criteria |
| **Feature links** | Which system surfaces this User Story exercises |
| **Status** | draft → ready → in_review → deprecated progression |
| **Validation** | Checks narrative and AC clarity |

---

## When to trigger it

```
create a user story for...
write acceptance criteria for...
document a business requirement
new user story for this feature
validate this user story
structure a user story
link user story to features
review this user story
```

---

## Narrative structure

The skill validates:

```
As a [ACTOR]
I can [CAPABILITY]
So that [BUSINESS VALUE]
```

- **Actor** — Specific role (e.g., "registered customer"), not "the user"
- **Capability** — Business action in user terms, not technical implementation
- **Outcome** — Business value or reason for the capability

---

## Related skills

- [Living Doc Create Feature](./living-doc-create-feature.md) — document system surfaces
- [Living Doc Create Functionality](./living-doc-create-functionality.md) — define atomic behaviors
- [Living Doc Scenario Creator](./living-doc-scenario-creator.md) — generate Gherkin from ACs
- [Living Doc Update](./living-doc-update.md) — refine narrative or ACs
- [Living Doc Gap Finder](./living-doc-gap-finder.md) — validate User Story coverage

---

## Helper scripts

One Python utility available in `skills/living-doc-create-user-story/scripts/`:
- **next_id.py** — generate sequential User Story entity IDs (US-XXX)

---

## Testing Evals

This skill has been validated with **18 test cases** covering:
- User Story entity creation
- Narrative elicitation (As-a/I-can/so-that)
- Acceptance Criteria definition and validation
- Feature linkage workflows
- Status progression (draft → ready)
