# ══════════════════════════════════════════════════════════════
# Makefile — Single command centre for all quality gates
#
# Mirrors the CI pipeline so developers get identical feedback
# locally. Run `make all` to execute every gate, or pick one.
#
# Typical developer workflow:
#   make install       — first-time setup (creates venv, installs all deps)
#   make all           — run every CI gate locally, or e.g. `make all-core` for a single project (in this case 'core')
#   make fix           — auto-fix Python lint, format issues and Terraform lint issues across all projects
#   make lock          — regenerate lockfile after editing pyproject.toml
#   make clean         — wipe all generated artifacts (.venv, caches, etc.)
#
# ══════════════════════════════════════════════════════════════

# Auto-discover Python projects: any directory that contains a pyproject.toml at depth 1 is a project.
# This avoids drift between the filesystem and a hand-maintained list.
PROJECTS := $(patsubst %/pyproject.toml,%,$(wildcard */pyproject.toml))

# .PHONY declares targets that don't correspond to files on disk. Without this, Make would skip a target
# if a file/dir with the same name exists (e.g. `core/` directory vs `unit-test-core` target).
.PHONY: all help install lock clean lint format format-fix lint-fix typecheck unit-test pip-audit lock-check tflint tflint-fix fix yamllint \
        $(foreach p,$(PROJECTS),all-$(p) clean-$(p) lint-$(p) format-$(p) format-fix-$(p) lint-fix-$(p) typecheck-$(p) unit-test-$(p) pip-audit-$(p))

# Default goal when running bare `make`.
.DEFAULT_GOAL := help

help:
	@echo "Targets:"
	@grep -E '^[a-zA-Z_-]+.*##' $(MAKEFILE_LIST) | sed 's/:.*##/ —/' | sort
	@echo ""
	@echo "Discovered projects: $(PROJECTS)"

# ──────────────────────────────────────────────
# Workspace-level targets
# ──────────────────────────────────────────────

all: lint format typecheck unit-test pip-audit lock-check yamllint tflint  ## Run every CI gate locally, for all projects

fix: lint-fix format-fix tflint-fix                      ## Auto-fix Python lint, format and Terraform lint issues

install:                                                 ## Create venv and install all deps (first-time setup)
	uv sync --all-packages

lock:                                                    ## Regenerate the workspace uv.lock after pyproject.toml changes
	# Clear UV_INDEX so the lockfile is always resolved against public PyPI.
	# This guarantees CI (which has no access to the corporate Artifactory) can
	# always install from the committed lockfile.
	UV_INDEX="" uv lock

lock-check:                                              ## Verify workspace uv.lock is in sync and free of corporate URLs
	UV_INDEX="" uv lock --check
	@if grep -q "artifacts.bcp" uv.lock; then \
		echo "::error::uv.lock contains Absa Artifactory URLs — regenerate with 'make lock'"; \
		exit 1; \
	fi

clean:                                                   ## Remove .venv, caches, and build artifacts
	rm -rf .venv .mypy_cache .ruff_cache .pytest_cache
	$(foreach p,$(PROJECTS),rm -rf $(p)/.mypy_cache $(p)/.ruff_cache $(p)/.pytest_cache $(p)/*.egg-info;)
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

tflint:                                                  ## TFLint static analysis on Terraform files in iac/ directory
	@test -d iac || (echo "ERROR: iac/ directory not found"; exit 1)
	tflint --init
	tflint --recursive --chdir=iac

tflint-fix:                                              ## TFLint auto-fix on Terraform files in iac/ directory
	@test -d iac || (echo "ERROR: iac/ directory not found"; exit 1)
	tflint --init
	tflint --recursive --fix --chdir=iac

yamllint:                                                ## Yamllint check on all YAML files
	uv run yamllint .

# ──────────────────────────────────────────────
# Aggregate per-project targets — fan out to every project
# ──────────────────────────────────────────────

lint:        $(foreach p,$(PROJECTS),lint-$(p))          ## Ruff lint
format:      $(foreach p,$(PROJECTS),format-$(p))        ## Ruff format check
format-fix:  $(foreach p,$(PROJECTS),format-fix-$(p))    ## Ruff format — auto-fix in-place (not a CI gate)
lint-fix:    $(foreach p,$(PROJECTS),lint-fix-$(p))      ## Ruff lint — auto-fix (not a CI gate)
typecheck:   $(foreach p,$(PROJECTS),typecheck-$(p))     ## mypy strict
unit-test:   $(foreach p,$(PROJECTS),unit-test-$(p))     ## Unit tests
pip-audit:   $(foreach p,$(PROJECTS),pip-audit-$(p))     ## pip-audit

# ──────────────────────────────────────────────
# Per-project targets (generated via template)
#
# `define` + `foreach` + `eval` creates identical targets for every project without copy-paste.
# ──────────────────────────────────────────────

define PROJECT_RULES

# Run every CI gate for this project only (e.g. make all-core).
all-$(1): lint-$(1) format-$(1) typecheck-$(1) unit-test-$(1) pip-audit-$(1)

lint-$(1):
	cd $(1) && uv run ruff check .

format-$(1):
	cd $(1) && uv run ruff format --check .

format-fix-$(1):
	cd $(1) && uv run ruff format .

lint-fix-$(1):
	cd $(1) && uv run ruff check --fix .

typecheck-$(1):
	cd $(1) && uv run mypy $(1)

unit-test-$(1):
	cd $(1) && uv run pytest -m unit --cov=$(1) --cov-report=term-missing

pip-audit-$(1):
	cd $(1) && uv run pip-audit --skip-editable # Ignore local editable packages, audit only real published dependencies

endef

$(foreach p,$(PROJECTS),$(eval $(call PROJECT_RULES,$(p))))
