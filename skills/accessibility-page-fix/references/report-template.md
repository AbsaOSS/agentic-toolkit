# Report template

Finish every run with a report in this shape. Keep it short and factual; use plain words. Don't claim the page is
"fully compliant" — say what was tested.

```markdown
## Accessibility fixes: <page name / route>

**Standard:** WCAG 2.2 AA · **States tested:** <default, menu open, error, …>

### Result
- axe: <N> violations before → <N> after (all states) · <N> incomplete resolved, <N> still open
- Keyboard walk: <pass / issues remaining>
- Text size 200% and 320 px reflow: <pass / issues remaining>
- Screen reader: <tool used / not tested>

### Fixed
| Problem | WCAG | Fix | Where |
|---|---|---|---|
| <what users experienced> | 4.1.2 | <what changed> | <file(s)> |

### Shared code changed
| Item | Other places that use it | How checked |
|---|---|---|

### Visual changes
- <intended changes users will notice, e.g. darker arrow color>

### Not fixed / needs a decision
| Issue | Why | Owner / next step |
|---|---|---|

### Observations (not failures)
- <e.g. submit button disabled until the form is valid; left as is because changing it alters behaviour>

### Tests added or changed
- <scans per state, keyboard or text-size tests, unit tests>
- Fail-before / pass-after: <confirmed by reverting the fix, new tests failed; restored, they pass>

### How to verify
<commands to run, plus 3-5 manual steps>
```

Guidance:

- Describe problems by **user impact** ("keyboard users could not open the menu"), not only rule ids.
- List every shared component, style or helper you touched, and the other pages you checked.
- Anything that is still `incomplete` or only checked by hand goes in "Not fixed / needs a decision" with the reason.
- Be honest about what you could not test (no screen reader, no mobile device, a state you could not reach).
