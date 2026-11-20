/**
 * This application's telemetry vocabulary.
 *
 * Scenario, step and business event names are metric dimensions, declared
 * once here rather than as free text at each call site. Once a registry has
 * an entry, a name not listed in it is a compile error.
 *
 * Names are kebab-case. Scenario, BI event and logger names start with the
 * app's prefix, `field-notes`. Step names have no prefix.
 *
 * Keep a side-effect import of this file (`import './telemetry.schema';`) in
 * the engine module, so it can never become unreferenced.
 */
// Loads the module being augmented, even where nothing else in the program imports it.
import type {} from '@absaoss-cps/ui-watchtower';

declare module '@absaoss-cps/ui-watchtower' {
  interface UwtLoggerNames {
    /** Application start-up and sign-in. */
    'field-notes-lifecycle': true;
  }
}

export {};
