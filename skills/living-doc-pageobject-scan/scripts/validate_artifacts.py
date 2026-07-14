#!/usr/bin/env python3
"""
validate_artifacts.py — BDD artifact validator (profile / seed / manifest)

Validates a Project Profile, Business Seed, or Exploration Manifest against the
canonical JSON Schemas in skills/shared/references/schemas/. This moves shape enforcement
out of the model and into a deterministic check, so re-runs are reproducible.

Usage:
    python validate_artifacts.py profile  .copilot/bdd/.project-profile.yaml
    python validate_artifacts.py seed      .copilot/bdd/seed.yaml
    python validate_artifacts.py manifest  .copilot/bdd/manifest.json
    python validate_artifacts.py manifest  manifest.json --canonicalize   # sort + rewrite for stable diffs
    python validate_artifacts.py manifest  manifest.json --json           # machine-readable output

Schema location is auto-detected relative to this script
(../../shared/references/schemas/) or overridden with --schema-dir.

Extra checks beyond the schema:
  * seed     — rejects inline credential literals (security gate).
  * manifest — --canonicalize sorts routes by url and elements/gaps by key, then
               rewrites with sorted JSON keys for deterministic, diff-friendly output.

Exit code 0 = valid (warnings allowed). Exit code 1 = errors. Exit code 2 = usage/IO error.
Requires: jsonschema, pyyaml (both present in the agent runtime).
"""

import argparse
import json
import re
import sys
from pathlib import Path

import yaml  # noqa: E402 — required dependency, imported early for error handling

ARTIFACT_SCHEMAS = {
    "profile": "project-profile.schema.json",
    "seed": "seed.schema.json",
    "manifest": "manifest.schema.json",
}

# Inline credential literals are a security violation in seed.yaml.
# Negative lookaheads allow safe patterns (env:, ${, <, ~, null) both quoted and unquoted.
CREDENTIAL_LEAK_RE = re.compile(
    r"^\s*(password|passwd|pwd|secret|token|api_?key|client_secret)\s*:\s*"
    r"(?![\"']?env:)(?![\"']?\$\{)(?![\"']?<)(?![\"']?~)(?!null\b)(?!\s*$)\S",
    re.IGNORECASE | re.MULTILINE,
)


def _default_schema_dir() -> Path:
    return (Path(__file__).resolve().parent / ".." / ".." / "shared" / "references" / "schemas").resolve()


def _load_document(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    if path.suffix in (".yaml", ".yml"):
        return yaml.safe_load(text)
    return json.loads(text)


def _schema_errors(document: dict, schema: dict) -> list[str]:
    from jsonschema import Draft7Validator  # noqa: PLC0415

    validator = Draft7Validator(schema)
    errors = []
    for err in sorted(validator.iter_errors(document), key=lambda e: list(e.path)):
        location = "/".join(str(p) for p in err.path) or "<root>"
        errors.append(f"{location}: {err.message}")
    return errors


def _seed_credential_errors(path: Path) -> list[str]:
    errors = []
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if CREDENTIAL_LEAK_RE.match(line):
            errors.append(
                f"line {lineno}: inline credential literal detected — reference via "
                f"credentials_source or env:VAR instead ({line.strip()[:60]})"
            )
    return errors


def _canonicalize_manifest(document: dict, path: Path) -> None:
    """Sort routes and their nested arrays deterministically and rewrite the file."""
    routes = document.get("routes", [])
    if isinstance(routes, list):
        for route in routes:
            if isinstance(route.get("elements"), list):
                route["elements"].sort(key=lambda e: str(e.get("data-cy", "")))
            if isinstance(route.get("coverage_gaps"), list):
                route["coverage_gaps"].sort(key=lambda g: str(g.get("suggestedDataCy", "")))
        routes.sort(key=lambda r: str(r.get("url", "")))
    path.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate a BDD artifact against its JSON Schema.")
    parser.add_argument("artifact", choices=sorted(ARTIFACT_SCHEMAS), help="Artifact kind to validate.")
    parser.add_argument("path", help="Path to the artifact file (YAML for profile/seed, JSON for manifest).")
    parser.add_argument("--schema-dir", help="Override the schema directory.")
    parser.add_argument(
        "--canonicalize",
        action="store_true",
        help="manifest only: sort routes/elements and rewrite with sorted keys for stable diffs.",
    )
    parser.add_argument("--json", action="store_true", help="Machine-readable JSON output.")
    args = parser.parse_args()

    doc_path = Path(args.path)
    if not doc_path.exists():
        print(f"Error: file not found: {doc_path}", file=sys.stderr)
        sys.exit(2)

    schema_dir = Path(args.schema_dir).resolve() if args.schema_dir else _default_schema_dir()
    schema_path = schema_dir / ARTIFACT_SCHEMAS[args.artifact]
    if not schema_path.exists():
        print(f"Error: schema not found: {schema_path}", file=sys.stderr)
        sys.exit(2)

    try:
        document = _load_document(doc_path)
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, yaml.YAMLError, OSError, ValueError) as exc:
        print(f"Error reading input: {exc}", file=sys.stderr)
        sys.exit(2)

    if document is None:
        print(f"Error: {doc_path} is empty or not a mapping", file=sys.stderr)
        sys.exit(1)

    errors = _schema_errors(document, schema)
    if args.artifact == "seed":
        errors.extend(_seed_credential_errors(doc_path))

    if args.artifact == "manifest" and args.canonicalize and not errors:
        _canonicalize_manifest(document, doc_path)

    valid = not errors
    if args.json:
        print(json.dumps({"artifact": args.artifact, "path": str(doc_path), "valid": valid, "errors": errors}, indent=2))
    elif valid:
        suffix = " (canonicalized)" if args.artifact == "manifest" and args.canonicalize else ""
        print(f"\u2705  {doc_path} is a valid {args.artifact}{suffix}.")
    else:
        print(f"\u274c  {doc_path} failed {args.artifact} validation ({len(errors)} error(s)):\n")
        for err in errors:
            print(f"  - {err}")

    sys.exit(0 if valid else 1)


if __name__ == "__main__":
    main()
