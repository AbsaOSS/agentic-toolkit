# UI Watchtower Setup Skill

The `ui-watchtower-setup` skill installs and wires
[`@absaoss-cps/ngx-ui-watchtower`](https://www.npmjs.com/package/@absaoss-cps/ngx-ui-watchtower) — a
telemetry library for Angular apps — in an existing application, and proves the pipeline works with
one real scenario: route-navigation tracking.

It is the first of two skills. Once the app is wired, use
[UI Watchtower Integration](./ui-watchtower-integration.md) to measure the app's own journeys and
interactions.

---

## What it does

| Step | Action |
|---|---|
| Detect | Reads Angular version, bootstrap style, SSR, package manager, test runner, existing RUM code, and the app's role (standalone, micro-frontend shell, or fragment) |
| Install | Adds the package (and `aws-rum-web` only where this app sends to RUM) |
| Wire | Registers exactly one destination for the app's role; a credentials provider for RUM; a log provider only if the app has a log backend; an opaque user id on sign-in and sign-out |
| Vocabulary | Creates `telemetry.schema.ts` so names are compile-checked metric dimensions |
| Migrate | If the app already sends RUM events itself: inventory, keep wire parity, retire the old service only after comparing what reaches CloudWatch |
| Prove | Adds route-navigation tracking with a test, and RUM page views — both under the route template (`/customers/:id`), never the resolved URL |
| Test & validate | Fixes specs that now need telemetry providers; build, unit tests, a real type-check, and a live check with the debug flags |
| Hand over | Points to the integration skill; for a shell, hands over the fragment contract |

---

## How to trigger it

```
add ngx-ui-watchtower to this Angular app
set up CloudWatch RUM with the watchtower library
replace our RumService with ngx-ui-watchtower
wire telemetry into our micro-frontend shell
our fragment should forward telemetry to the shell
```

---

## What you'll be asked

Only what the code can't answer: the `application` name to report, whether there is a log backend,
the endpoint that returns RUM settings and short-lived AWS credentials — or that RUM isn't ready
yet, in which case the app is wired with an explicit "ship nowhere" destination to swap later — and,
if the app has sign-in but no obvious opaque user id, which one to use.

If the library is already partly wired, only the missing pieces are added.

---

## Requirements

- An Angular version the library supports (the skill checks its `peerDependencies` on npm and stops
  rather than forcing an install)
- A Node.js version your Angular version supports
- Access to the npm registry

---

## Out of scope

- Measuring the app's own journeys and interactions → [UI Watchtower Integration](./ui-watchtower-integration.md)
- CloudWatch dashboards, RUM extended metrics and alarms
- Fragment teams' own setup when your app is a shell — the skill hands you their contract
- Non-Angular applications

---

## Installation

```bash
npx skills add https://github.com/AbsaOSS/agentic-toolkit -g --skill ui-watchtower-setup
# Companion: holds the ngx-ui-watchtower API reference both watchtower skills load
npx skills add https://github.com/AbsaOSS/agentic-toolkit -g --skill shared
```

See [Getting Started](../getting-started.md) for the full install guide.
