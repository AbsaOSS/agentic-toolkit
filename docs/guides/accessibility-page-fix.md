# Accessibility Page Fix Skill

The `accessibility-page-fix` skill finds and fixes accessibility problems on **one page of a web app** and proves the fixes. It targets **WCAG 2.2 AA**. It is not tied to any framework, component library or backend, so you can use it in any web app.

It pairs with [`accessibility-infra-setup`](./accessibility-infra-setup.md): that skill sets up the scanning tools, this one fixes a page using them.

---

## How to use it

Name the page you want fixed. It can be a URL, a route, a component or file, or a feature name:

```
fix the accessibility issues on the settings page
make /checkout WCAG 2.2 AA compliant
axe reports 12 violations on the login page, please fix them
the dashboard doesn't work with a keyboard, remediate it
```

If you don't name a page, the skill asks for one. It never audits a whole app in one go. For several pages, run it once per page, so each page gets its own checks and report.

---

## What it does

| Step | Action |
|------|--------|
| Reach the page | Opens the page (using the project's test login, and fake network responses if the backend isn't available) and lists its states (loading, empty, error, menus and dialogs open) and the contexts a component is shown in (full page vs dialog). Hard-to-reach states such as an error message or a session-expired dialog are produced by mocking requests |
| Baseline | Runs axe on every state and takes screenshots, so changes can be compared later |
| Triage | Groups findings by root cause and decides where each fix belongs: this page, shared code, a third-party library or design |
| Manual checks | Keyboard walk, accessible names and roles, 200% text size and 320 px reflow, structure, status messages, target size, contrast. Four bundled scripts automate the repetitive parts |
| Fix | Smallest change per cause, native HTML first, re-checking after each one and comparing screenshots |
| Lock in | Adds a scan per state to the accessibility tests, proves they fail without the fix, runs regressions for anything shared, and writes a short report (including observations that are not failures) |

Automated scanners find only part of WCAG, so the page is finished when axe is clean **and** the manual checks pass.

---

## What's in the skill

```
skills/accessibility-page-fix/
├── SKILL.md                              # Workflow, rules, gotchas
├── scripts/
│   ├── keyboard-walk.mjs                 # Tabs through the page; flags invisible stops, no visible focus, unreachable clickables
│   ├── text-size-check.mjs               # 200% text, 320 px reflow, text spacing: text that doesn't grow, clipped text, dialogs too wide
│   ├── contrast-sample.mjs               # Worst-case contrast for text over images/gradients (axe "incomplete")
│   └── compare-screenshots.mjs           # Full-page pixel comparison of the base branch and yours, with diff images
├── references/
│   ├── wcag-22-aa-checklist.md           # Every criterion: what axe covers, how to check, typical fix
│   ├── fix-patterns.md                   # Framework-neutral fixes: buttons, names, focus, live regions, sizing…
│   ├── manual-verification.md            # Keyboard walk, text size, reflow and target-size checks with snippets
│   └── report-template.md                # Shape of the final report
└── evals/                                # Test prompts and a small fixture page
```

---

## Scripts

Run them from the app's directory; they load the app's own Playwright. All accept `--wait <selector>`,
`--storage <state.json>` (a saved Playwright login state for pages behind a login) and `--click "<selector>"`
(opens a menu or dialog first).

```bash
node <skill>/scripts/keyboard-walk.mjs http://localhost:4200/orders --wait h1
node <skill>/scripts/text-size-check.mjs http://localhost:4200/orders --out a11y-text-size
node <skill>/scripts/text-size-check.mjs http://localhost:4200/orders --click "#export-button" --scope '[role="dialog"]'
node <skill>/scripts/contrast-sample.mjs http://localhost:4200/orders ".hero-title"
node <skill>/scripts/compare-screenshots.mjs compare shots /orders /home --base http://localhost:4201 --head http://localhost:4200 --full
```

Their output is a set of leads for the agent and the engineer to check, not a pass/fail verdict.

---

## Requirements

- A web app with a runnable dev server
- Node.js 22+
- Playwright + axe-core. If they're missing, the skill points to `accessibility-infra-setup`.
- Network access on first run (Playwright downloads a browser)

---

## Installation

The skill is installed along with the rest of the toolkit:

```bash
npx skills add https://github.com/AbsaOSS/agentic-toolkit -g
```

To install only this skill:

```bash
npx skills add https://github.com/AbsaOSS/agentic-toolkit -g --skill accessibility-page-fix
```

See [Getting Started](../getting-started.md) for the full install guide.
