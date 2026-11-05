# Tool palette and gate rules

Only these 12 tool names may appear in a `tools` list:
`ruff`, `pylint`, `flake8`, `black`, `mypy`, `pytest`, `unittest`, `pytest-cov`, `coverage`, `bandit`, `pip-audit`, `radon`.

Any other tool (pyright, pyflakes, isort, nose, safety, …) is ignored. A gate covered only by such a tool is `MISSING`.

## Gates (fixed order)

| # | Gate | Requirement | Palette tools |
|---|---|---|---|
| 1 | Linter | Mandatory | ruff, pylint, flake8 |
| 2 | Formatter | Mandatory | ruff, black |
| 3 | Type checker | Mandatory | mypy |
| 4 | Test runner | Mandatory | pytest, unittest |
| 5 | Coverage | Mandatory | pytest-cov, coverage |
| 6 | Security | Recommended | ruff (only if rule `S` is selected), bandit |
| 7 | Dependency audit | Recommended | pip-audit |
| 8 | Complexity | Recommended | ruff (only if rule `C90` is selected), radon |

## Status values

| Status | Meaning | `tools` list |
|---|---|---|
| PRESENT | Exactly one palette tool covers the gate | 1 tool |
| OVERLAP | Two or more palette tools cover the same gate (only Linter, Formatter, Test runner, Security, Complexity) | 2+ tools |
| MISSING | No palette tool covers the gate | empty |
| EXTERNAL | CI only: gate not found locally in CI, but a gating workflow calls an external reusable workflow that may run it | empty |

Coverage is never `OVERLAP`. If both pytest-cov and coverage are present, the status is `PRESENT` with both tools listed.

## Local rules

- A tool is present locally when it is **declared** (pyproject dependencies, `requirements*.txt`, `setup.cfg`, `setup.py`, Pipfile), **configured** (`[tool.<name>]`, `.pylintrc`, `.flake8`, `mypy.ini`, `.coveragerc`, `pytest.ini`, `conftest.py`, …), or **invoked** (Makefile, tox, nox, pre-commit, hatch/pdm/poe scripts, shell scripts).
- Locally, ruff counts for both Linter and Formatter.
- unittest counts only if `python -m unittest` is invoked. `unittest.TestCase` imports alongside pytest are not unittest usage.

## CI rules

- A gate is enforced only by a command in a GitHub Actions workflow triggered by `pull_request`, `pull_request_target`, `push` or `merge_group`, either directly or via local reusable workflows or composite actions called from such a workflow.
- Commands may be wrapped (make targets incl. prerequisites, tox, nox, pre-commit, hatch/pdm/poe scripts, `.sh` files), resolved up to 2 levels deep.
- Install lines (`pip install ruff`, `uv add`, `poetry install`) never count.
- In CI, `ruff check` (or bare `ruff`) counts for Linter, and `ruff format` counts for Formatter.
- ruff counts for Security/Complexity only if `S`/`C90` is selected in local config or in a `--select`/`--extend-select` flag.
- `pytest` counts as Coverage when it is run with `--cov` or when the pytest config `addopts` contains `--cov`.
- Coverage threshold: a `fail_under` / `--cov-fail-under` value below 80 (or none) does not change the Coverage status. The report only suggests raising it to at least 80.

## Evidence format

`path:line`, relative to the repo root, e.g. `pyproject.toml:42`, `.github/workflows/ci.yml:31`.
