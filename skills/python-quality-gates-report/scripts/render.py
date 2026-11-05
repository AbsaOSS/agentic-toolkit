#!/usr/bin/env python3
"""
render.py - validate analyser outputs and render the python-quality-gates-report.

The skill calls this module through qg.py. Direct use is for debugging:

    python3 render.py --work-dir DIR [--use-drafts] [--keep]
        Read meta.json and the outputs of the analysers listed in meta "agents_needed"
        (project.json, local-gates.json, ci.json). Analysers not listed use the scan drafts.
        --use-drafts ignores all agent outputs. The work dir is removed after rendering
        unless --keep is given.

Output (one line on stdout) and exit codes:
    0  REPORT <absolute report path>
    2  INVALID <agent>: <reason>   (one line per invalid analyser output; re-run that agent)
    1  ERROR: <one sentence>
"""

from __future__ import annotations

import argparse
import json
import re
import sys

sys.dont_write_bytecode = True
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from scan import GATES, MANDATORY, PALETTE, PROJECT_FIELDS, clear_work_dir  # noqa: E402

ASSETS = Path(__file__).resolve().parent.parent / "assets"
AGENT_FILES = {"qg-project": "project.json", "qg-local-gates": "local-gates.json", "qg-ci": "ci.json"}
DRAFT_FILES = {"qg-project": "facts-project.json", "qg-local-gates": "facts-local.json", "qg-ci": "facts-ci.json"}
LOCAL_STATUSES = {"PRESENT", "MISSING", "OVERLAP"}
CI_STATUSES = LOCAL_STATUSES | {"EXTERNAL"}
PROJECT_STATUSES = {"Active", "Maintained", "Stale", "Archived", ""}
IN_PLACE = {"PRESENT", "OVERLAP"}
RUFF_GATES = ("Linter", "Formatter", "Security", "Complexity")
RUFF_CHECK_GATES = {"Linter", "Security", "Complexity"}
SUBPROJECTS = "Sub-projects"
MAX_NOTE = 300
MAX_EVIDENCE_SHOWN = 3
MIN_COVERAGE_THRESHOLD = 80


class Invalid(Exception):
    pass


# ---------------------------------------------------------------- validation

def check(condition: bool, reason: str) -> None:
    if not condition:
        raise Invalid(reason)


def check_note(data: dict) -> None:
    note = data.get("note")
    check(isinstance(note, str), "`note` must be a string")
    check("\n" not in note and len(note) <= MAX_NOTE, f"`note` must be one line of at most {MAX_NOTE} chars")


def check_gates(data: dict, statuses: set[str], ci: bool) -> None:
    gates = data.get("gates")
    check(isinstance(gates, list) and len(gates) == len(GATES), f"`gates` must list exactly {len(GATES)} gates")
    for expected, gate in zip(GATES, gates):
        check(isinstance(gate, dict) and gate.get("gate") == expected,
              f"gates must be in fixed order; expected `{expected}`")
        status, tools = gate.get("status"), gate.get("tools")
        check(status in statuses, f"{expected}: status must be one of {sorted(statuses)}")
        check(isinstance(tools, list) and all(t in PALETTE for t in tools),
              f"{expected}: tools must be palette names {list(PALETTE)}")
        check(len(set(tools)) == len(tools), f"{expected}: duplicate tools")
        if status == "PRESENT":
            check(len(tools) >= 1, f"{expected}: PRESENT needs at least one tool")
        if status == "OVERLAP":
            check(len(tools) >= 2, f"{expected}: OVERLAP needs at least two tools")
        if status in ("MISSING", "EXTERNAL"):
            check(not tools, f"{expected}: {status} must have an empty tools list")
        evidence = gate.get("evidence")
        check(isinstance(evidence, list) and all(isinstance(e, str) for e in evidence),
              f"{expected}: evidence must be a list of strings")
        if ci:
            workflows = gate.get("workflows")
            check(isinstance(workflows, list) and all(isinstance(w, str) for w in workflows),
                  f"{expected}: workflows must be a list of strings")


