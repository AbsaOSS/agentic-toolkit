# wired-checkout-angular

A small web shop that is already wired for `@absaoss-cps/ngx-ui-watchtower` (setup is done: providers, RUM
destination, route-navigation tracking, typed names file) but has **no scenario or BI instrumentation of its
own**. Three components in separate files make HTTP calls: the cart (loads the cart, applies a coupon), the
order summary (places the order) and a static confirmation page.

Used by the `no-merged-telemetry-wrapper` eval of `ui-watchtower-integration`: several call sites that need
telemetry make a shared telemetry service tempting; the skill must use the scenario and BI services directly
where they are needed.
