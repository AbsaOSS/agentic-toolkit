# Copilot Instructions

## PR Review

When reviewing a pull request, load and apply:
https://github.com/AbsaOSS/agentic-toolkit/blob/master/skills/pr-review/SKILL.md

### Skill-specific checks — apply when any `SKILL.md` is modified

For every modified `SKILL.md`, also verify:
- `name` is kebab-case, matches the directory name, and is ≤ 64 chars
- `description` covers both "what it does" AND "when to trigger" with explicit trigger keywords
- `description` is ≤ 1024 chars and not padded with filler
- SKILL.md body is < 500 lines, or uses progressive disclosure via `references/`
- No hardcoded credentials, secrets, or absolute internal paths in skill body or scripts
- Any bundled script in `scripts/` is referenced from SKILL.md with clear usage guidance
- The new or modified skill's description does not conflict with or shadow existing skills