def validate(agent: str, data: object) -> None:
    check(isinstance(data, dict), "top level must be a JSON object")
    check(data.get("agent") == agent, f"`agent` must be `{agent}`")
    check_note(data)
    if agent == "qg-project":
        fields = data.get("fields")
        check(isinstance(fields, dict) and list(fields) == list(PROJECT_FIELDS),
              f"`fields` must have exactly these keys in order: {list(PROJECT_FIELDS)}")
        check(all(isinstance(v, str) and "\n" not in v for v in fields.values()),
              "every field value must be a one-line string")
        check(fields["Status"] in PROJECT_STATUSES, f"Status must be one of {sorted(PROJECT_STATUSES)}")
    elif agent == "qg-local-gates":
        check_gates(data, LOCAL_STATUSES, ci=False)
        threshold = data.get("coverage_threshold")
        check(isinstance(threshold, str) and re.fullmatch(r"(\d+(\.\d+)?)?", threshold) is not None,
              "`coverage_threshold` must be a number string or empty")
    else:
        check_gates(data, CI_STATUSES, ci=True)


def load_outputs(work_dir: Path, agents: list[str] | None) -> tuple[dict, list[str]]:
    """Agents listed in `agents` must have written their output file; all others use the scan draft."""
    outputs: dict[str, dict] = {}
    problems: list[str] = []
    for agent in AGENT_FILES:
        from_agent = agents is not None and agent in agents
        path = work_dir / (AGENT_FILES if from_agent else DRAFT_FILES)[agent]
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if not from_agent:
                data = data["draft"]
            validate(agent, data)
            outputs[agent] = data
        except FileNotFoundError:
            problems.append(f"INVALID {agent}: output file {path.name} is missing")
        except json.JSONDecodeError:
            problems.append(f"INVALID {agent}: {path.name} is not valid JSON")
        except Invalid as exc:
            problems.append(f"INVALID {agent}: {exc}")
    return outputs, problems


# ---------------------------------------------------------------- rendering

def cell(value: str, empty: str = "-") -> str:
    value = value.replace("\n", " ").replace("|", "\\|").strip()
    return value or empty


def evidence_cell(items: list[str]) -> str:
    if not items:
        return "-"
    shown = ", ".join(f"`{cell(i)}`" for i in items[:MAX_EVIDENCE_SHOWN])
    extra = len(items) - MAX_EVIDENCE_SHOWN
    return f"{shown} (+{extra} more)" if extra > 0 else shown


def tools_text(gate: dict) -> str:
    return ", ".join(sorted(gate["tools"], key=PALETTE.index))


def requirement(gate: str) -> str:
    return "Mandatory" if gate in MANDATORY else "Recommended"


def status_cell(gate: dict) -> str:
    if gate["status"] == "PRESENT":
        return cell(tools_text(gate))
    if gate["status"] == "OVERLAP":
        return cell(f"OVERLAP: {tools_text(gate)}")
    return gate["status"]


def join_names(names: list[str]) -> str:
    if len(names) <= 1:
        return "".join(names)
    return ", ".join(names[:-1]) + " and " + names[-1]


def format_item(index: int, title: str, bullets: list[str]) -> str:
    return "\n".join([f"{index}. **{title}**", *(f"   - {b}" for b in bullets)])


def ruff_item(local_by: dict, ci_by: dict, catalog: dict) -> tuple[str, list[str]] | None:
    """One grouped ruff recommendation listing every gate it adds or replaces."""
    cat = catalog["ruff"]
    present = {g: set(local_by[g]["tools"]) | set(ci_by[g]["tools"]) for g in RUFF_GATES}
    ruff_in_use = any("ruff" in tools for tools in present.values())
    labels, bullets, replaced = [], [], []
    for gate in RUFF_GATES:
        legacy = sorted(present[gate] - {"ruff"}, key=PALETTE.index)
        info = cat["capabilities"][gate]
        if legacy:
            bullets.append(info["replaces"].format(tools=join_names(legacy)))
            replaced += [t for t in legacy if t not in replaced]
        elif not present[gate]:
            bullets.append(info["missing"])
        else:
            continue
        labels.append(info["label"])
    if not bullets:
        return None
    gates_involved = {g for g in RUFF_GATES if not present[g] or present[g] - {"ruff"}}
    commands = []
    if gates_involved & RUFF_CHECK_GATES:
        commands.append("`ruff check .`")
    if "Formatter" in gates_involved:
        commands.append("`ruff format --check .`")
    if not ruff_in_use:
        bullets.insert(0, cat["add_dependency"])
        title = cat["add_title"].format(capabilities=join_names(labels))
    elif replaced:
        title = cat["consolidate_title"].format(tools=join_names(sorted(replaced, key=PALETTE.index)))
    else:
        title = cat["enable_title"].format(capabilities=join_names(labels))
    if commands:
        bullets.append(cat["ci"].format(commands=join_names(commands)))
    if replaced:
        bullets.append(cat["remove"].format(tools=join_names(sorted(replaced, key=PALETTE.index))))
    return title, bullets


