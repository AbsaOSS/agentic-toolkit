# Issue Templates — Rendering Rules

`gh issue create --body` accepts markdown, not structured form data. YAML form fields must be rendered as markdown sections.

## Rendering

| Field type | Render as | If required + unknown |
|------------|-----------|----------------------|
| `textarea` / `input` | `### Label\n\n<content>` | `<!-- TODO: fill in -->` |
| `dropdown` | `### Label\n\n<chosen option>` | Fall back to `--web` |
| `checkboxes` | `- [x] Option` per checked item | Auto-check universal items (CoC); `--web` for rest |
| `markdown` | Skip — informational only | — |

If 3+ required fields can't be inferred, prefer `--web` over a low-quality submission.

## Markdown templates

Front-matter: `name`, `about`, `title`, `labels`, `assignees`. Body below `---` is the template — fill each section, replace `<!-- placeholder -->` comments.

## Template selection

Match by `name` and `about`/`description` fields against the issue type. Use template's default `labels`. Only ask user when genuinely ambiguous.
