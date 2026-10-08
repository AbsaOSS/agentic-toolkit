import { ApplicationConfig, isDevMode, provideBrowserGlobalErrorListeners } from '@angular/core';
import { provideHttpClient } from '@angular/common/http';
import { provideRouter } from '@angular/router';
import { provideUwtTelemetry } from '@absaoss-cps/ngx-ui-watchtower';
import {
  UWT_RUM_CREDENTIALS_PROVIDER,
  provideUwtTelemetryRumSink
} from '@absaoss-cps/ngx-ui-watchtower/rum';
import { routes } from './app.routes';
import { AppRumCredentialsProvider } from './telemetry/rum-credentials.provider';
import './telemetry/telemetry.schema'; // side-effect import: the telemetry vocabulary

/** Reported as the telemetry `version`; keep in step with package.json. */
const APP_VERSION = '1.4.0';

export const appConfig: ApplicationConfig = {
  providers: [
    provideBrowserGlobalErrorListeners(),
    provideRouter(routes),
    provideHttpClient(),
    // No features (withScenarios / withBIEvents / withLogging / withRedaction):
    // the library defaults fit, and there is no log backend.
    provideUwtTelemetry({
      application: 'customer-portal',
      // The app has no environment files; dev server vs. production build is
      // the only distinction available at runtime.
      environment: isDevMode() ? 'dev' : 'prod',
      version: APP_VERSION
    }),
    // This app's one destination: AWS CloudWatch RUM. Settings and short-lived
    // credentials come from GET /rum/init; a failed fetch only disables RUM
    // for the session.
    provideUwtTelemetryRumSink(),
    { provide: UWT_RUM_CREDENTIALS_PROVIDER, useExisting: AppRumCredentialsProvider }
  ]
};
