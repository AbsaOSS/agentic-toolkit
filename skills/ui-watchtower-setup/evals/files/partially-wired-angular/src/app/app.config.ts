import { ApplicationConfig, provideBrowserGlobalErrorListeners } from '@angular/core';
import { provideHttpClient } from '@angular/common/http';
import { provideRouter } from '@angular/router';
import { provideUwtTelemetry } from '@absaoss-cps/ngx-ui-watchtower';
import { routes } from './app.routes';

export const appConfig: ApplicationConfig = {
  providers: [
    provideBrowserGlobalErrorListeners(),
    provideRouter(routes),
    provideHttpClient(),
    // TODO(telemetry): finish wiring — started in the last sprint
    provideUwtTelemetry({ application: 'customer-portal', environment: 'prod', version: '1.4.0' })
  ]
};
