# Python Quality Gates Report: {{REPO}}

## 1. Project information

| Field | Value |
|---|---|
{{PROJECT_ROWS}}

## 2. Local quality gates

Tools declared as dependencies or configured in the repository (pyproject.toml, requirements files, setup.cfg, tox.ini, pre-commit, Makefile).

| Gate | Requirement | Status | Tools | Evidence |
|---|---|---|---|---|
{{LOCAL_ROWS}}

## 3. CI enforcement

Gates executed by GitHub Actions workflows triggered on `pull_request` or `push`.

| Gate | Requirement | Status | Tools | Workflow | Evidence |
|---|---|---|---|---|---|
{{CI_ROWS}}

## 4. Summary

**Verdict:** {{VERDICT}}

| Gate | Requirement | Tool (CI) |
|---|---|---|
{{SUMMARY_ROWS}}

### {{RECOMMENDATIONS_HEADING}}

{{RECOMMENDATIONS}}
{{NOTES_SECTION}}
{{TARGET_NOTE}}