def build_recommendations(local_by: dict, ci_by: dict, threshold: str, externals: list[str], catalog: dict) -> list[str]:
    items: list[tuple[str, list[str]]] = []
    ruff = ruff_item(local_by, ci_by, catalog)
    if ruff:
        items.append(ruff)
    for gate in GATES:
        if gate in RUFF_GATES:
            if ruff and (set(local_by[gate]["tools"]) | set(ci_by[gate]["tools"])) != {"ruff"}:
                continue
        entry = catalog["gates"].get(gate)
        lg, cg = local_by[gate], ci_by[gate]
        local_missing, ci_missing = lg["status"] == "MISSING", cg["status"] == "MISSING"
        if local_missing and cg["status"] in ("MISSING", "EXTERNAL") and entry:
            items.append((entry["setup"]["title"], entry["setup"]["bullets"]))
        elif local_missing and cg["status"] in IN_PLACE:
            bullets = [entry["declare"] if entry else catalog["ruff"]["add_dependency"]]
            items.append((catalog["declare_title"].format(gate=gate, tools=tools_text(cg)), bullets))
        elif ci_missing:
            items.append((catalog["ci_title"].format(gate=gate), [entry["ci"] if entry else catalog["ruff"]["ci"].format(commands=join_names([f"`{t}`" for t in lg["tools"]]))]))
    if "unittest" in set(local_by["Test runner"]["tools"]) | set(ci_by["Test runner"]["tools"]):
        items.append((catalog["unittest"]["title"], catalog["unittest"]["bullets"]))
    if local_by["Coverage"]["status"] in IN_PLACE:
        if not threshold:
            items.append((catalog["coverage_threshold"]["title"], catalog["coverage_threshold"]["bullets"]))
        elif float(threshold) < MIN_COVERAGE_THRESHOLD:
            low = catalog["coverage_threshold_low"]
            items.append((low["title"], [b.format(value=threshold) for b in low["bullets"]]))
    if externals:
        workflows = sorted({w for g in externals for w in ci_by[g]["workflows"]})
        workflow_text = ", ".join(f"`{w}`" for w in workflows) or "-"
        items.append((catalog["external"]["title"], [b.format(workflows=workflow_text) for b in catalog["external"]["bullets"]]))
    return [format_item(i, title, bullets) for i, (title, bullets) in enumerate(items, 1)]


