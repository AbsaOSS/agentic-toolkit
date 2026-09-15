# Copilot Instructions

## Always Active

The **token-saving** skill is always active in this workspace. Every response applies concise formatting rules and removes noise (no filler, no closing platitudes, structured output). 

See [Token-Saving Skill](../docs/guides/token-saving.md) for details, including override behavior when you explicitly request depth.

---

## BDD Artifacts

When working with living documentation and BDD automation, use these standard artifact locations:
- **Business Seed:** `.copilot/bdd/seed.yaml` — App configuration, routes, test users, form fixtures
- **Exploration Manifest:** `.copilot/bdd/manifest.json` — Discovered surfaces, PageObject paths, UI elements
- **Project Profile:** `.copilot/bdd/.project-profile.yaml` — BDD conventions for this project
- **Feature Files (User Story):** `features/liv_doc_us/` — E2E scenarios linked to User Stories
- **Feature Files (Functionality):** `features/liv_doc_func/` — System-test scenarios linked to Functionalities
- **PageObjects:** `playwright/pages/` — Locators and page interaction methods
- **Step Definitions:** `playwright/steps/` — Gherkin step implementations
- **Living Doc Catalog:** `docs/living-doc/` — User Stories, Features, Functionalities, and Acceptance Criteria

These paths are configurable in `.copilot/bdd/.project-profile.yaml`.

---

## PR Review

When reviewing a pull request, load and apply:
https://github.com/AbsaOSS/agentic-toolkit/blob/master/skills/pr-review/SKILL.md
