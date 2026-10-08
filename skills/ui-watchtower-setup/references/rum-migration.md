# Migrating an existing RUM integration

Use when the app already calls `aws-rum-web` itself (a `RumService`, a wrapper around `AwsRum`).
The library emits its own event types (`com.uwt.scenario`, `com.uwt.scenario.step`, `com.uwt.bi`)
with its own payload shapes. Event types are a contract with whatever already queries them —
extended metrics, Logs Insights queries, dashboards — so a naive "delete RumService, call
`track()` instead" silently breaks them. **Migrate first, diff the wire, delete last.**

## 1. Inventory — before changing anything

```bash
rg -n "recordEvent|recordError|recordPageView|dispatch|pinUserId|addSessionAttributes|new AwsRum" src/
```

Build this table and keep it in the PR description. The payload column matters — the event type
alone is not parity:

| Call site | AWS API | Event type | Payload keys | Consumers (dashboard, metric, query) |
|-----------|---------|------------|--------------|--------------------------------------|
|           |         |            |              |                                      |

Also note how the existing code obtains credentials (Cognito identity pool vs a backend broker), how
it handles sign-in/sign-out, and whether it records page views manually.

## 2. Pick a parity tool per row

| Tool                                                   | Use when                                                         | Result                                                                                                     |
|--------------------------------------------------------|------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------|
| `eventNamespace` in the identity                       | Existing types differ from the library's only by prefix          | `eventNamespace: 'myapp'` → `myapp.scenario`, `myapp.scenario.step`, `myapp.bi`. Cheapest                  |
| `track(name, metadata, { eventType: 'legacy.type' })`  | A dashboard needs one specific event type                        | Exact event type; payload becomes the `UwtBIEvent` envelope (`eventName`, `eventTime`, `metadata`, `application`, …). A migration escape hatch, not a pattern |
| `inject(UwtTelemetrySink).record(eventType, payload)`  | Byte-exact payload parity is required                            | Raw passthrough — you own the shape. Use sparingly and comment why                                         |

If a consumer can be updated instead (a query, a metric filter), prefer moving it to the library's
event types — record that decision in the table.

## 3. Credentials

- A backend broker → wrap it in `assets/rum-credentials.provider.ts`; keep the endpoint.
- A Cognito identity pool (`identityPoolId`, `guestRoleArn`) → not supported by the library's config
  on purpose. Credentials must come from a broker that returns short-lived AWS credentials. If none
  exists, stop and tell the user: a broker is a backend change, outside this skill.

## 4. Migrate with both paths alive

Move call sites one at a time. Keep `RumService` until the last row is migrated. Do not run two RUM
clients at once: once `provideUwtTelemetryRumSink()` is wired, the old service's remaining calls
should go through the library's sink (`inject(UwtTelemetrySink).record(...)`) or be migrated — two
`AwsRum` instances would mean two sessions per visitor.

## 5. Diff the wire

Enable `debugScenario` and `debugBI`, drive each migrated path, and compare the console output (its
second argument is the exact object handed to the sink) against the inventory. Tick each row only
when type and payload match what its consumers need.

## 6. Delete

Only when every row is ticked: delete `RumService`, its providers and its tests; remove any direct
`aws-rum-web` imports outside the library.

Ticking rows needs the app running in a browser. If you can't run it in this session (no install,
no browser), **don't delete**: stop initialising the old service (so there is never a second RUM
client), leave its file in place, and hand over "diff the wire, then delete `RumService`" as an
explicit follow-up with the inventory table attached. Deleting first throws away the reference the
diff needs.

## Specific checks

- **Page views.** The RUM client records a page view on every `history.pushState`, which covers the
  Angular router. If the old code recorded page views manually, drop that code — or keep it via
  `UwtRumTelemetrySink.recordPageView(template)` **and** set `disableAutoPageView: true` in the app
  monitor config. Never both. If routes carry ids, the automatic page id (with `pageIdFormat:
  'PATH'`) is the resolved path — a cardinality and PII problem; record templates manually instead.
- **Free-text and per-keystroke events** (a search box sending every keystroke): debounce them, and
  don't port the raw text — it is unbounded cardinality and can contain personal data. Send a
  low-cardinality attribute instead (query length, result count, which filter was used). If a
  documented consumer genuinely needs the text, ask before porting it.
- **`aws:` metadata keys** are reserved and dropped by the RUM client; the sink filters them out. Any
  the old code set were already being dropped — don't port them.
- **Session attributes.** `application`, `environment` and `version` from the identity are attached
  as session attributes. Port any other attributes via `sessionAttributes` in the app monitor config
  returned by the credentials provider.
- **User identity.** Replace `pinUserId` with `inject(UwtTelemetrySink).setUserId(id)` /
  `setUserId(undefined)`. Sign-out starts a fresh session with a new anonymous id; if the old code
  behaved differently, call out the change.
- **Errors.** The RUM client still captures unhandled JS errors itself. Handled errors the old code
  sent with `recordError` become `scenario.fail({ error })`, or a log line with
  `withLogging({ mirrorErrorsToRum: true })` when the app has a log backend.
