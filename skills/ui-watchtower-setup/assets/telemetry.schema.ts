/**
 * This application's telemetry vocabulary.
 *
 * Scenario, step and business event names are metric dimensions, declared
 * once here rather than as free text at each call site. Once a registry has
 * an entry, a name not listed in it is a compile error.
 *
 * Names are kebab-case. Scenario, BI event and logger names start with the
 * app's prefix — `my-app` here: replace it with the confirmed one. Step names
 * have no prefix.
 *
 * Keep a side-effect import of this file (`import './telemetry.schema';`)
 * where the telemetry providers are configured and in the router telemetry
 * service, so it can never become unreferenced.
 */
declare module '@absaoss-cps/ngx-ui-watchtower' {
  interface UwtScenarioNames {
    /** A router navigation, from click to activated route, under the final route template. */
    'my-app-route-navigate': true;

    // One entry per confirmed journey, <prefix>-<thing>-<action>, with a line saying what it measures:
    // /** Loading the customer list, from request to first render. */
    // 'my-app-customers-load': true;
  }

  // Add once the first journey with steps is confirmed (no prefix: <action> or
  // <thing>-<action>; steps and aggregates share this registry):
  // interface UwtScenarioSteps {
  //   /** Fetching data from the API. */
  //   fetch: true;
  // }

  // Add once the first business event is confirmed (<prefix>-<thing>-<past-tense verb>):
  // interface UwtBIEventNames {
  //   /** The user exported the current result set. */
  //   'my-app-export-clicked': true;
  // }

  // Only when the app has a log backend (UWT_LOG_API_PROVIDER bound to a real provider):
  // interface UwtLoggerNames {
  //   /** Application lifecycle and routing (<prefix>-<area>). */
  //   'my-app-lifecycle': true;
  // }
}

export {};
