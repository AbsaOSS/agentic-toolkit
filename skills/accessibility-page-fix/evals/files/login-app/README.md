# login-app

A small customer portal (TypeScript + Vite, no framework). There is **no backend**: every `/api/*` request fails
when you run `npm run dev`, so signed-in pages can only be reached with mocked responses (for example Playwright
`page.route`).

```bash
npm install
npm run dev          # http://localhost:5173 (PORT=5174 npm run dev for a second copy)
npm run test:a11y    # axe scans (Playwright project `accessibility`)
npm run typecheck
npm run build
```

Runtime configuration is loaded at start-up from `public/config.json` (`apiUrl`, `sessionWarningSeconds`).

## Pages and requests

| Route | Needs sign-in | Requests |
|---|---|---|
| `/login` | no | `POST {apiUrl}/login` → `{ "token": string, "expiresIn": seconds }` (401 = wrong password) |
| `/home` | yes | none |
| `/account/settings` | yes | `GET {apiUrl}/settings`, `PUT {apiUrl}/settings` (body and reply: `displayName`, `email`, `language`, `emailNotifications`, `smsNotifications`); 401 sends the user to `/login` |

The session is kept in `sessionStorage` (`portal.session`). When it has `sessionWarningSeconds` or less left, a
"Please sign in again" dialog with the same sign-in form opens over the current page. A failed sign-in shows a
notification at the bottom right.

Accessibility tests live in `playwright/a11y/*.accessibility.spec.ts` and use the shared axe fixture in
`playwright/fixtures/axe-helpers.ts`.
