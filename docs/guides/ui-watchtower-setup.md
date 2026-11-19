# UI Watchtower Setup Skill

The `ui-watchtower-setup` skill installs and wires the UI Watchtower telemetry library in an
existing frontend app, then confirms that telemetry arrives, in the way you choose:

- **Angular apps** get the adapter,
  [`@absaoss-cps/ngx-ui-watchtower`](https://www.npmjs.com/package/@absaoss-cps/ngx-ui-watchtower)
  (providers and services).
- **Any other app** — any framework, or none — gets the framework-free core,
  [`@absaoss-cps/ui-watchtower`](https://www.npmjs.com/package/@absaoss-cps/ui-watchtower), created
  once in an engine module.

CloudWatch RUM is used as it comes, automatic page views included: the skill adds no routing code
unless you ask for it.

It is the first of two skills. Once the app is wired, use
[UI Watchtower Integration](./ui-watchtower-integration.md) to measure the app's own journeys and
interactions.

---

## What it does

| Step | Action |
|---|---|
| Detect | Reads the framework (Angular or not), package manager, SSR, test runner, existing RUM code, the app's role (standalone, micro-frontend shell, or fragment), and a few things the app does that could confirm the setup |
| Install | Adds the adapter (Angular) or the core (anything else), and `aws-rum-web` only where this app sends to RUM |
| Wire | Exactly one destination for the app's role; a credentials provider for RUM; a log provider only if the app has a log backend; an opaque user id on sign-in and sign-out |
| Vocabulary | Creates `telemetry.schema.ts` so names are compile-checked metric dimensions |
| Migrate | If the app already sends RUM events itself: inventory, keep wire parity, retire the old service only after comparing what reaches CloudWatch |
| Confirm | The way you chose: route-navigation tracking, kept; one or two small telemetry items from your app, kept; or a temporary check that is removed afterwards |
| Test & validate | Fixes specs that now need telemetry; build, unit tests, a real type-check, and a live check with the debug flags |
| Hand over | What was wired and how it was confirmed, what RUM stores in the browser, and the pointer to the integration skill; for a shell, the fragment contract |

---

## How to trigger it

```
add ui-watchtower to this app
add ngx-ui-watchtower to this Angular app
set up CloudWatch RUM with the watchtower library
replace our RumService with ui-watchtower
wire telemetry into our micro-frontend shell
our fragment should forward telemetry to the shell
```

---

## What you'll be asked

Only what the code can't answer, in one message:

- the `application` name and the name prefix;
- whether there is a log backend;
- the endpoint that returns RUM settings and short-lived AWS credentials — or that RUM isn't ready
  yet, in which case the app gets an explicit "ship nowhere" destination to swap later;
- if the app has sign-in but no obvious opaque user id, which one to use;
- **how to confirm the setup works:**
  1. route-navigation tracking, kept (only if the router has route templates; RUM then records page
     views under the route template instead of the URL);
  2. one or two simple telemetry items the skill suggests from your app — a main button, a form
     submit, a data load — kept;
  3. nothing permanent: the skill checks with temporary code and removes it.

With no answer, it uses option 3. If the library is already partly wired, only the missing pieces
are added.

---

## Requirements

- A browser app built from npm packages (a bundler or a framework CLI)
- For Angular, a version the adapter supports (the skill checks its `peerDependencies` on npm and
  stops rather than forcing an install)
- Access to the npm registry

---

## Out of scope

- Measuring the app's own journeys and interactions → [UI Watchtower Integration](./ui-watchtower-integration.md)
- CloudWatch dashboards, RUM extended metrics and alarms
- Fragment teams' own setup when your app is a shell — the skill hands you their contract
- Server-side and native mobile apps

---

## Installation

```bash
npx skills add https://github.com/AbsaOSS/agentic-toolkit -g --skill ui-watchtower-setup
# Companion: holds the ui-watchtower API references both watchtower skills load
npx skills add https://github.com/AbsaOSS/agentic-toolkit -g --skill shared
```

See [Getting Started](../getting-started.md) for the full install guide.
