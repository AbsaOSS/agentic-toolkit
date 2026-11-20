# sample-page

A single static page ("Orders") with typical accessibility problems. Vite serves it at `/` and, as a single-page
app fallback, at any route such as `/orders`.

```bash
npm install
npm run dev          # http://localhost:5173 (PORT=5174 npm run dev for a second copy)
npm run test:a11y    # axe scans (Playwright project `accessibility`)
npm run typecheck
npm run build
```

Accessibility tests live in `playwright/a11y/*.accessibility.spec.ts` and use the shared axe fixture in
`playwright/fixtures/axe-helpers.ts` (WCAG 2.2 AA tags). `example.accessibility.spec.ts` is a dummy scan that proves
the setup works.

## States

- default
- status message shown ("Saved", always visible)
- card actions (⋮) clicked: no menu opens yet (the handlers are stubs)
