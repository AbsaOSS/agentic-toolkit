# React

On top of `core.md`, which has the install, the engine module, the tracker module and the tests.
This file says where things go in a React app and how to bind React Router.

## Where things go

- `src/telemetry/telemetry.ts` (the engine) is imported first in `src/main.tsx`, before
  `createRoot(...)`. It is a module, not a component, a hook or a context value — so StrictMode's
  double rendering and effects never create a second engine.
- Instrumenting components (scenarios in effects, BI events in handlers) is
  `ui-watchtower-integration`'s job; setup adds only the route proof.

## React Router

Find which API the app uses (Step 1):

| The app uses | Binding, from `assets/route-navigation.react.ts` |
|---|---|
| A data router: `createBrowserRouter` / `createHashRouter` + `<RouterProvider>` | `bindDataRouter(router, navigationTracker)` |
| A declarative router: `<BrowserRouter>` / `<HashRouter>` + `<Routes>` or `useRoutes` | `useRouteNavigationTelemetry(navigationTracker, routes)` |
| React Router's framework mode, Next.js, Remix, TanStack Router, no router | Not covered by a template: `core.md`, "Other routers" |

Copy `assets/route-navigation-tracker.ts` and `assets/route-navigation.react.ts` (and their specs)
next to the schema. The binding is written for React Router 7 (`'react-router'`); with React
Router 6, import from `'react-router-dom'` in the binding and its spec, and let the spec confirm
it.

**Data router** — bind right after creating the router, before `<RouterProvider>` renders, so the
initial navigation counts. A loader or action redirect stays one scenario, under the final
template:

```tsx
// the app's router module
import { createBrowserRouter } from 'react-router';
import { bindDataRouter } from './telemetry/route-navigation.react';
import { navigationTracker } from './telemetry/route-navigation';

export const router = createBrowserRouter(routes);
bindDataRouter(router, navigationTracker);
```

**Declarative router** — call the hook once, in a component rendered inside the router (the
`App` that holds `<Routes>`). It has no navigation events, so a navigation is recorded when its
location renders; its duration runs from the click only where a handler called
`navigationTracker.markIntent()`, otherwise it is about zero and the scenario only counts
navigations — say so in the hand-over. It needs the route objects for templates:

- An app using `useRoutes(routes)` passes the same `routes`.
- An app writing `<Routes>` JSX: move the `<Route>` elements into one constant, render it inside
  `<Routes>`, and pass `createRoutesFromElements(thatConstant)` (from `react-router`) to the hook,
  so there is still one route table.
- Nested `<Routes>` in descendant components: the template ends at the parent's `/*`
  (`/settings/*`). Acceptable; note it in the hand-over.

**Click intent** (either router) — to start the clock at the click rather than at the router's
start, call `navigationTracker.markIntent()` first in click handlers that navigate:
`<Link onClick={() => navigationTracker.markIntent()}>`, or before `navigate(...)` in a handler
that does work first.

## Tests

The binding's spec, `route-navigation.react.spec.ts`, uses `createMemoryRouter` and runs in
jsdom (it selects it itself; install `jsdom` as a dev dependency if the app has none). Add the
app's own route shapes to its route table. Component specs that render the app's router module get
the test engine from the setup mock in `core.md`, Step 7.
