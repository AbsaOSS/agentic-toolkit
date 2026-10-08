/**
 * This application's telemetry vocabulary.
 *
 * Scenario, step and business event names are metric dimensions, declared
 * once here rather than as free text at each call site. Once a registry has
 * an entry, a name not listed in it is a compile error.
 *
 * Keep a side-effect import of this file (`import './telemetry.schema';`)
 * where the telemetry providers are configured and in the router telemetry
 * service, so it can never become unreferenced.
 */
declare module '@absaoss-cps/ngx-ui-watchtower' {
  interface UwtScenarioNames {
    /** A router navigation, from click to activated route. */
    'route-navigation': true;

    // One entry per confirmed journey, kebab-case, with a line saying what it measures:
    // /** Loading the customer list, from request to first render. */
    // 'customers-load': true;
  }

  interface UwtScenarioSteps {
    /** From the recognized URL to activation: guards, resolvers, lazy components. */
    'resolve-route': true;

    /** Activating the routed component. */
    activate: true;

    // Steps and aggregates share this registry:
    // /** Fetching data from the API. */
    // fetch: true;
  }

  // Add once the first business event is confirmed (snake_case):
  // interface UwtBIEventNames {
  //   /** The user exported the current result set. */
  //   export_clicked: true;
  // }

  // Only when the app has a log backend (UWT_LOG_API_PROVIDER bound to a real provider):
  // interface UwtLoggerNames {
  //   /** Application lifecycle and routing. */
  //   app: true;
  // }
}

export {};
