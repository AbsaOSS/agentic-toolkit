#!/usr/bin/env python3
"""
ac_tag.py — Canonical @AC: Cucumber tag grammar (shared library)

Single source of truth for what counts as a valid @AC: tag in living-doc feature
files, and for walking the consecutive tag lines immediately above a Scenario line.
Used by scan_ac_links.py (traceability validation) and coverage_report.py (coverage
computation) so the two tools cannot drift apart on tag validity again — previously
coverage_report.py accepted FEAT and slug-parent tags (@AC:FEAT-checkout-page-01)
that scan_ac_links.py rejected as malformed, so the same tag was "covered" in one
tool and "malformed" in the other.

Canonical grammar (skills/shared/references/living-doc-glossary.md):
  AC:<PARENT>-<nn>, where <PARENT> is US-<n> or FUNC-<nnn> — numeric only, no slugs,
  no FEAT (Features own Functionalities, not ACs directly). <nn> is a two-digit
  sequence number, not required to be pre-zero-padded.

Functions:
  - match_ac_tag(token: str) -> re.Match | None
    Full-string match of a single whitespace-free @AC:... token.
  - iter_ac_tags(text: str) -> Iterator[re.Match]
    Find all @AC:... tag occurrences anywhere in text (e.g. a full line).
  - get_tag_lines_above(lines: list[str], scenario_index: int) -> list[str]
    Consecutive Cucumber tag lines immediately above a scenario, closest first.
  - canonicalize_ac_id(ac_id: str) -> str
    Zero-pad the numeric parent to 3 digits: US-1-01 -> US-001-01. Returns the
    input unchanged if it isn't a US|FUNC canonical AC ID.

Constants:
  - AC_TAG_PATTERN — the "@AC:..." Cucumber tag form (with optional /param:value segments)
  - AC_ID_PATTERN — the bare "AC:..." form, for validating an AC's own "id" field in
    entity JSON (e.g. validate_entity.py), as opposed to a Cucumber tag token
"""

import re

# (?!\d) prevents a trailing digit from being silently dropped — @AC:US-1-011 must
# not match as @AC:US-1-01 — for both match() and finditer() callers, since finditer
# scans a whole line (multiple tags may share it) and has no line-level $ anchor to
# lean on the way a single-token match() does.
_AC_ID_CORE = r"(?:US|FUNC)-\d+-\d{2}(?!\d)"
_AC_PARAMS = r"(?:/[a-z][\w-]*:[^\s/@]+)*"
AC_TAG_PATTERN = re.compile(rf"@AC:({_AC_ID_CORE})({_AC_PARAMS})", re.IGNORECASE)

# Bare "AC:US-001-01" form (no leading "@", no /param segments) — for validating an
# AC's own "id" field in entity JSON (e.g. living-doc-update's validate_entity.py),
# as opposed to AC_TAG_PATTERN which matches a Cucumber tag token in a feature file.
AC_ID_PATTERN = re.compile(rf"^AC:{_AC_ID_CORE}$", re.IGNORECASE)

# Matches any Cucumber tag line (used to find the consecutive tag-line block above a
# Scenario — not specific to @AC: tags, since other tags like @Regression may share it).
TAG_LINE = re.compile(r"^\s*@\S+")


def match_ac_tag(token: str) -> re.Match | None:
    """Full-string match of a single whitespace-free @AC:... token.
    Fails (returns None) on any trailing content the grammar doesn't account for,
    e.g. a malformed @AC:US-1-011 or @AC:US-1-01x."""
    return AC_TAG_PATTERN.fullmatch(token)


def iter_ac_tags(text: str):
    """Yield every @AC:... tag occurrence found anywhere in text (e.g. a full line
    that may carry multiple tags)."""
    return AC_TAG_PATTERN.finditer(text)


def get_tag_lines_above(lines: list[str], scenario_index: int) -> list[str]:
    """Return consecutive Cucumber tag lines immediately above a scenario, closest first."""
    tag_lines: list[str] = []
    i = scenario_index - 1
    while i >= 0 and TAG_LINE.match(lines[i]):
        tag_lines.append(lines[i])
        i -= 1
    return tag_lines


def canonicalize_ac_id(ac_id: str) -> str:
    """Zero-pad the numeric parent to 3 digits: US-1-01 -> US-001-01, FUNC-2-03 -> FUNC-002-03.
    Returns the input unchanged if it doesn't match the canonical US|FUNC AC-ID grammar
    (e.g. a stray FEAT-prefixed or slug-parent ID) rather than guessing at a normal form."""
    m = re.match(r"^(US|FUNC)-(\d+)-(\d{2})$", ac_id.strip(), re.IGNORECASE)
    if not m:
        return ac_id
    parent_type, num, seq = m.group(1).upper(), m.group(2), m.group(3)
    return f"{parent_type}-{num.zfill(3)}-{seq}"
