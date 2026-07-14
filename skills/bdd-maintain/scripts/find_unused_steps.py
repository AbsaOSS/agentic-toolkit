#!/usr/bin/env python3
"""
find_unused_steps.py — Dead-code detector: step definitions unused in any .feature file.

Usage:
    python playwright/scripts/find_unused_steps.py [--steps-dir DIR] [--features-dir DIR]

Exits with code 1 if any unused steps are found (useful in CI).
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# Patterns
# ---------------------------------------------------------------------------

# Matches: Given('pattern', ...) / When(`pattern`, ...) / Then("pattern", ...)
# playwright-bdd uses Given/When/Then imported from cucumber or createBdd
STEP_DEF_RE = re.compile(
    r"""(?:Given|When|Then|And|But)\s*\(\s*(['"`])(.*?)\1""",
    re.DOTALL,
)

# Playwright-bdd also supports: @Given('pattern')  @When('pattern')  @Then('pattern')
DECORATOR_RE = re.compile(
    r"""@(?:Given|When|Then|And|But)\s*\(\s*(['"`])(.*?)\1""",
    re.DOTALL,
)

# Convert a Cucumber expression / simple regex pattern to a Python regex
# Cucumber expression placeholders: {string}, {int}, {word}, {float}


@dataclass
class StepDefinition:
    pattern: str          # raw pattern string from source
    file: Path
    line: int
    regex: re.Pattern     # compiled regex for matching


def cucumber_to_regex(pattern: str) -> re.Pattern:
    """Convert a Cucumber expression pattern to a Python compiled regex."""
    # Escape the pattern, then replace escaped Cucumber placeholders with non-greedy wildcard
    escaped = re.escape(pattern)
    escaped = re.sub(r"\\{(?:string|int|word|float|[^}]+)\\}", r".+?", escaped)
    return re.compile(rf"^\s*{escaped}\s*$", re.IGNORECASE)


def collect_step_definitions(steps_dir: Path) -> list[StepDefinition]:
    defs: list[StepDefinition] = []
    for ts_file in sorted(steps_dir.rglob("*.steps.ts")):
        text = ts_file.read_text(encoding="utf-8")
        for pattern_re in (STEP_DEF_RE, DECORATOR_RE):
            for m in pattern_re.finditer(text):
                raw_pattern = m.group(2)
                line = text[: m.start()].count("\n") + 1
                try:
                    compiled = cucumber_to_regex(raw_pattern)
                    defs.append(StepDefinition(raw_pattern, ts_file, line, compiled))
                except re.error:
                    print(f"  WARN: could not compile pattern at {ts_file}:{line}: {raw_pattern!r}",
                          file=sys.stderr)
    return defs


def collect_feature_steps(features_dir: Path) -> list[str]:
    """Return every step line from every .feature file (stripped of keyword)."""
    step_line_re = re.compile(
        r"^\s*(?:Given|When|Then|And|But)\s+(.+)$", re.IGNORECASE
    )
    steps: list[str] = []
    for feat_file in sorted(features_dir.rglob("*.feature")):
        for line in feat_file.read_text(encoding="utf-8").splitlines():
            m = step_line_re.match(line)
            if m:
                steps.append(m.group(1).strip())
    return steps


def main() -> int:
    parser = argparse.ArgumentParser(description="Find unused Playwright-BDD step definitions.")
    parser.add_argument(
        "--steps-dir",
        default="playwright/steps",
        help="Directory containing *.steps.ts files (default: playwright/steps)",
    )
    parser.add_argument(
        "--features-dir",
        default="playwright/features",
        help="Directory containing *.feature files (default: playwright/features)",
    )
    args = parser.parse_args()

    steps_dir = Path(args.steps_dir)
    features_dir = Path(args.features_dir)

    if not steps_dir.is_dir():
        print(f"ERROR: steps-dir not found: {steps_dir}", file=sys.stderr)
        return 2
    if not features_dir.is_dir():
        print(f"ERROR: features-dir not found: {features_dir}", file=sys.stderr)
        return 2

    print(f"Scanning step definitions in:  {steps_dir}")
    print(f"Scanning feature steps in:     {features_dir}")
    print()

    step_defs = collect_step_definitions(steps_dir)
    feature_steps = collect_feature_steps(features_dir)

    print(f"Found {len(step_defs)} step definition(s) across {steps_dir}")
    print(f"Found {len(feature_steps)} step usage(s) across {features_dir}")
    print()

    unused: list[StepDefinition] = []
    for sd in step_defs:
        matched = any(sd.regex.match(fs) for fs in feature_steps)
        if not matched:
            unused.append(sd)

    if not unused:
        print("✅  All step definitions are used.")
        return 0

    print(f"⚠️  {len(unused)} UNUSED step definition(s) found:\n")
    by_file: dict[Path, list[StepDefinition]] = {}
    for sd in unused:
        by_file.setdefault(sd.file, []).append(sd)

    for file, sds in sorted(by_file.items()):
        print(f"  {file}")
        for sd in sorted(sds, key=lambda s: s.line):
            print(f"    line {sd.line:4d}  {sd.pattern!r}")
    print()
    return 1


if __name__ == "__main__":
    sys.exit(main())
