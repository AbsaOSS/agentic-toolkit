# catalogue-fragment

Plain TypeScript app (no framework) embedded as `<web-fragment fragment-id="catalogue">` inside the
workspace shell. The shell is an Angular app; it already sends telemetry to CloudWatch RUM with
ngx-ui-watchtower and hosts the broadcast channel. The shell's telemetry uses
`eventNamespace: 'com.workspace'`.
