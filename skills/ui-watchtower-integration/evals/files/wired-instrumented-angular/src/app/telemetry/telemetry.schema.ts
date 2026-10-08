/**
 * This application's telemetry vocabulary.
 *
 * Scenario, step and business event names are metric dimensions, declared
 * once here rather than as free text at each call site. Once a registry has
 * an entry, a name not listed in it is a compile error.
 *
 * No `UwtLoggerNames`: this app has no log backend.
 */
declare module '@absaoss-cps/ngx-ui-watchtower' {
  interface UwtScenarioNames {
    /** A router navigation, from click to activated route. */
    'route-navigation': true;

    /** Loading the customer list, from request to rows shown. */
    'customers-load': true;
  }

  interface UwtScenarioSteps {
    /** From the recognized URL to activation: guards, resolvers, lazy components. */
    'resolve-route': true;

    /** Activating the routed component. */
    activate: true;

    /** Fetching data from the API. */
    fetch: true;
  }
}

export {};
