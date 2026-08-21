# Fixture Map — living-doc-pageobject-scan

## Fixture files

No fixture files for this skill. All evals are conversational or reference live webapp URLs.

## Eval to fixture mapping

| Eval ID | Category | Fixture file(s) | Coverage |
|---|---|---|---|
| 1 | happy-path | _(none — URL-based Create mode)_ | Bootstrap CheckoutPage from /checkout: elements, selectors, Feature link |
| 2 | happy-path | _(none)_ | Fragile positional selector: FRAGILE comment + data-testid recommendation |
| 3 | happy-path | _(none)_ | Maintain mode: renamed data-testid selector → BREAKING CHANGE report |
| 4 | regression | _(none)_ | Maintain mode: removed element → BREAKING comment, never auto-delete method |
| 5 | negative | _(none)_ | Routing: BDD scenario generation → living-doc-scenario-creator |
| 6 | paraphrase | _(none)_ | "Playwright tests failing after redesign" → Maintain mode |
| 7 | edge-case | _(none)_ | API endpoint: PageObjects are for UI only → living-doc-create-functionality |
| 8 | output-format | _(none)_ | Python CheckoutPage skeleton: ALL_CAPS constants, method stubs, living-doc header |
| 9 | happy-path | _(none)_ | Create mode Step 5: Functionality stubs from discovered behaviors |
| 10 | output-format | _(none)_ | TypeScript CheckoutPage: readonly Locators, async methods, living-doc header |
| 11 | edge-case | _(none)_ | Maintain mode: multi-step auth route — navigation_context string with sequential steps |

## Trigger eval summary

18 entries: 14 `should_trigger=true`, 4 `should_trigger=false`

| Routes to | Query count |
|---|---|
| living-doc-create-user-story | 1 |
| living-doc-scenario-creator | 1 |
| living-doc-update | 1 |
| living-doc-create-functionality | 1 (API endpoint redirect) |
