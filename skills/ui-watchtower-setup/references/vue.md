# Vue

On top of `core.md`, which has the install, the engine module, the tracker module and the tests.
This file says where things go in a Vue 3 app and how to bind Vue Router 4.

## Where things go

- `src/telemetry/telemetry.ts` (the engine) is imported first in `src/main.ts`, before
  `createApp(App)`. It is a module, not a plugin, a `provide()` value or a composable — so it
  exists before the app mounts and is never created twice.
- Instrumenting components (scenarios in composables, BI events in handlers) is
  `ui-watchtower-integration`'s job; setup adds only the route proof.
- Nuxt, Vue 2 / Vue Router 3, or no router: not covered by a template — `core.md`, "Other
  routers".

## Vue Router

Copy `assets/route-navigation-tracker.ts` and `assets/route-navigation.vue.ts` (and their specs)
next to the schema. Bind right after `createRouter(...)`, before `app.use(router)` starts the
initial navigation:

```ts
// the app's router module, e.g. src/router/index.ts
import { createRouter, createWebHistory } from 'vue-router';
import { bindVueRouter } from '../telemetry/route-navigation.vue';
import { navigationTracker } from '../telemetry/route-navigation';

export const router = createRouter({ history: createWebHistory(), routes });
bindVueRouter(router, navigationTracker);
```

The template is the matched record's full path (`/customers/:id`, nested paths already joined).
A guard that returns another location stays one scenario, under the final template; a guard that
returns `false` is `incomplete`; a navigation replaced by a newer one is `abandoned`.

**Click intent** — to start the clock at the click rather than at the router's start, call
`navigationTracker.markIntent()` first in click handlers that navigate:
`<RouterLink to="/orders" @click="navigationTracker.markIntent()">`, or before `router.push(...)`
in a handler that does work first.

## Tests

The binding's spec, `route-navigation.vue.spec.ts`, uses `createMemoryHistory` and needs no DOM.
Add the app's own route shapes to its routes. A spec that imports the app's own router module
needs jsdom, for `createWebHistory`. Component specs get the test engine from the setup mock in
`core.md`, Step 7.