def render(meta: dict, project: dict, local: dict, ci: dict, catalog: dict) -> str:
    threshold = local["coverage_threshold"]
    project_rows = "\n".join(
        f"| {name} | {cell(value, '_TBD_')} |"
        for name, value in project["fields"].items()
        if not (name == SUBPROJECTS and value.strip().lower() in ("", "none"))
    )
    local_rows = []
    for gate in local["gates"]:
        tools = tools_text(gate) or "-"
        if gate["gate"] == "Coverage" and gate["tools"] and threshold:
            tools += f" (threshold {threshold}%)"
        local_rows.append(
            f"| {gate['gate']} | {requirement(gate['gate'])} | {gate['status']} | {cell(tools)} | "
            f"{evidence_cell(gate['evidence'])} |"
        )
    ci_rows = [
        f"| {g['gate']} | {requirement(g['gate'])} | {g['status']} | {cell(tools_text(g))} | "
        f"{cell(', '.join(g['workflows']))} | {evidence_cell(g['evidence'])} |"
        for g in ci["gates"]
    ]

    local_by = {g["gate"]: g for g in local["gates"]}
    ci_by = {g["gate"]: g for g in ci["gates"]}
    enforced = sum(1 for g in MANDATORY if ci_by[g]["status"] in IN_PLACE)
    verdict = "COMPLIANT" if enforced == len(MANDATORY) else ("NON-COMPLIANT" if enforced == 0 else "PARTIAL")
    externals = [g for g in GATES if ci_by[g]["status"] == "EXTERNAL"]
    verdict += f" (CI {enforced}/{len(MANDATORY)}"
    verdict += f"; {len(externals)} EXTERNAL to verify)" if externals else ")"

    summary_rows = [
        f"| {gate} | {requirement(gate)} | {status_cell(ci_by[gate])} |" for gate in GATES
    ]
    compliant = enforced == len(MANDATORY)
    recs = build_recommendations(local_by, ci_by, threshold, externals, catalog)
    recommendations = "\n\n".join(recs) or catalog["none"]
    heading = catalog["headings"]["suggestions" if compliant else "recommendations"]

    notes = " ".join(n.strip() for n in (project["note"], local["note"], ci["note"]) if n.strip())
    notes_section = f"\n### Reviewer notes\n\n{notes}\n" if notes else ""

    template = (ASSETS / "report-template.md").read_text(encoding="utf-8")
    values = {
        "REPO": meta["repo"],
        "PROJECT_ROWS": project_rows,
        "LOCAL_ROWS": "\n".join(local_rows),
        "CI_ROWS": "\n".join(ci_rows),
        "VERDICT": verdict,
        "SUMMARY_ROWS": "\n".join(summary_rows),
        "RECOMMENDATIONS_HEADING": heading,
        "RECOMMENDATIONS": recommendations,
        "NOTES_SECTION": notes_section,
        "TARGET_NOTE": catalog["target_note"],
    }
    for key, value in values.items():
        template = template.replace("{{" + key + "}}", value)
    return template


def render_no_python(meta: dict) -> str:
    template = (ASSETS / "report-template-no-python.md").read_text(encoding="utf-8")
    values = {
        "REPO": meta["repo"],
        "REPO_URL": cell(meta.get("repository_url", ""), "_TBD_"),
        "SCAN_TIME": meta["scan_time_utc"],
    }
    for key, value in values.items():
        template = template.replace("{{" + key + "}}", value)
    return template


def render_work_dir(work_dir: Path, agents: list[str] | None = None, cleanup: bool = True) -> tuple[int, str]:
    """Render the report. `agents`: analysers whose output files to use (default: meta agents_needed)."""
    try:
        meta = json.loads((work_dir / "meta.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return 1, "ERROR: Scan results are missing, run the scan first."

    if not meta.get("has_python"):
        report = render_no_python(meta)
    else:
        if agents is None:
            agents = meta.get("agents_needed", [])
        outputs, problems = load_outputs(work_dir, agents)
        if problems:
            return 2, "\n".join(problems)
        catalog = json.loads((ASSETS / "recommendations.json").read_text(encoding="utf-8"))
        report = render(meta, outputs["qg-project"], outputs["qg-local-gates"], outputs["qg-ci"], catalog)

    report_path = Path(meta["report_path"])
    report_path.write_text(report.rstrip("\n") + "\n", encoding="utf-8")
    if cleanup:
        clear_work_dir(work_dir, remove_dir=True)
    return 0, f"REPORT {report_path}"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--work-dir", required=True)
    parser.add_argument("--use-drafts", action="store_true", help="ignore agent outputs, render from scan drafts")
    parser.add_argument("--keep", action="store_true", help="keep the work dir after rendering")
    args = parser.parse_args()
    code, message = render_work_dir(Path(args.work_dir), [] if args.use_drafts else None, cleanup=not args.keep)
    print(message)
    return code


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # noqa: BLE001 - one-line failure reason for the orchestrator
        print(f"ERROR: Report rendering crashed ({type(exc).__name__}).")
        sys.exit(1)
