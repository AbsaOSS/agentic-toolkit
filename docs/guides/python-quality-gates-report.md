# Python Quality Gates Report Skill

The `python-quality-gates-report` skill produces a fixed-format Markdown report of the Python quality gates a repository **has** locally and which of them **CI enforces**. It is a read-only static analysis: no linters or tests are executed, and only the report file is written.

It runs only when invoked explicitly with `/python-quality-gates-report`, from the repository root, with no arguments.

---

## What it does

| Step | Action |
|------|--------|
| Collect facts | `scripts/scan.py` parses pyproject/setup/requirements, tool configs, Makefile, tox, nox, pre-commit, scripts and `.github/workflows` (incl. composite actions and reusable workflows), plus git/gh metadata |
| Analyse | 3 cheap-model subagents run in parallel (`qg-project`, `qg-local-gates`, `qg-ci`). Each verifies the script draft and corrects it only with cited `path:line` evidence |
| Render | `scripts/render.py` validates their JSON, computes the verdict and recommendations, and fills the fixed template |

Terminal output is fixed:

```
🔍 Analysing Python quality gates for owner/repo…
   ├─ Collecting facts
   ├─ Running analysers in parallel: project · local-gates · ci
   └─ Rendering report
✅ Report ready: /path/to/repo/python-quality-gates-report.md
```

---

## Gates and tool palette

| Gate | Requirement | Tools recognised |
|------|-------------|------------------|
| Linter | Mandatory | ruff, pylint, flake8 |
| Formatter | Mandatory | ruff, black |
| Type checker | Mandatory | mypy |
| Test runner | Mandatory | pytest, unittest |
| Coverage | Mandatory | pytest-cov, coverage |
| Security | Recommended | ruff (`S` rules), bandit |
| Dependency audit | Recommended | pip-audit |
| Complexity | Recommended | ruff (`C90` rules), radon |

Statuses: `PRESENT`, `MISSING`, `OVERLAP` (several tools in one gate), `EXTERNAL` (CI calls a reusable workflow from another repository that may run the gate).

**Verdict** counts the 5 mandatory gates enforced in CI: all 5 → `COMPLIANT`, 1–4 → `PARTIAL`, 0 → `NON-COMPLIANT`.

**Recommendations** target one consolidated stack: ruff (lint, format, `S`, `C90`), mypy, pytest + pytest-cov (threshold, default 80%), pip-audit. Legacy tools (black, flake8, pylint, bandit, radon, unittest) get a migration hint.

---

## Report sections

1. **Project information**: name, URL, scan time, default branch, size (Small < 5k, Medium ≤ 50k, Large > 50k non-test Python LOC), last human commit and merged PR (bots excluded), Python versions, status (Active ≤ 90 days, Maintained ≤ 365 days, Stale, Sunsetting), sub-projects.
2. **Local quality gates**: one row per gate, with tools and evidence.
3. **CI enforcement**: one row per gate, with the workflow and evidence. Only workflows triggered on `pull_request`, `pull_request_target`, `push` or `merge_group` count.
4. **Summary**: verdict, present, missing, overlaps, numbered recommendations, reviewer notes.

The report is written to `<repo>/python-quality-gates-report.md` and overwritten on every run. Repositories without Python get a short "not applicable" report.

---

## Requirements

- Python 3.11+ and git.
- `gh` CLI (optional): adds the last merged PR and archived status. Missing data renders as `_TBD_`.

## Debugging

```bash
python3 skills/python-quality-gates-report/scripts/scan.py            # prints work_dir
python3 skills/python-quality-gates-report/scripts/render.py --work-dir <work_dir> --use-drafts
```

`--use-drafts` renders straight from the script output without subagents.
