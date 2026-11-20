# shell-app ("Workbench")

A small web app (TypeScript + Vite, no framework) with an app shell: a fixed top bar, a fixed left sidebar, and
pages that scroll inside the content area. `src/ui-kit/` is the app's design system (tokens, global styles, menu,
dropdown, dialog, toasts, paginator, live announcer, focus and root-font-size helpers); import it from
`src/ui-kit/index.ts`.

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

## Data

Reads come from static JSON in `public/api/` (a stand-in backend). Writes (`PUT`, `POST`, `DELETE`) have no backend
in development and fail with 404; tests mock them. `src/api.ts` sends every 401 or 403 to the shared error page
(`/error`); other failures are handled by each page.

## Pages

| Route | Content | Requests |
|---|---|---|
| `/home` | Summary cards (each with a menu button), recent activity | `GET /api/activity.json` |
| `/projects` | Search box, sort dropdown, "New project", project cards (version dropdown, "More actions" menu: Rename, Delete), sticky paginator (12 per page) | `GET /api/projects.json`, `GET /api/versions.json` (on failure the version dropdowns show "N/A"), Rename dialog: `GET /api/project-names.json?q=` (similar names), `PUT /api/projects/:id`; Delete: `DELETE /api/projects/:id` |
| `/reports` | Filter chips, "Add filter" dialog, "Export" dialog (two steps: format, then template file), reports table with a menu per row. `/reports?view=readonly` hides the Export button | `GET /api/reports.json`, `POST /api/reports/export` |
| `/pricing` | Hero banner with a gradient, three plans | none |
| `/support/new` | Subject, a rich text editor (Quill) for the message, Send | none |
| `/error` | Shared error page | none |

The shared menu button (`createMenuButton`) is used on `/home`, `/projects`, `/reports` and in the top bar's user
menu.
