#!/usr/bin/env python3
"""
qg.py - single entrypoint of the python-quality-gates-report skill. Run from the repository root.

    python3 qg.py run
        Scan the repository into <repo>/.python-quality-gates-report/. If no analyser is needed,
        render the report immediately. Prints one JSON line:
            {"repo": ..., "work_dir": ..., "agents": [...], "report": "<path>" | null}
        "agents" lists the analysers to spawn; their prompts are in <work_dir>/prompt-<agent>.md.

    python3 qg.py render
        Validate the analyser outputs, render the report, and remove the work dir.
        Prints "REPORT <path>" (exit 0), "INVALID <agent>: <reason>" lines (exit 2), or
        "ERROR: <sentence>" (exit 1).
"""

import json
import shutil
import sys

sys.dont_write_bytecode = True  # keep the skill directory unchanged between permission check and execution
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))
from render import render_work_dir  # noqa: E402
from scan import WORK_DIR_NAME, collect  # noqa: E402

REFERENCES = SCRIPTS.parent / "references"
PROMPT_FILES = {
    "qg-project": "agent-project.md",
    "qg-local-gates": "agent-local-gates.md",
    "qg-ci": "agent-ci.md",
}


def write_prompts(root: Path, work_dir: Path, agents: list[str]) -> None:
    """Copy the analyser prompts into the work dir so agents read only files inside the repo."""
    shutil.copyfile(REFERENCES / "tool-palette.md", work_dir / "tool-palette.md")
    header = f"REPO_ROOT={root}\nWORK_DIR={work_dir}\n\n"
    for agent in agents:
        text = (REFERENCES / PROMPT_FILES[agent]).read_text(encoding="utf-8")
        (work_dir / f"prompt-{agent}.md").write_text(header + text, encoding="utf-8")


def main() -> int:
    command = sys.argv[1] if len(sys.argv) > 1 else ""
    root = Path.cwd().resolve()
    work_dir = root / WORK_DIR_NAME
    if command == "run":
        result = collect(root, work_dir)
        agents = result["agents_needed"]
        report = None
        if agents:
            write_prompts(root, work_dir, agents)
        else:
            code, message = render_work_dir(work_dir, [])
            if code != 0:
                print(message)
                return code
            report = message.removeprefix("REPORT ")
        print(json.dumps({"repo": result["repo"], "work_dir": str(work_dir), "agents": agents, "report": report}))
        return 0
    if command == "render":
        code, message = render_work_dir(work_dir)
        print(message)
        return code
    print("ERROR: Unknown command, use `run` or `render`.")
    return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # noqa: BLE001 - one-line failure reason for the orchestrator
        print(f"ERROR: Quality gates scan crashed ({type(exc).__name__}).")
        sys.exit(1)
