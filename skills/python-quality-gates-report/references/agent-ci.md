# Analyser qg-ci

You verify which **Python quality gates are enforced in CI** (GitHub Actions). You do **not** check whether CI passes. You are given a draft computed by a script. Confirm it, and correct it only with file evidence.

## Inputs

- `REPO_ROOT`, `WORK_DIR`: absolute paths given at the top of this file. `WORK_DIR` is inside the repository.
- `WORK_DIR/facts-ci.json`: `{"draft": {...}, "raw": {...}}`.
  - `raw.workflows`: `{file, kind, triggers, gating, called_by}` per workflow/composite action. `gating: true` means it runs on pull_request/push/merge_group (directly or via a caller).
  - `raw.hits`: detected tool commands: `{key, workflow, line, command, via, gating, select}`. `key` is a palette tool, or `ruff-check` / `ruff-format`. `via` describes the wrapper chain or `uses:` action, or null for a direct command.
  - `raw.unresolved_wrappers`: wrapper commands the script could not resolve (e.g. `make ci` with no Makefile target found).
  - `raw.external_reusable_workflows`: `uses:` of workflows from other repositories.
- `WORK_DIR/tool-palette.md`: the authoritative gate and status rules. Read it first.

## Steps

1. Read `tool-palette.md`, then `WORK_DIR/facts-ci.json`.
2. Start from `draft` and copy it **exactly**.
3. Spot-check: open the workflow file of the 1–2 most important gating hits and confirm the cited line runs the tool (not just installs it). If a hit is only an install, a comment, or a disabled step (`if: false`), remove it and recompute that gate.
4. Resolve `raw.unresolved_wrappers` only: open the wrapper target (Makefile, tox.ini, noxfile.py, script, `pyproject.toml` scripts) and add any palette tool it runs. Cite the workflow line in `evidence` and add the wrapper file line after it.
5. Recompute the status of every gate you changed using the rules in `tool-palette.md`:
   - `EXTERNAL` only when the gate has no tools and a **gating** workflow calls an external reusable workflow. `workflows` lists the external `uses:` paths without `@ref`, and `evidence` lists the calling lines.
   - Do not change gates you did not touch.
   - Draft evidence strings may carry context after `path:line`, such as `via make lint | Makefile:12` or `not on pull_request/push: ...`. Keep them unchanged.
6. `note`: one line (max 200 chars) only for something the table cannot express (e.g. "Lint job has continue-on-error: true."). Otherwise `""`.
7. Write the result to `WORK_DIR/ci.json`.
8. Reply with only the word `done`.

## Output schema (exact)

```json
{
  "agent": "qg-ci",
  "gates": [
    {"gate": "Linter", "status": "PRESENT", "tools": ["ruff"], "workflows": [".github/workflows/ci.yml"], "evidence": [".github/workflows/ci.yml:31"]},
    {"gate": "Formatter", "status": "MISSING", "tools": [], "workflows": [], "evidence": []},
    {"gate": "Type checker", "status": "PRESENT", "tools": ["mypy"], "workflows": [".github/workflows/ci.yml"], "evidence": [".github/workflows/ci.yml:35"]},
    {"gate": "Test runner", "status": "PRESENT", "tools": ["pytest"], "workflows": [".github/workflows/ci.yml"], "evidence": [".github/workflows/ci.yml:40"]},
    {"gate": "Coverage", "status": "PRESENT", "tools": ["pytest-cov"], "workflows": [".github/workflows/ci.yml"], "evidence": [".github/workflows/ci.yml:40"]},
    {"gate": "Security", "status": "MISSING", "tools": [], "workflows": [], "evidence": []},
    {"gate": "Dependency audit", "status": "EXTERNAL", "tools": [], "workflows": ["my-org/shared/.github/workflows/audit.yml"], "evidence": [".github/workflows/security.yml:12"]},
    {"gate": "Complexity", "status": "MISSING", "tools": [], "workflows": [], "evidence": []}
  ],
  "note": ""
}
```

Rules:
- Exactly 8 gates, in this order.
- `status`: `PRESENT` (1 tool), `OVERLAP` (2+ tools; never for Type checker, Dependency audit or Coverage), `MISSING` (no tools), `EXTERNAL` (no tools).
- `tools`: palette names only (`ruff`, never `ruff-check`), no duplicates.
- `workflows` and `evidence`: paths relative to the repo root.
- Do not write any other file. Do not execute any tool; only read files.
