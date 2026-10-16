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

| Call site | AWS API | Event type | Payload keys | Consumers (dashboard, metric, query) | Parity tool (§2) |
|-----------|---------|------------|--------------|--------------------------------------|------------------|
|           |         |            |              |                                      |                  |

Also note how the existing code obtains credentials (Cognito identity pool vs a backend broker), how
it handles sign-in/sign-out, and whether it records page views manually.

**Fix live privacy leaks now, even if the migration is blocked.** Raw search text, an email as user
id, page ids with query strings: fix them in the old code right away (debounce and send
`queryLength`, an opaque id, strip query strings), mark the rows, and tell the dashboard owners.
Parity never outranks personal data.
Put each comment on its own line above the code it explains, and re-read every line you edited in
the old service when you are done: you cannot compile here, and a trailing `// …` before a closing
`);` silently swallows the bracket and breaks the only page-view path.

## 2. Pick a parity tool per row

Choose exactly one tool for every row and write it in the last column of the §1 table. A list of
options is not a choice: without one, the cutover has no agreed target and the wire diff (§5) has
nothing to compare against, even when the cutover itself has to wait for a broker.

| Tool                                                   | Use when                                                         | Result                                                                                                     |
|--------------------------------------------------------|------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------|
| `eventNamespace` in the identity                       | Existing types differ from the library's only by prefix          | `eventNamespace: 'myapp'` → `myapp.scenario`, `myapp.scenario.step`, `myapp.bi`. Cheapest                  |
| `track(name, metadata, { eventType: 'legacy.type' })`  | A dashboard needs one specific event type                        | Exact event type; payload becomes the `UwtBIEvent` envelope (`eventName`, `eventTime`, `metadata`, `application`, …). A migration escape hatch, not a pattern |
| `sink.record(eventType, payload)` (sink injected as a field) | Byte-exact payload parity is required | Raw passthrough, no redaction — never forward free text (an error becomes its name or code). Use sparingly |

If a consumer can be updated instead (a query, a metric filter), prefer moving it to the library's
event types — record that decision in the table.

## 3. Credentials

- A backend broker → wrap it in `assets/rum-credentials.provider.ts`; keep the endpoint.
- A Cognito identity pool (`identityPoolId`, `guestRoleArn`) → not supported by the library's config
  on purpose. Credentials must come from a broker that returns short-lived AWS credentials. If none
  exists, stop and tell the user: a broker is a backend change, outside this skill.

## 4. Cut over without ever running two RUM clients

Two `AwsRum` instances mean two sessions per visitor, so the old client and
`provideUwtTelemetryRumSink()` must never start in the same build. Until the cutover, the old
`RumService` stays the **only** RUM client (the library can already be wired with `'noop'`, so the
vocabulary, route tracking and tests are in place). The cutover is one change, in this order:

1. **Stop the old client** — remove whatever runs `RumService.init()` / `new AwsRum` (usually an
   `APP_INITIALIZER`), and its page-view subscription.
2. **Wire the new destination** — replace `'noop'` with `provideUwtTelemetryRumSink()`, the
   credentials provider and the page-view recorder.
3. **Turn the old service into an adapter** — inject `UwtTelemetrySink` (and the BI / scenario
   services) as fields, and point each remaining method at the library: the migrated call, or
   `this.sink.record(…)` for rows that need byte parity. Then move call sites to the library one at
   a time. The class stays, without any `AwsRum` of its own, as the reference for §5 until every row
   is ticked.

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

- **Page views.** Setup records one page view per navigation under the route template
  (`disableAutoPageView: true` plus the route service's page-view recorder — Step 6). Drop any
  manual `recordPageView` calls in the old code; never keep both. If the old setup relied on
  automatic page views, its page ids were resolved paths (`/customers/42`) and become templates
  (`/customers/:id`) — tell the owners of page-based dashboards.
- **Session attributes.** `application`, `environment` and `version` from the identity are attached
  as session attributes. Port any other attributes via `sessionAttributes` in the app monitor config
  returned by the credentials provider.
- **User identity.** Replace `pinUserId` with `setUserId` (SKILL.md Step 3). Sign-out starts a fresh
  session; call it out if the old code behaved differently.
- **Errors.** The RUM client still captures unhandled JS errors itself. Handled errors the old code
  sent with `recordError` become `scenario.fail(...)` (never a raw `HttpErrorResponse` — see the
  integration patterns' `safeHttpFailure`), or a log line with
  `withLogging({ mirrorErrorsToRum: true })` when the app has a log backend.
