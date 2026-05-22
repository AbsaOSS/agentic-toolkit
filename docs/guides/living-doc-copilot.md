# Living Doc Copilot Agent

`@living-doc-copilot` is the requirements layer agent. It owns the living documentation catalog — creating, updating, healing, and planning entities. It does not write code or test files.

---

## What it does

| Task | When to use |
|---|---|
| Create User Story / Feature / Functionality | Documenting new business requirements or system surfaces |
| Add or update Acceptance Criteria | After a sprint review, new requirement, or AC priority change |
| Deprecate entities | Code deleted, feature removed, or superseded by a new entity |
| Promote `PLANNED` → `ACTIVE` | After implementation is confirmed |
| Impact analysis | Before merging a PR that touches business logic |
| Gap finding — HEALING mode | Catalog has drifted: orphan tests, stale ACs, broken traceability |
| Gap finding — PLAN mode | PO has descriptions but no code exists yet |

---

## How to trigger it

```
create user story for X
document feature — login screen
update AC on US-42
deprecate the payment-gateway functionality
mark US-17 as ready
what does this change affect?
living doc gaps
HEALING mode
PLAN mode
living doc copilot
```

---

## Before you start — project setup

On first use in a project, tell the agent how your living documentation is structured. The agent calls this a **Storage Profile** and uses it to apply the correct field names, AC block layout, and entity templates for your project.

Examples of what to describe:

| What to tell the agent | Example |
|---|---|
| Where entities are stored | `docs/living-doc/` as YAML files, or ADO work items, or Confluence pages |
| Entity fields | `id`, `title`, `state`, `acs` — and what each is called in your project |
| AC block structure | Inline fields under each AC, nested list, or table |
| State vocabulary | `PLANNED` / `ACTIVE` / `DEPRECATED` or custom terms your project uses |

The agent will ask this question automatically at session start. You can also state it upfront before any command:

```
Our living doc is stored as YAML files in docs/living-doc/.
User Stories have: id, title, state, acs (list).
Each AC has: id, text, state, version, pre-conditions, not_in_scope.
```

> If the Storage Profile is incomplete, the agent will ask one targeted follow-up before creating or updating anything.

---

## Modes

### HEALING mode

Repairs catalog drift. Triggers when the living doc has fallen behind the codebase:
- Sets `DEPRECATED` state on entities whose code no longer exists
- Fixes broken traceability links (US ↔ Feature ↔ Functionality)
- Updates `version` fields and removes stale `pre-conditions`
- Does **not** repair PageObject selectors or step definitions → `@living-doc-bdd-copilot`

> `@living-doc-bdd-copilot` is the expected cooperating agent for automation-layer healing. It is deployed separately from this agent — if it is not yet available in your repo, record the automation-layer items as TODO notes for a future BDD session.

### PLAN mode

Drafts new ACs from PO descriptions before any code exists:
- Presents draft for confirmation before creating
- Creates in `PLANNED` state only — never `ACTIVE`

---

## AC Metadata

Every AC created or updated by this agent carries:

| Field | Values |
|---|---|
| `state` | `PLANNED` / `ACTIVE` / `DEPRECATED` / `IN_REVIEW` |
| `version` | Semantic version string |
| `pre-conditions` | Conditions that must hold before the AC can be tested |
| `not_in_scope` | Explicit statement of what is excluded |

---

## Skills used

| Skill | Purpose |
|---|---|
| `living-doc-create-user-story` | New User Story with business-level ACs |
| `living-doc-create-feature` | New Feature entity (system surface) |
| `living-doc-create-functionality` | New atomic, testable behaviour |
| `living-doc-update` | Amend or deprecate existing entities |
| `living-doc-impact-analysis` | Trace entities affected by a code change |
| `living-doc-gap-finder` | Find undocumented behaviours and orphan tests. **Shared skill** — used top-down here (missing doc entities) and bottom-up by `@living-doc-bdd-copilot` (scenario coverage gaps against known ACs). |

---

## Handoff

**Inbound:** `@bdd-copilot` hands a surface list after webapp exploration. Load it and create the corresponding Feature and User Story entities.

**Outbound:** When entities are confirmed and ready:

> "US and ACs are ready. Call @bdd-copilot to generate scenarios."

---

## Installation

```bash
npx skills add https://github.com/AbsaOSS/agentic-toolkit -g
```

See [Getting Started](../getting-started.md) for the full install guide.
