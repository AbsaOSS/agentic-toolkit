#!/usr/bin/env python3
"""
scan.py - deterministic fact collector for the python-quality-gates-report skill.

Read-only: never modifies the scanned repository. Python 3.11+ standard library only.

The skill calls this module through qg.py. Direct use is for debugging:

    python3 scan.py --identify [--repo PATH]
        Print "owner/repo" (or the folder name when there is no GitHub remote).

    python3 scan.py [--repo PATH] [--work-dir DIR]
        Write meta.json and facts-{project,local,ci}.json into the work dir
        (default: <repo>/.python-quality-gates-report/) and print one JSON line:
        {"repo": ..., "has_python": ..., "work_dir": ..., "agents_needed": [...]}.

Each facts file contains a "draft" object that already matches the output schema of the
corresponding analyser agent, plus raw evidence the agent uses to verify the draft.
"agents_needed" lists only analysers whose facts contain ambiguity the script cannot resolve.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

REPORT_FILE = "python-quality-gates-report.md"
WORK_DIR_NAME = ".python-quality-gates-report"
EXCLUDED_DIRS = frozenset({
    WORK_DIR_NAME, ".git", ".venv", "venv", "env", ".tox", ".nox", "build", "dist", "node_modules",
    "site-packages", "__pycache__", ".mypy_cache", ".ruff_cache", ".pytest_cache",
})
MAX_FILE_BYTES = 2_000_000
BOT_RE = re.compile(r"\[bot\]|dependabot|renovate|pre-commit-ci|github-actions", re.IGNORECASE)
SUNSET_RE = re.compile(
    r"\b(deprecated|no longer (?:actively )?maintained|unmaintained|not maintained|sunset(?:ting)?|"
    r"end[- ]of[- ]life|archived|superseded by)\b",
    re.IGNORECASE,
)
SCAN_TIME_FORMAT = "%d.%m.%Y %H:%M"
ACTIVE_DAYS = 90
MAINTAINED_DAYS = 365

GATES = (
    "Linter", "Formatter", "Type checker", "Test runner", "Coverage",
    "Security", "Dependency audit", "Complexity",
)
MANDATORY = frozenset(GATES[:5])
PALETTE = (
    "ruff", "pylint", "flake8", "black", "mypy", "pytest", "unittest",
    "pytest-cov", "coverage", "bandit", "pip-audit", "radon",
)
DEPENDENCY_NAMES = frozenset(PALETTE) - {"unittest"}
GATING_TRIGGERS = frozenset({"pull_request", "pull_request_target", "push", "merge_group"})
# Gates where several palette tools are alternatives; two of them together is an OVERLAP.
# Coverage is excluded on purpose: pytest-cov is a plugin on top of coverage, not a rival.
OVERLAP_GATES = frozenset({"Linter", "Formatter", "Test runner", "Security", "Complexity"})

PROJECT_FIELDS = (
    "Name", "Repository URL", "Scan time (UTC)", "Default branch", "Status",
    "Last human commit", "Last merged human PR", "Python versions", "Sub-projects",
)


# ---------------------------------------------------------------- utilities

def rel(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def read_text(path: Path) -> str:
    try:
        if path.stat().st_size > MAX_FILE_BYTES:
            return ""
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def load_toml(text: str) -> dict:
    try:
        return tomllib.loads(text)
    except tomllib.TOMLDecodeError:
        return {}


def norm(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


REQ_NAME_RE = re.compile(r"^\s*['\"]?([A-Za-z0-9][A-Za-z0-9._-]*)")


def req_name(spec: str) -> str | None:
    match = REQ_NAME_RE.match(spec)
    return norm(match.group(1)) if match else None


def strs(value: object) -> list[str]:
    return [v for v in value if isinstance(v, str)] if isinstance(value, list) else []


def evidence(path: str, line: int, text: str, kind: str) -> dict:
    return {"path": path, "line": line, "text": text.strip()[:160], "kind": kind}


def ref(item: dict) -> str:
    return f"{item['path']}:{item['line']}"


def eu_date(iso_date: str) -> str:
    """YYYY-MM-DD -> DD.MM.YYYY."""
    return dt.date.fromisoformat(iso_date).strftime("%d.%m.%Y")


def run(cmd: list[str], cwd: Path, timeout: int = 30) -> str | None:
    try:
        result = subprocess.run(
            cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout, check=False
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    return result.stdout if result.returncode == 0 else None


def tool_pattern(name: str) -> re.Pattern[str]:
    return re.compile(rf"(?<![\w.-]){re.escape(name)}(?![\w-])", re.IGNORECASE)


def find_line(lines: list[str], name: str) -> tuple[int, str]:
    """First non-comment, non-table-header line mentioning `name` as a whole token."""
    pattern = tool_pattern(name)
    for number, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith(("#", "[")):
            continue
        if pattern.search(line):
            return number, line
    return 1, ""


def walk(root: Path) -> list[Path]:
    files: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(
            d for d in dirnames if d not in EXCLUDED_DIRS and not d.endswith(".egg-info")
        )
        for name in sorted(filenames):
            path = Path(dirpath, name)
            if path.is_symlink() or rel(root, path) == REPORT_FILE:
                continue
            files.append(path)
    return files


def is_test_file(relpath: str) -> bool:
    parts = relpath.split("/")
    name = parts[-1]
    return (
        any(p in ("tests", "test", "testing") for p in parts[:-1])
        or name.startswith("test_")
        or name.endswith("_test.py")
        or name == "conftest.py"
    )


# ---------------------------------------------------------------- identity

def parse_remote(url: str) -> tuple[str, str] | None:
    match = re.search(r"github\.com[:/]([^/\s]+)/([^/\s]+?)(?:\.git)?/?$", url.strip())
    return (match.group(1), match.group(2)) if match else None


def sanitize_url(url: str) -> str:
    # Never leak credentials embedded in a remote URL.
    return re.sub(r"//[^@/]+@", "//", url.strip())


def identify(root: Path) -> tuple[str, str]:
    """Return (display id, repository URL)."""
    url = run(["git", "remote", "get-url", "origin"], root) or ""
    parsed = parse_remote(url)
    if parsed:
        owner, repo = parsed
        return f"{owner}/{repo}", f"https://github.com/{owner}/{repo}"
    return root.name, sanitize_url(url) if url else ""


# ---------------------------------------------------------------- project facts

def gh_json(args: list[str], root: Path) -> object | None:
    if not shutil.which("gh"):
        return None
    out = run(["gh", *args], root, timeout=30)
    if not out:
        return None
    try:
        return json.loads(out)
    except json.JSONDecodeError:
        return None


def default_branch(root: Path, gh_repo: dict | None) -> str:
    if gh_repo and isinstance(gh_repo.get("defaultBranchRef"), dict):
        name = gh_repo["defaultBranchRef"].get("name")
        if name:
            return name
    out = run(["git", "symbolic-ref", "--short", "refs/remotes/origin/HEAD"], root)
    return out.strip().removeprefix("origin/") if out else ""


def last_human_commit(root: Path, branch: str) -> dict | None:
    ref_name = f"origin/{branch}" if branch and run(
        ["git", "rev-parse", "--verify", "--quiet", f"origin/{branch}"], root
    ) else "HEAD"
    out = run(["git", "log", ref_name, "-n", "500", "--format=%H%x1f%an%x1f%ae%x1f%cI"], root)
    for line in (out or "").splitlines():
        parts = line.split("\x1f")
        if len(parts) != 4:
            continue
        sha, name, email, date = parts
        if BOT_RE.search(name) or BOT_RE.search(email):
            continue
        return {"sha": sha[:7], "date": date[:10]}
    return None


def last_human_pr(root: Path, repo_id: str) -> dict | None:
    data = gh_json(
        ["pr", "list", "--repo", repo_id, "--state", "merged", "--limit", "50",
         "--json", "number,mergedAt,author"],
        root,
    )
    if not isinstance(data, list):
        return None
    prs = sorted(
        (p for p in data if isinstance(p, dict) and p.get("mergedAt")),
        key=lambda p: p["mergedAt"],
        reverse=True,
    )
    for pr in prs:
        author = pr.get("author") or {}
        if author.get("is_bot") or BOT_RE.search(str(author.get("login", ""))):
            continue
        return {"number": pr.get("number"), "date": str(pr["mergedAt"])[:10]}
    return None


def activity_status(archived: bool | None, last_activity: dict | None, today: dt.date) -> str:
    """`last_activity` is the last merged human PR, or the last human commit when no PR is known."""
    if archived:
        return "Archived"
    if not last_activity:
        return ""
    age = (today - dt.date.fromisoformat(last_activity["date"])).days
    if age <= ACTIVE_DAYS:
        return "Active"
    if age <= MAINTAINED_DAYS:
        return "Maintained"
    return "Stale"


def ci_python_versions(workflow_texts: list[str]) -> list[str]:
    found: set[str] = set()
    for text in workflow_texts:
        lines = text.splitlines()
        for index, line in enumerate(lines):
            match = re.match(r"^(\s*)-?\s*python-versions?\s*:\s*(.*)$", line)
            if not match:
                continue
            found.update(re.findall(r"\b3\.\d{1,2}\b", match.group(2)))
            indent = len(match.group(1))
            for follow in lines[index + 1:]:
                if not follow.strip():
                    continue
                if len(follow) - len(follow.lstrip()) <= indent or not follow.lstrip().startswith("-"):
                    break
                found.update(re.findall(r"\b3\.\d{1,2}\b", follow))
    return sorted(found, key=lambda v: tuple(int(x) for x in v.split(".")))


def python_versions(root: Path, pyprojects: dict[str, dict], workflow_texts: list[str]) -> str:
    parts: list[str] = []
    requires = []
    classifiers: set[str] = set()
    for path in sorted(pyprojects, key=lambda p: (p.count("/"), p)):
        project = pyprojects[path].get("project", {})
        if isinstance(project, dict):
            spec = project.get("requires-python")
            if isinstance(spec, str):
                label = spec if path == "pyproject.toml" else f"{spec} ({path.rsplit('/', 1)[0]})"
                requires.append(label)
            for item in strs(project.get("classifiers")):
                match = re.match(r"Programming Language :: Python :: (3\.\d+)$", item)
                if match:
                    classifiers.add(match.group(1))
    if requires:
        parts.append("requires-python " + "; ".join(requires))
    elif classifiers:
        parts.append("classifiers " + ", ".join(sorted(classifiers, key=lambda v: int(v.split(".")[1]))))
    else:
        for name in ("setup.cfg", "setup.py"):
            match = re.search(r"python_requires\s*=\s*['\"]?([^'\"\n,)]+)", read_text(root / name))
            if match:
                parts.append(f"python_requires {match.group(1).strip()}")
                break
    version_file = read_text(root / ".python-version").strip().splitlines()
    if version_file:
        parts.append(f".python-version {version_file[0].strip()}")
    ci = ci_python_versions(workflow_texts)
    if ci:
        parts.append("CI " + ", ".join(ci))
    return " | ".join(parts)


def project_facts(
    root: Path, files: list[Path], pyprojects: dict[str, dict], workflow_texts: list[str],
    scan_time: dt.datetime,
) -> dict:
    repo_id, repo_url = identify(root)
    is_github = "/" in repo_id and repo_url.startswith("https://github.com/")
    gh_repo = gh_json(["repo", "view", repo_id, "--json", "isArchived,defaultBranchRef,description"],
                      root) if is_github else None
    gh_repo = gh_repo if isinstance(gh_repo, dict) else None
    archived = gh_repo.get("isArchived") if gh_repo else None
    branch = default_branch(root, gh_repo)
    commit = last_human_commit(root, branch) if (root / ".git").exists() else None
    pr = last_human_pr(root, repo_id) if is_github else None

    py_files = [p for p in files if p.suffix == ".py"]
    subprojects = sorted({
        rel(root, p.parent) for p in files
        if p.name in ("pyproject.toml", "setup.py", "setup.cfg") and p.parent != root
    })

    readme_hits = []
    for name in ("README.md", "README.rst", "README.txt", "README"):
        text = read_text(root / name)
        if text:
            for number, line in enumerate(text.splitlines(), 1):
                if SUNSET_RE.search(line):
                    readme_hits.append(evidence(name, number, line, "readme"))
            break

    today = scan_time.date()
    fields = {
        "Name": repo_id.split("/")[-1],
        "Repository URL": repo_url,
        "Scan time (UTC)": scan_time.strftime(SCAN_TIME_FORMAT),
        "Default branch": branch,
        "Status": activity_status(archived, pr or commit, today),
        "Last human commit": f"{eu_date(commit['date'])} ({commit['sha']})" if commit else "",
        "Last merged human PR": f"{eu_date(pr['date'])} (#{pr['number']})" if pr else "",
        "Python versions": python_versions(root, pyprojects, workflow_texts),
        "Sub-projects": ", ".join(subprojects) if subprojects else "",
    }
    return {
        "repo": repo_id,
        "has_python": bool(py_files),
        "draft": {"agent": "qg-project", "fields": fields, "note": ""},
        "raw": {
            "archived": archived,
            "description": gh_repo.get("description") if gh_repo else None,
            "gh_available": gh_repo is not None,
            "last_human_commit": commit,
            "last_merged_human_pr": pr,
            "readme_sunset_hits": readme_hits[:20],
            "status_rules": {
                "Archived": "repository archived, or README states deprecated/unmaintained/sunset",
                "Active": f"last merged human PR (else last human commit) <= {ACTIVE_DAYS} days before scan",
                "Maintained": f"last merged human PR (else last human commit) <= {MAINTAINED_DAYS} days before scan",
                "Stale": f"last merged human PR (else last human commit) > {MAINTAINED_DAYS} days before scan",
            },
        },
    }


# ---------------------------------------------------------------- command detection

INSTALL_RE = re.compile(
    r"^\s*(?:sudo\s+)?(?:python[\d.]*\s+-m\s+)?"
    r"(?:pip3?|uv\s+pip|uv\s+tool|pipx|poetry|uv|pdm|hatch|conda|mamba|micromamba|brew|apt(?:-get)?)"
    r"\s+(?:install|add|sync|lock|inject|self|upgrade|env\s+create)\b",
    re.IGNORECASE,
)
COMMAND_RULES: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("ruff-format", re.compile(r"(?<![\w.-])ruff\s+format\b")),
    ("ruff-check", re.compile(r"(?<![\w.-])ruff(?![\w-])(?!\s+format\b)(?!\s+--?version\b)")),
    ("black", tool_pattern("black")),
    ("flake8", tool_pattern("flake8")),
    ("pylint", tool_pattern("pylint")),
    ("mypy", tool_pattern("mypy")),
    ("pytest", re.compile(r"(?<![\w.-])(?:pytest|py\.test)(?![\w-])")),
    ("unittest", re.compile(r"-m\s+unittest\b")),
    ("pytest-cov", re.compile(r"(?<![\w-])--cov\b")),
    ("coverage", re.compile(r"(?<![\w.-])coverage\s+(?:run|report|xml|html|json|lcov|combine|erase)\b")),
    ("bandit", tool_pattern("bandit")),
    ("pip-audit", re.compile(r"(?<![\w.-])pip[-_]audit(?![\w-])")),
    ("radon", tool_pattern("radon")),
)
KEY_TO_TOOL = {"ruff-format": "ruff", "ruff-check": "ruff"}
SELECT_RE = re.compile(r"--(?:extend-)?select[=\s]+([A-Z0-9,]+)")
HOOK_COMMANDS = {
    "ruff": "ruff check", "ruff-check": "ruff check", "ruff-format": "ruff format",
    "black": "black", "black-jupyter": "black", "flake8": "flake8", "pylint": "pylint",
    "mypy": "mypy", "bandit": "bandit", "pip-audit": "pip-audit", "pytest": "pytest",
    "radon": "radon",
}


def selects_security(codes: list[str]) -> bool:
    return any(c == "ALL" or re.fullmatch(r"S\d*", c) for c in codes)


def selects_complexity(codes: list[str]) -> bool:
    return any(c in ("ALL", "C", "C9", "C90", "C901") for c in codes)


def segments(text: str) -> list[str]:
    joined = re.sub(r"\\\s*\n\s*", " ", text)
    out: list[str] = []
    for line in joined.splitlines():
        for part in re.split(r"\s*(?:&&|\|\||;)\s*", line):
            part = part.strip()
            if part and not part.startswith("#") and not part.startswith("echo "):
                out.append(part)
    return out


def detect(segment: str) -> list[str]:
    if INSTALL_RE.match(segment):
        return []
    return [key for key, pattern in COMMAND_RULES if pattern.search(segment)]


# ---------------------------------------------------------------- indirection sources

def ini_entries(text: str):
    """Yield (section, key, value, line) for every value line of an INI file."""
    section, key = "", ""
    for number, raw in enumerate(text.splitlines(), 1):
        if not raw.strip() or raw.lstrip().startswith(("#", ";")):
            continue
        header = re.match(r"^\[([^\]]+)\]", raw)
        if header:
            section, key = header.group(1).strip(), ""
            continue
        if raw[0] in " \t" and key:
            yield section, key, raw.strip(), number
            continue
        match = re.match(r"^([\w.-]+)\s*[=:]\s*(.*)$", raw)
        if match:
            key = match.group(1).strip()
            if match.group(2).strip():
                yield section, key, match.group(2).strip(), number


def parse_makefile(text: str) -> dict[str, dict]:
    targets: dict[str, dict] = {}
    current: list[str] = []
    for number, line in enumerate(text.splitlines(), 1):
        if line.startswith("\t"):
            for name in current:
                targets[name]["recipe"].append((number, line.strip().lstrip("@-+")))
            continue
        match = re.match(r"^([A-Za-z0-9_./%$()-][A-Za-z0-9_./%$() -]*?)\s*::?(?!=)\s*(.*)$", line)
        if match and not line.lstrip().startswith("#") and "=" not in match.group(1):
            names = match.group(1).split()
            deps = match.group(2).split("#")[0].split(";")[0].split()
            current = names
            for name in names:
                targets.setdefault(name, {"line": number, "deps": deps, "recipe": []})
        elif line.strip() and not line.lstrip().startswith("#"):
            current = []
    return targets


def parse_noxfile(text: str) -> dict[str, list[tuple[int, str]]]:
    sessions: dict[str, list[tuple[int, str]]] = {}
    pending_name: str | None = None
    decorated = False
    current: str | None = None
    for number, line in enumerate(text.splitlines(), 1):
        stripped = line.strip()
        if stripped.startswith("@") and "session" in stripped:
            decorated = True
            named = re.search(r"name\s*=\s*['\"]([\w-]+)['\"]", stripped)
            pending_name = named.group(1) if named else None
            continue
        func = re.match(r"^def\s+(\w+)\s*\(", line)
        if func:
            current = (pending_name or func.group(1)) if decorated else None
            if current:
                sessions.setdefault(current, [])
            decorated, pending_name = False, None
            continue
        if current and re.search(r"\.run(?:_always|_install)?\s*\(", stripped):
            args = re.findall(r"['\"]([^'\"]+)['\"]", stripped)
            if args:
                sessions[current].append((number, " ".join(args)))
    return sessions


def parse_precommit(text: str) -> list[dict]:
    hooks: list[dict] = []
    for number, line in enumerate(text.splitlines(), 1):
        hook_id = re.match(r"^\s*-\s*id:\s*['\"]?([\w.-]+)", line)
        if hook_id:
            hooks.append({"id": hook_id.group(1), "line": number, "entry": None})
            continue
        entry = re.match(r"^\s*entry:\s*(.+)$", line)
        if entry and hooks:
            hooks[-1]["entry"] = entry.group(1).strip().strip("'\"")
    for hook in hooks:
        hook["command"] = HOOK_COMMANDS.get(hook["id"]) or hook["entry"] or ""
    return hooks


def script_commands(value: object) -> list[str]:
    """Commands of a hatch/pdm/poe script definition."""
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [c for item in value for c in script_commands(item)]
    if isinstance(value, dict):
        for key in ("cmd", "shell", "script", "composite", "sequence"):
            if key in value:
                return script_commands(value[key])
    return []


class Sources:
    """Parsed local entry points (Makefile, tox, nox, pre-commit, pyproject scripts, shell)."""

    def __init__(self, root: Path, pyproject: dict):
        self.root = root
        self.makefiles: dict[str, dict] = {}
        tox_text = read_text(root / "tox.ini")
        self.tox: dict[str, list[tuple[int, str]]] = {}
        for section, key, value, number in ini_entries(tox_text):
            if key == "commands" and section.startswith("testenv"):
                env = section.split(":", 1)[1] if ":" in section else ""
                self.tox.setdefault(env, []).append((number, value))
        self.nox = parse_noxfile(read_text(root / "noxfile.py"))
        self.precommit = parse_precommit(read_text(root / ".pre-commit-config.yaml"))
        self.pyproject_lines = read_text(root / "pyproject.toml").splitlines()
        tool = pyproject.get("tool", {}) if isinstance(pyproject.get("tool"), dict) else {}
        self.scripts: dict[str, dict[str, list[str]]] = {"hatch": {}, "pdm": {}, "poe": {}}
        envs = tool.get("hatch", {}).get("envs", {}) if isinstance(tool.get("hatch"), dict) else {}
        for env_name, env in (envs.items() if isinstance(envs, dict) else []):
            for name, value in (env.get("scripts", {}) or {}).items() if isinstance(env, dict) else []:
                self.scripts["hatch"][f"{env_name}:{name}"] = script_commands(value)
        pdm = tool.get("pdm", {}).get("scripts", {}) if isinstance(tool.get("pdm"), dict) else {}
        for name, value in (pdm.items() if isinstance(pdm, dict) else []):
            self.scripts["pdm"][name] = script_commands(value)
        poe = tool.get("poe", {}).get("tasks", {}) if isinstance(tool.get("poe"), dict) else {}
        for name, value in (poe.items() if isinstance(poe, dict) else []):
            self.scripts["poe"][name] = script_commands(value)

    def makefile(self, relpath: str) -> dict[str, dict]:
        if relpath not in self.makefiles:
            self.makefiles[relpath] = parse_makefile(read_text(self.root / relpath))
        return self.makefiles[relpath]

    def script_line(self, name: str) -> int:
        short = name.split(":")[-1]
        pattern = re.compile(rf"^\s*['\"]?{re.escape(short)}['\"]?\s*=")
        for number, line in enumerate(self.pyproject_lines, 1):
            if pattern.match(line):
                return number
        return 1

    def resolve(self, segment: str) -> tuple[list[tuple[str, str]], bool]:
        """Return ([(command, via)], wrapper_detected) for one level of indirection."""
        out: list[tuple[str, str]] = []
        if INSTALL_RE.match(segment):
            return out, False
        make = re.search(r"(?:(?<![\w.-])make|\$\(MAKE\))\s*(.*)$", segment)
        if make:
            tokens = make.group(1).split()
            path, targets, skip = "Makefile", [], False
            for index, token in enumerate(tokens):
                if skip:
                    skip = False
                    continue
                if token in ("-C", "-f"):
                    if index + 1 < len(tokens):
                        value = tokens[index + 1]
                        path = f"{value.rstrip('/')}/Makefile" if token == "-C" else value
                    skip = True
                elif not token.startswith("-") and "=" not in token:
                    targets.append(token)
            parsed = self.makefile(path)
            if not targets:
                targets = [next((t for t in parsed if not t.startswith(".")), "")]
            for target in targets:
                info = parsed.get(target)
                if not info:
                    continue
                for dep in [target, *info["deps"]]:
                    for number, command in parsed.get(dep, {}).get("recipe", []):
                        out.append((command, f"make {target} -> {path}:{number}"))
            return out, True
        tox = re.search(r"(?<![\w.-])tox(?![\w-])(.*)$", segment)
        if tox:
            envs_arg = re.search(r"(?:-e|--envlist)[=\s]+([\w.,:-]+)", tox.group(1))
            envs = envs_arg.group(1).split(",") if envs_arg else list(self.tox)
            for env in envs:
                for number, command in self.tox.get(env, self.tox.get("", [])):
                    out.append((command, f"tox -e {env or 'default'} -> tox.ini:{number}"))
            return out, True
        nox = re.search(r"(?<![\w.-])nox(?![\w-])(.*)$", segment)
        if nox:
            chosen = re.search(r"(?:-s|--sessions?)\s+([\w\s-]+)", nox.group(1))
            names = chosen.group(1).split() if chosen else list(self.nox)
            for name in names:
                for number, command in self.nox.get(name, []):
                    out.append((command, f"nox -s {name} -> noxfile.py:{number}"))
            return out, True
        precommit = re.search(r"(?<![\w.-])(?:pre-commit|prek)\s+run\b(.*)$", segment)
        if precommit:
            wanted = [t for t in precommit.group(1).split() if not t.startswith("-")]
            for hook in self.precommit:
                if hook["command"] and (not wanted or hook["id"] in wanted):
                    out.append((hook["command"],
                                f"pre-commit hook {hook['id']} -> .pre-commit-config.yaml:{hook['line']}"))
            return out, True
        for runner, pattern in (
            ("hatch", r"(?<![\w.-])hatch\s+run\s+((?:[\w-]+:)?[\w-]+)"),
            ("pdm", r"(?<![\w.-])pdm\s+run\s+([\w-]+)"),
            ("poe", r"(?<![\w.-])(?:poe|poethepoet)\s+([\w-]+)"),
        ):
            match = re.search(pattern, segment)
            if not match:
                continue
            name = match.group(1)
            if runner == "hatch" and ":" not in name:
                name = f"default:{name}"
            commands = self.scripts[runner].get(name)
            if commands is None:
                continue
            line = self.script_line(name)
            out.extend((c, f"{runner} {name} -> pyproject.toml:{line}") for c in commands)
            return out, True
        shell = re.search(r"(?:^|\s)(?:bash\s+|sh\s+|source\s+)?\.?/?((?:[\w.-]+/)*[\w.-]+\.sh)\b", segment)
        if shell:
            text = read_text(self.root / shell.group(1))
            for number, line in enumerate(text.splitlines(), 1):
                if line.strip() and not line.lstrip().startswith("#"):
                    out.append((line.strip(), f"{shell.group(1)} -> {shell.group(1)}:{number}"))
            return out, True
        wrapper = re.match(r"^(?:just|task|invoke|inv|nox|tox|make|hatch|pdm|poe)\b", segment)
        return out, bool(wrapper)


# ---------------------------------------------------------------- local gates

PYPROJECT_TOOL_TABLES = (
    "ruff", "pylint", "flake8", "black", "mypy", "pytest", "coverage", "bandit", "radon",
)
STANDALONE_CONFIGS = {
    "ruff.toml": "ruff", ".ruff.toml": "ruff", ".pylintrc": "pylint", "pylintrc": "pylint",
    ".flake8": "flake8", "mypy.ini": "mypy", ".mypy.ini": "mypy", "pytest.ini": "pytest",
    "conftest.py": "pytest", ".coveragerc": "coverage", ".bandit": "bandit",
    "bandit.yaml": "bandit", "bandit.yml": "bandit", "radon.cfg": "radon",
}
INI_SECTION_TOOLS = (
    (re.compile(r"^flake8$"), "flake8"),
    (re.compile(r"^mypy(?:-.*)?$"), "mypy"),
    (re.compile(r"^(?:tool:)?pytest$"), "pytest"),
    (re.compile(r"^coverage:"), "coverage"),
    (re.compile(r"^pylint"), "pylint"),
    (re.compile(r"^radon$"), "radon"),
    (re.compile(r"^bandit$"), "bandit"),
)
REQUIREMENTS_RE = re.compile(r"(?:^|[-_.])requirements?(?:[-_.].*)?\.(?:txt|in)$", re.IGNORECASE)
THRESHOLD_RES = (
    re.compile(r"^\s*fail_under\s*=\s*([\d.]+)"),
    re.compile(r"--cov-fail-under[=\s]+([\d.]+)"),
)
UNITTEST_RE = re.compile(r"unittest\.TestCase\b|from\s+unittest\s+import\s+[^\n]*\bTestCase\b")


def pyproject_dependencies(data: dict) -> set[str]:
    specs: list[str] = []
    names: list[str] = []
    project = data.get("project", {}) if isinstance(data.get("project"), dict) else {}
    specs += strs(project.get("dependencies"))
    for group in (project.get("optional-dependencies") or {}).values():
        specs += strs(group)
    for group in (data.get("dependency-groups") or {}).values():
        specs += strs(group)
    tool = data.get("tool", {}) if isinstance(data.get("tool"), dict) else {}
    poetry = tool.get("poetry", {}) if isinstance(tool.get("poetry"), dict) else {}
    for key in ("dependencies", "dev-dependencies"):
        if isinstance(poetry.get(key), dict):
            names += list(poetry[key])
    for group in (poetry.get("group") or {}).values():
        if isinstance(group, dict) and isinstance(group.get("dependencies"), dict):
            names += list(group["dependencies"])
    pdm = tool.get("pdm", {}) if isinstance(tool.get("pdm"), dict) else {}
    for group in (pdm.get("dev-dependencies") or {}).values():
        specs += strs(group)
    hatch = tool.get("hatch", {}) if isinstance(tool.get("hatch"), dict) else {}
    for env in (hatch.get("envs") or {}).values():
        if isinstance(env, dict):
            specs += strs(env.get("dependencies")) + strs(env.get("extra-dependencies"))
    uv = tool.get("uv", {}) if isinstance(tool.get("uv"), dict) else {}
    specs += strs(uv.get("dev-dependencies"))
    found = {req_name(s) for s in specs} | {norm(n) for n in names}
    return {n for n in found if n}


def ruff_codes(data: dict) -> list[str]:
    codes: list[str] = []
    for table in (data, data.get("lint", {})):
        if isinstance(table, dict):
            codes += strs(table.get("select")) + strs(table.get("extend-select"))
    return codes


def local_facts(root: Path, files: list[Path], pyprojects: dict[str, dict], sources: Sources) -> dict:
    tools: dict[str, list[dict]] = {t: [] for t in PALETTE}
    considered: list[str] = []
    codes: list[str] = []
    select_evidence: list[dict] = []
    threshold: dict | None = None
    unittest_invoked = False

    def add(tool: str, item: dict) -> None:
        if all(ref(e) != ref(item) for e in tools[tool]):
            tools[tool].append(item)

    def add_command(command: str, path: str, line: int, kind: str) -> None:
        nonlocal unittest_invoked
        for key in detect(command):
            add(KEY_TO_TOOL.get(key, key), evidence(path, line, command, kind))
            unittest_invoked = unittest_invoked or key == "unittest"

    for path in files:
        relpath, name = rel(root, path), path.name
        text = None
        if name == "pyproject.toml":
            text = read_text(path)
            lines = text.splitlines()
            data = pyprojects.get(relpath, {})
            for dep in sorted(pyproject_dependencies(data) & DEPENDENCY_NAMES):
                number, line = find_line(lines, dep)
                add(dep, evidence(relpath, number, line, "dependency"))
            tool_table = data.get("tool", {}) if isinstance(data.get("tool"), dict) else {}
            for key in PYPROJECT_TOOL_TABLES:
                if key in tool_table:
                    pattern = re.compile(rf"^\[tool\.{key}\b")
                    number = next((i for i, l in enumerate(lines, 1) if pattern.match(l)), 1)
                    add(key, evidence(relpath, number, lines[number - 1] if lines else "", "config"))
            ruff_table = tool_table.get("ruff")
            if isinstance(ruff_table, dict):
                found = ruff_codes(ruff_table)
                codes += found
                if found:
                    number = next((i for i, l in enumerate(lines, 1)
                                   if re.match(r"^\s*(?:extend-)?select\s*=", l)), 1)
                    select_evidence.append(evidence(relpath, number, lines[number - 1], "config"))
        elif name in ("ruff.toml", ".ruff.toml"):
            text = read_text(path)
            found = ruff_codes(load_toml(text))
            codes += found
            if found:
                lines = text.splitlines()
                number = next((i for i, l in enumerate(lines, 1)
                               if re.match(r"^\s*(?:extend-)?select\s*=", l)), 1)
                select_evidence.append(evidence(relpath, number, lines[number - 1], "config"))
        elif REQUIREMENTS_RE.search(name) or (
            path.parent.name == "requirements" and path.suffix in (".txt", ".in")
        ):
            text = read_text(path)
            for number, line in enumerate(text.splitlines(), 1):
                if line.strip().startswith(("#", "-")):
                    continue
                dep = req_name(line)
                if dep in DEPENDENCY_NAMES:
                    add(dep, evidence(relpath, number, line, "dependency"))
        elif name == "Pipfile":
            text = read_text(path)
            data = load_toml(text)
            lines = text.splitlines()
            for section in ("packages", "dev-packages"):
                for dep in sorted({norm(n) for n in (data.get(section) or {})} & DEPENDENCY_NAMES):
                    number, line = find_line(lines, dep)
                    add(dep, evidence(relpath, number, line, "dependency"))
        elif name in ("setup.cfg", "tox.ini"):
            text = read_text(path)
            for section, key, value, number in ini_entries(text):
                is_dep = (
                    (section == "options" and key in ("install_requires", "tests_require"))
                    or section == "options.extras_require"
                    or (section.startswith("testenv") and key == "deps")
                )
                if is_dep:
                    dep = req_name(value)
                    if dep in DEPENDENCY_NAMES:
                        add(dep, evidence(relpath, number, value, "dependency"))
            for number, line in enumerate(text.splitlines(), 1):
                header = re.match(r"^\[([^\]]+)\]", line)
                if header:
                    for pattern, tool in INI_SECTION_TOOLS:
                        if pattern.search(header.group(1).strip()):
                            add(tool, evidence(relpath, number, line, "config"))
        elif name == "setup.py":
            text = read_text(path)
            for number, line in enumerate(text.splitlines(), 1):
                for spec in re.findall(r"['\"]([A-Za-z0-9][\w.-]*\s*(?:[<>=!~\[;][^'\"]*)?)['\"]", line):
                    dep = req_name(spec)
                    if dep in DEPENDENCY_NAMES:
                        add(dep, evidence(relpath, number, line, "dependency"))
        elif name == ".pre-commit-config.yaml":
            text = read_text(path)
            for hook in parse_precommit(text):
                if hook["command"]:
                    add_command(hook["command"], relpath, hook["line"], "pre-commit")
        elif path.suffix == ".py" and is_test_file(relpath):
            text = read_text(path)
            match = UNITTEST_RE.search(text)
            if match:
                number = text[: match.start()].count("\n") + 1
                add("unittest", evidence(relpath, number, text.splitlines()[number - 1], "test-code"))
            text = None
        if name in STANDALONE_CONFIGS:
            add(STANDALONE_CONFIGS[name], evidence(relpath, 1, name, "config"))
        if name in ("pyproject.toml", "pytest.ini", "setup.cfg", "tox.ini", ".coveragerc"):
            text = text if text is not None else read_text(path)
            considered.append(relpath)
            for number, line in enumerate(text.splitlines(), 1):
                if name != ".coveragerc" and re.search(r"(?<![\w-])--cov\b", line):
                    add("pytest-cov", evidence(relpath, number, line, "config"))
                for pattern in THRESHOLD_RES:
                    found = pattern.search(line)
                    if found and threshold is None:
                        threshold = {"value": found.group(1), **evidence(relpath, number, line, "config")}
        elif text is not None:
            considered.append(relpath)

    # Local entry points (root level only).
    makefile = sources.makefile("Makefile")
    for target, info in sorted(makefile.items()):
        for number, command in info["recipe"]:
            add_command(command, "Makefile", number, "invocation")
    for env, commands in sorted(sources.tox.items()):
        for number, command in commands:
            add_command(command, "tox.ini", number, "invocation")
    for session, commands in sorted(sources.nox.items()):
        for number, command in commands:
            add_command(command, "noxfile.py", number, "invocation")
    for runner in ("hatch", "pdm", "poe"):
        for name, commands in sorted(sources.scripts[runner].items()):
            for command in commands:
                add_command(command, "pyproject.toml", sources.script_line(name), "invocation")
    for path in sorted([*root.glob("*.sh"), *root.glob("scripts/*.sh"), root / "justfile"]):
        if path.is_file():
            for number, line in enumerate(read_text(path).splitlines(), 1):
                if line.strip() and not line.lstrip().startswith("#"):
                    add_command(line.strip(), rel(root, path), number, "invocation")
    if threshold is None:
        threshold = command_threshold(root, ["Makefile", "tox.ini", "noxfile.py", "justfile",
                                             *[rel(root, p) for p in root.glob("scripts/*.sh")]])

    ruff_s = bool(tools["ruff"]) and selects_security(codes)
    ruff_c90 = bool(tools["ruff"]) and selects_complexity(codes)
    present = {t for t in PALETTE if tools[t]}
    if {"unittest", "pytest"} <= present and not unittest_invoked:
        # pytest runs TestCase classes natively; that alone is not a second test runner.
        present.discard("unittest")

    gate_tools = {
        "Linter": [t for t in ("ruff", "pylint", "flake8") if t in present],
        "Formatter": [t for t in ("ruff", "black") if t in present],
        "Type checker": [t for t in ("mypy",) if t in present],
        "Test runner": [t for t in ("pytest", "unittest") if t in present],
        "Coverage": [t for t in ("pytest-cov", "coverage") if t in present],
        "Security": (["ruff"] if ruff_s else []) + [t for t in ("bandit",) if t in present],
        "Dependency audit": [t for t in ("pip-audit",) if t in present],
        "Complexity": (["ruff"] if ruff_c90 else []) + [t for t in ("radon",) if t in present],
    }
    gates = []
    for gate in GATES:
        names = gate_tools[gate]
        refs: list[str] = []
        for tool in names:
            source = select_evidence if tool == "ruff" and gate in ("Security", "Complexity") else tools[tool]
            refs += [ref(e) for e in source[:3]]
        if gate == "Coverage" and threshold:
            refs.append(ref(threshold))
        gates.append({
            "gate": gate,
            "status": gate_status(gate, names, local=True),
            "tools": names,
            "evidence": list(dict.fromkeys(refs))[:6],
        })
    return {
        "draft": {
            "agent": "qg-local-gates",
            "gates": gates,
            "coverage_threshold": threshold["value"] if threshold else "",
            "note": "",
        },
        "raw": {
            "tool_evidence": {t: tools[t][:10] for t in PALETTE if tools[t]},
            "ruff_selected_rules": sorted(set(codes)),
            "ruff_select_evidence": select_evidence,
            "ruff_security_rules_selected": ruff_s,
            "ruff_complexity_rules_selected": ruff_c90,
            "unittest_invoked": unittest_invoked,
            "coverage_threshold": threshold,
            "files_considered": considered,
        },
    }


def command_threshold(root: Path, relpaths: list[str]) -> dict | None:
    """Find `--cov-fail-under` in command files, resolving simple Make/shell variables."""
    for relpath in relpaths:
        text = read_text(root / relpath)
        variables = dict(re.findall(r"^\s*(?:export\s+)?([A-Za-z_]\w*)\s*[:?+]?=\s*['\"]?([\d.]+)", text, re.M))
        for number, line in enumerate(text.splitlines(), 1):
            found = re.search(r"--cov-fail-under[=\s]+(?:\$[({]?([A-Za-z_]\w*)[)}]?|([\d.]+))", line)
            if not found:
                continue
            value = found.group(2) or variables.get(found.group(1) or "", "")
            if value:
                return {"value": value, **evidence(relpath, number, line, "invocation")}
    return None


def gate_status(gate: str, tools: list[str], local: bool) -> str:
    if not tools:
        return "MISSING"
    if gate in OVERLAP_GATES and len(set(tools)) > 1:
        return "OVERLAP"
    return "PRESENT"


# ---------------------------------------------------------------- CI enforcement

ACTION_RULES: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"^(?:astral-sh|chartboost)/ruff-action@"), "ruff {args}"),
    (re.compile(r"^psf/black@"), "black"),
    (re.compile(r"^pypa/gh-action-pip-audit@"), "pip-audit"),
    (re.compile(r"^py-actions/flake8@"), "flake8"),
    (re.compile(r"^jpetrucciani/ruff-check@"), "ruff check"),
    (re.compile(r"^jpetrucciani/black-check@"), "black"),
    (re.compile(r"^jpetrucciani/mypy-check@"), "mypy"),
    (re.compile(r"^jpetrucciani/bandit-check@"), "bandit"),
    (re.compile(r"^pre-commit/action@"), "pre-commit run {args}"),
)
EXTERNAL_WORKFLOW_RE = re.compile(r"^[\w.-]+/[\w.-]+/\.github/workflows/[\w./-]+\.ya?ml@")
KEY_GATES = {
    "ruff-check": ("Linter",), "ruff-format": ("Formatter",), "black": ("Formatter",),
    "flake8": ("Linter",), "pylint": ("Linter",), "mypy": ("Type checker",),
    "pytest": ("Test runner",), "unittest": ("Test runner",), "pytest-cov": ("Coverage",),
    "coverage": ("Coverage",), "bandit": ("Security",), "pip-audit": ("Dependency audit",),
    "radon": ("Complexity",),
}


def parse_triggers(lines: list[str]) -> list[str]:
    for index, line in enumerate(lines):
        match = re.match(r"""^(?:on|"on"|'on'|true)\s*:\s*(.*)$""", line)
        if not match:
            continue
        rest = match.group(1).split("#")[0].strip()
        if rest:
            return [t.strip().strip("'\"") for t in rest.strip("[]{}").split(",")
                    if t.strip() and ":" not in t] or [rest.split(":")[0].strip("{ '\"")]
        triggers: list[str] = []
        base = None
        for follow in lines[index + 1:]:
            if not follow.strip() or follow.lstrip().startswith("#"):
                continue
            indent = len(follow) - len(follow.lstrip())
            if indent == 0:
                break
            base = indent if base is None else base
            if indent == base:
                name = re.match(r"^\s*-?\s*['\"]?([\w-]+)['\"]?", follow)
                if name:
                    triggers.append(name.group(1))
        return triggers
    return []


def parse_steps(lines: list[str]) -> tuple[list[tuple[int, str]], list[tuple[int, str, str]]]:
    commands: list[tuple[int, str]] = []
    uses: list[tuple[int, str, str]] = []
    index = 0
    while index < len(lines):
        line = lines[index]
        run_key = re.match(r"^(\s*(?:-\s+)?)run\s*:\s*(.*)$", line)
        if run_key:
            key_col = len(run_key.group(1))
            rest = run_key.group(2).strip()
            if rest[:1] in ("|", ">"):
                block: list[tuple[int, str]] = []
                follow = index + 1
                while follow < len(lines):
                    text = lines[follow]
                    if text.strip() and len(text) - len(text.lstrip()) <= key_col:
                        break
                    if text.strip():
                        block.append((follow + 1, text.strip()))
                    follow += 1
                # Merge backslash continuations onto the line that starts the command.
                merged: list[tuple[int, str]] = []
                for number, text in block:
                    if merged and merged[-1][1].endswith("\\"):
                        merged[-1] = (merged[-1][0], merged[-1][1][:-1] + " " + text)
                    else:
                        merged.append((number, text))
                commands.extend(merged)
                index = follow
                continue
            if rest:
                commands.append((index + 1, rest.strip("'\"")))
        uses_key = re.match(r"^(\s*(?:-\s+)?)uses\s*:\s*['\"]?([^'\"\s#]+)", line)
        if uses_key:
            key_col = len(uses_key.group(1))
            args = []
            for follow in lines[index + 1: index + 12]:
                if re.match(r"^\s*-\s", follow) or (
                    follow.strip() and len(follow) - len(follow.lstrip()) < key_col
                ):
                    break
                arg = re.match(r"^\s*(?:args|extra_args)\s*:\s*(.+)$", follow)
                if arg:
                    args.append(arg.group(1).strip().strip("'\""))
            uses.append((index + 1, uses_key.group(2), " ".join(args)))
        index += 1
    return commands, uses


def local_target(value: str) -> str | None:
    """Repo-relative target of a local `uses: ./...` (workflow file or composite action dir)."""
    return value[2:].rstrip("/") if value.startswith("./") else None


def ci_facts(root: Path, workflow_paths: list[Path], action_paths: list[Path],
             sources: Sources, local_raw: dict) -> dict:
    units: dict[str, dict] = {}
    for path in [*workflow_paths, *action_paths]:
        relpath = rel(root, path)
        lines = read_text(path).splitlines()
        commands, uses = parse_steps(lines)
        is_action = path in action_paths
        triggers = [] if is_action else parse_triggers(lines)
        units[relpath] = {
            "file": relpath,
            "kind": "composite-action" if is_action else "workflow",
            "triggers": triggers,
            "gating": bool(GATING_TRIGGERS & set(triggers)),
            "called_by": [],
            "commands": commands,
            "uses": uses,
        }
    action_dirs = {u["file"].rsplit("/", 1)[0]: f for f, u in units.items() if u["kind"] == "composite-action"}

    # Reusable workflows and composite actions inherit gating from their callers.
    for _ in range(5):
        changed = False
        for unit in units.values():
            if not unit["gating"]:
                continue
            for _, value, _ in unit["uses"]:
                target = local_target(value)
                if not target:
                    continue
                callee = units.get(target) or units.get(action_dirs.get(target, ""))
                if callee and unit["file"] not in callee["called_by"]:
                    callee["called_by"].append(unit["file"])
                    if not callee["gating"]:
                        callee["gating"] = changed = True
        if not changed:
            break

    hits: list[dict] = []
    unresolved: list[dict] = []
    external: list[dict] = []

    def record(command: str, unit: dict, line: int, via: str | None, depth: int) -> None:
        for key in detect(command):
            hits.append({
                "key": key, "workflow": unit["file"], "line": line, "command": command[:160],
                "via": via, "gating": unit["gating"], "select": SELECT_RE.findall(command),
            })
        resolved, wrapper = sources.resolve(command)
        if wrapper and not resolved:
            unresolved.append({"workflow": unit["file"], "line": line, "command": command[:160]})
        if depth < 2:
            for inner, inner_via in resolved:
                for part in segments(inner):
                    record(part, unit, line, f"{via} | {inner_via}" if via else inner_via, depth + 1)

    for unit in units.values():
        for line, text in unit["commands"]:
            for part in segments(text):
                record(part, unit, line, None, 0)
        for line, value, args in unit["uses"]:
            if EXTERNAL_WORKFLOW_RE.match(value):
                external.append({"workflow": unit["file"], "line": line, "uses": value,
                                 "gating": unit["gating"]})
                continue
            for pattern, template in ACTION_RULES:
                if pattern.match(value):
                    command = template.format(args=args or ("check" if "ruff" in template else "")).strip()
                    record(command, unit, line, f"uses {value.split('@')[0]}", 0)
                    break

    local_tools = local_raw["tool_evidence"]
    ruff_s = local_raw["ruff_security_rules_selected"]
    ruff_c90 = local_raw["ruff_complexity_rules_selected"]
    cov_in_config = any(e["kind"] == "config" for e in local_tools.get("pytest-cov", []))

    per_gate: dict[str, list[tuple[str, dict]]] = {g: [] for g in GATES}
    for hit in hits:
        if not hit["gating"]:
            continue
        tool = KEY_TO_TOOL.get(hit["key"], hit["key"])
        for gate in KEY_GATES[hit["key"]]:
            per_gate[gate].append((tool, hit))
        if hit["key"] == "ruff-check":
            codes = [c for group in hit["select"] for c in group.split(",")]
            if ruff_s or selects_security(codes):
                per_gate["Security"].append(("ruff", hit))
            if ruff_c90 or selects_complexity(codes):
                per_gate["Complexity"].append(("ruff", hit))
        if hit["key"] == "pytest" and cov_in_config:
            per_gate["Coverage"].append(("pytest-cov", {**hit, "via": (hit["via"] or "") + " (--cov in pytest config)"}))

    gating_external = [e for e in external if e["gating"]]
    gates = []
    for gate in GATES:
        entries = per_gate[gate]
        tools = list(dict.fromkeys(t for t, _ in entries))
        refs = []
        for _, hit in entries:
            text = f"{hit['workflow']}:{hit['line']}"
            if hit["via"]:
                text += f" via {hit['via'].strip()}"
            refs.append(text)
        status = gate_status(gate, tools, local=False)
        workflows = sorted({h["workflow"] for _, h in entries})
        if status == "MISSING" and gating_external:
            status = "EXTERNAL"
            workflows = sorted({e["uses"].split("@")[0] for e in gating_external})
            refs = [f"{e['workflow']}:{e['line']}" for e in gating_external]
        elif status == "MISSING":
            keys = {k for k, gates_for in KEY_GATES.items() if gate in gates_for}
            refs = [f"not on pull_request/push: {h['workflow']}:{h['line']}"
                    for h in hits if not h["gating"] and h["key"] in keys]
        gates.append({
            "gate": gate,
            "status": status,
            "tools": tools,
            "workflows": workflows,
            "evidence": list(dict.fromkeys(refs))[:4],
        })
    return {
        "draft": {"agent": "qg-ci", "gates": gates, "note": ""},
        "raw": {
            "workflows": [
                {k: u[k] for k in ("file", "kind", "triggers", "gating", "called_by")}
                for u in units.values()
            ],
            "hits": hits[:80],
            "unresolved_wrappers": unresolved[:20],
            "external_reusable_workflows": external,
            "ruff_security_rules_selected": ruff_s,
            "ruff_complexity_rules_selected": ruff_c90,
        },
    }


# ---------------------------------------------------------------- main

OWNED_FILES = (
    "meta.json", "facts-project.json", "facts-local.json", "facts-ci.json",
    "project.json", "local-gates.json", "ci.json",
    "prompt-qg-project.md", "prompt-qg-local-gates.md", "prompt-qg-ci.md", "tool-palette.md",
)


def clear_work_dir(work_dir: Path, remove_dir: bool = False) -> None:
    for name in OWNED_FILES:
        (work_dir / name).unlink(missing_ok=True)
    if remove_dir:
        try:
            work_dir.rmdir()
        except OSError:
            pass


def agents_needed(project: dict, local: dict, ci: dict) -> list[str]:
    """Analysers whose facts contain ambiguity a script cannot resolve; others render from drafts."""
    needed = []
    if project["raw"]["readme_sunset_hits"]:
        needed.append("qg-project")
    if local["raw"]["parse_warnings"]:
        needed.append("qg-local-gates")
    if ci["raw"]["unresolved_wrappers"] or any(e["gating"] for e in ci["raw"]["external_reusable_workflows"]):
        needed.append("qg-ci")
    return needed


def collect(root: Path, work_dir: Path | None = None) -> dict:
    repo_id = identify(root)[0]
    scan_time = dt.datetime.now(dt.UTC).replace(second=0, microsecond=0)
    files = walk(root)
    pyprojects = {rel(root, p): load_toml(read_text(p)) for p in files if p.name == "pyproject.toml"}
    workflow_paths = [p for p in files if rel(root, p).startswith(".github/workflows/")
                      and p.suffix in (".yml", ".yaml")]
    action_paths = [p for p in files if rel(root, p).startswith(".github/actions/")
                    and p.name in ("action.yml", "action.yaml")]
    workflow_texts = [read_text(p) for p in workflow_paths]

    project = project_facts(root, files, pyprojects, workflow_texts, scan_time)
    sources = Sources(root, pyprojects.get("pyproject.toml", {}))
    local = local_facts(root, files, pyprojects, sources)
    ci = ci_facts(root, workflow_paths, action_paths, sources, local["raw"])
    if not local["draft"]["coverage_threshold"]:
        # A threshold enforced only in CI still counts as a project threshold.
        found = command_threshold(root, [rel(root, p) for p in workflow_paths])
        if found:
            local["draft"]["coverage_threshold"] = found["value"]
            local["raw"]["coverage_threshold"] = found
            coverage = next(g for g in local["draft"]["gates"] if g["gate"] == "Coverage")
            if coverage["tools"]:
                coverage["evidence"] = [*coverage["evidence"], ref(found)][:6]
    local["raw"]["parse_warnings"] = [
        path for path, data in pyprojects.items() if not data and read_text(root / path).strip()
    ]

    work_dir = work_dir or root / WORK_DIR_NAME
    work_dir.mkdir(parents=True, exist_ok=True)
    clear_work_dir(work_dir)
    needed = agents_needed(project, local, ci) if project["has_python"] else []

    meta = {
        "schema_version": 2,
        "repo": repo_id,
        "repo_root": str(root),
        "report_path": str(root / REPORT_FILE),
        "scan_time_utc": scan_time.strftime(SCAN_TIME_FORMAT),
        "has_python": project["has_python"],
        "repository_url": project["draft"]["fields"]["Repository URL"],
        "agents_needed": needed,
    }
    outputs = {
        "meta.json": meta,
        "facts-project.json": {"draft": project["draft"], "raw": project["raw"]},
        "facts-local.json": local,
        "facts-ci.json": ci,
    }
    for name, payload in outputs.items():
        (work_dir / name).write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return {"repo": repo_id, "has_python": meta["has_python"], "work_dir": str(work_dir), "agents_needed": needed}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--repo", default=".", help="repository root (default: cwd)")
    parser.add_argument("--work-dir", help="where to write facts files")
    parser.add_argument("--identify", action="store_true", help="print owner/repo and exit")
    args = parser.parse_args()

    root = Path(args.repo).resolve()
    if not root.is_dir():
        print(f"ERROR: Repository path {root} does not exist.")
        return 1
    if args.identify:
        print(identify(root)[0])
        return 0
    print(json.dumps(collect(root, Path(args.work_dir) if args.work_dir else None)))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # noqa: BLE001 - one-line failure reason for the orchestrator
        print(f"ERROR: Fact collection crashed ({type(exc).__name__}).")
        sys.exit(1)
