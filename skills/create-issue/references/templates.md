# Issue Templates Reference

How to discover, parse, and select GitHub issue templates in the target repository.

## Template locations

| Path | Format | Notes |
|------|--------|-------|
| `.github/ISSUE_TEMPLATE/*.yml` | YAML issue form | Structured fields with validation |
| `.github/ISSUE_TEMPLATE/*.yaml` | YAML issue form | Same as above |
| `.github/ISSUE_TEMPLATE/*.md` | Markdown template | Free-form with front-matter |
| `.github/ISSUE_TEMPLATE/config.yml` | Config file | Controls blank issues & contact links |
| `.github/ISSUE_TEMPLATE/config.yaml` | Config file | Same as above |

## Config file (`config.yml`)

Always check this file first. Key fields:

```yaml
blank_issues_enabled: false   # if false, do NOT use plain title+body — fall back to --web
contact_links:                # informational links shown to user but not templates
  - name: Community Forum
    url: https://...
    about: Ask questions here
```

If `blank_issues_enabled: false` and no template matches, inform the user and use `gh issue create --web`.

## YAML issue forms

```yaml
name: Bug Report            # ← used for template selection
description: File a bug     # ← used for template selection  
title: "[Bug]: "            # default title prefix
labels: ["bug"]             # default labels (apply these)
assignees: []
body:
  - type: markdown
    attributes:
      value: "## Description"   # informational — not a field

  - type: textarea
    id: what-happened
    attributes:
      label: What happened?
      description: A clear description of the bug
      placeholder: Tell us what you see
    validations:
      required: true            # ← must be filled

  - type: input
    id: version
    attributes:
      label: Version
      placeholder: "1.0.0"
    validations:
      required: false

  - type: dropdown
    id: severity
    attributes:
      label: Severity
      options: [Critical, High, Medium, Low]
    validations:
      required: true            # ← must choose one

  - type: checkboxes
    id: terms
    attributes:
      label: Code of Conduct
      options:
        - label: I agree
          required: true        # ← must be checked
```

### Filling YAML form fields for CLI submission

Since `gh issue create --body` accepts free-form markdown (not structured form data), render the form as markdown:

```markdown
### What happened?

<inferred or placeholder content>

### Version

<inferred or placeholder>

### Severity

<chosen option>

### Code of Conduct

- [x] I agree
```

- For **required textarea / input** fields that cannot be inferred: insert `<!-- TODO: fill in -->` and warn the user before posting.
- For **required dropdowns** with many options: pick the most likely one based on context; show the choice in the confirmation draft.
- For **required checkboxes** (e.g. CoC acceptance): check them only if the label implies universal acceptance; otherwise ask.
- If the form has **3 or more required fields** that cannot be inferred, prefer `--web` to avoid a low-quality submission.

## Markdown templates

Front-matter fields:

```yaml
---
name: Feature Request
about: Suggest an idea for this project
title: ''
labels: enhancement
assignees: ''
---
```

The body below the `---` is the template text. Fill in each section, replacing HTML comment placeholders like `<!-- Describe the feature -->`.

## Template selection

Score each template against the parsed intent (higher = better match):

| Signal | Score |
|--------|-------|
| `name` contains the issue type keyword (bug, feature, etc.) | +3 |
| `description` / `about` contains the type keyword | +2 |
| Default `labels` contain the type keyword | +2 |
| Body section headings contain relevant keywords | +1 each |

**Auto-select** when the top template scores ≥ 3 and leads by ≥ 2 over the second-best.  
**Ask the user** otherwise — list template names and one-line descriptions, let them choose.

### Common type → template name mappings

| User says | Look for template name containing |
|-----------|----------------------------------|
| bug, error, crash, broken, not working | `bug`, `defect`, `problem` |
| feature, enhancement, add, improve | `feature`, `enhancement`, `improvement` |
| question, help, how to | `question`, `support` |
| task, chore, tech debt | `task`, `chore`, `maintenance` |
| security, vulnerability | `security`, `vuln` |

## Fallback: no templates

If `.github/ISSUE_TEMPLATE/` does not exist (and blank issues are allowed):
- Use a plain title and a minimal body covering: description, steps to reproduce (if bug), expected vs actual behaviour.
