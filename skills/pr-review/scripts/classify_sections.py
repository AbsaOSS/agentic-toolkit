#!/usr/bin/env python3
"""
classify_sections.py — Given a list of changed files, print which pr-review
conditional sections apply.

Usage:
    # From a file list (one path per line):
    python3 classify_sections.py /tmp/pr_files.txt

    # Or pipe from gh:
    gh pr view 42 --json files --jq '.files[].path' | python3 classify_sections.py -

Output example:
    Sections to apply:
      [x] Standard review       (always)
      [x] API contracts         (router.py, schemas.py)
      [ ] Elevated risk
      [ ] Dependency bumps
      [ ] CI/CD
      [ ] Infrastructure
"""

import sys
import re
from pathlib import Path


SECTION_RULES = [
    (
        "Elevated risk",
        [
            # Elevated risk is an overlay for auth/security/infra-touching PRs.
            # Use a stricter pattern for "access" so "access-logging" does not match.
            r"\bauth\b", r"\bsecurity\b", r"\bpermission\b", r"(?<![\w-])access(?![\w-])",
            r"\bsecret\b", r"\bsecrets\b", r"\binfra(?:structure)?\b", r"\biac\b",
            r"\boauth\b", r"\bsaml\b", r"\bopenid\b", r"\bjwt\b",
        ],
    ),
    (
        "API contracts",
        [
            r"router", r"endpoint", r"controller", r"view",
            r"schema", r"dto", r"serializer",
            r"\.env", r"config\.(py|ts|js|yaml|yml|json)",
            r"action\.ya?ml",   # GitHub Actions input/output
        ],
    ),
    (
        "Dependency bumps",
        [
            r"pom\.xml$", r"requirements.*\.txt$", r"pyproject\.toml$",
            r"package\.json$", r"package-lock\.json$", r"yarn\.lock$",
            r"poetry\.lock$", r".*\.csproj$", r"go\.mod$", r"go\.sum$",
            r"build\.sbt$", r"Cargo\.toml$", r"Gemfile", r"composer\.json$",
            r"pubspec\.yaml$",
        ],
    ),
    (
        "CI/CD",
        [
            r"\.github/workflows/", r"Jenkinsfile", r"Justfile",
            # Match only exact Makefile name (not MakefileHelper.py etc.).
            # Note: still a broad heuristic — only applies when Makefile is a pipeline
            # entrypoint. A manual check is recommended when this fires on Makefile alone.
            r"(?:^|/)Makefile$",
            r"\.circleci/", r"\.travis\.yml$",
            r"azure-pipelines\.yml$", r"bitbucket-pipelines\.yml$",
        ],
    ),
    (
        "Infrastructure",
        [
            r"\.tf$", r"\.tfvars$", r"terragrunt\.hcl$",
            r"cloudformation", r"helm", r"Dockerfile",
            r"docker-compose", r"iac/", r"infra/",
            # Kubernetes / Helm assets
            r"(?:^|/)Chart\.yaml$", r"(?:^|/)values(?:[^/]*)\.yaml$",
            r"(?:^|/)charts/", r"(?:^|/)k8s/", r"\.k8s\.", r"kubernetes/", r"manifests/",
        ],
    ),
    (
        "DB migrations",
        [
            r"alembic/", r"migrations/", r"flyway/", r"liquibase/",
            r"\.sql$", r"db/", r"database/",
        ],
    ),
    (
        "Skill definitions",
        [
            r"(?:^|/)SKILL\.md$",
        ],
    ),
]


def classify(files: list[str]) -> dict[str, list[str]]:
    triggered: dict[str, list[str]] = {}
    for section, patterns in SECTION_RULES:
        matched = [
            f for f in files
            if any(re.search(p, f, re.IGNORECASE) for p in patterns)
        ]
        if matched:
            triggered[section] = matched
    return triggered


def main() -> None:
    source = sys.argv[1] if len(sys.argv) > 1 else "-"
    if source == "-":
        files = [line.strip() for line in sys.stdin if line.strip()]
    else:
        files = Path(source).read_text().splitlines()
        files = [f.strip() for f in files if f.strip()]

    if not files:
        print("No files provided.", file=sys.stderr)
        sys.exit(1)

    triggered = classify(files)

    all_sections = [s for s, _ in SECTION_RULES]
    print("Sections to apply:")
    print(f"  [x] Standard review       (always)")
    for section in all_sections:
        if section in triggered:
            examples = triggered[section][:3]
            label = ", ".join(examples)
            if len(triggered[section]) > 3:
                label += f" (+{len(triggered[section]) - 3} more)"
            print(f"  [x] {section:<22} ({label})")
        else:
            print(f"  [ ] {section}")


if __name__ == "__main__":
    main()
