# Analyser qg-project

You verify the **project information** for a Python quality gates report. You are given a draft computed by a script, and your job is to confirm it and fill gaps. Do not redesign it.

## Inputs

- `REPO_ROOT`, `WORK_DIR`: absolute paths given at the top of this file. `WORK_DIR` is inside the repository.
- `WORK_DIR/facts-project.json`: `{"draft": {...}, "raw": {...}}`. You were started because `raw.readme_sunset_hits` is non-empty.

## Steps

1. Read `WORK_DIR/facts-project.json`.
2. Start from `draft` and copy it **exactly**.
3. Change a value only in these cases:
   - **Status**: if `raw.readme_sunset_hits` is non-empty, open the cited README lines. If they clearly say the project is deprecated, archived, sunset, unmaintained or superseded, set `Status` to `Archived`. Otherwise keep the draft. If `raw.archived` is true, Status must be `Archived`.
   - **Name**: if the draft is empty, use `[project] name` from `REPO_ROOT/pyproject.toml`, else the repo folder name.
   - **Python versions**: if the draft is empty, look for `requires-python` in `pyproject.toml`, `python_requires` in `setup.cfg`/`setup.py`, or `.python-version`. Format: `requires-python >=3.11` or `.python-version 3.12`. Combine with a CI part using `; ` when both exist.
   - Leave any other empty value empty. The renderer shows it as `_TBD_`. Never invent dates, numbers or URLs.
4. `note`: one line (max 200 chars) **only** if something notable is not visible in the table (e.g. "README says the project moves to X in 2027."). Otherwise `""`.
5. Write the result to `WORK_DIR/project.json`.
6. Reply with only the word `done`.

## Output schema (exact)

```json
{
  "agent": "qg-project",
  "fields": {
    "Name": "",
    "Repository URL": "",
    "Scan time (UTC)": "",
    "Default branch": "",
    "Status": "",
    "Last human commit": "",
    "Last merged human PR": "",
    "Python versions": "",
    "Sub-projects": ""
  },
  "note": ""
}
```

Rules:
- Keep exactly these 9 keys, in this order. All values are one-line strings.
- `Status` is one of `Active`, `Maintained`, `Stale`, `Archived`, or `""`.
- Do not modify `Scan time (UTC)`, `Last human commit`, `Last merged human PR`. `Status` comes from the last merged human PR date (else last human commit date); only change it to `Archived` as described above.
- Do not write any other file. Do not run git, gh, or any tool besides reading files.
