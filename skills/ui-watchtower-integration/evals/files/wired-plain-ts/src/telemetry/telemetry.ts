import './telemetry.schema'; // the vocabulary
import { version } from '../../package.json';
import { uwtCreateTelemetry } from '@absaoss-cps/ui-watchtower';
import { UwtRumTelemetrySink } from '@absaoss-cps/ui-watchtower/rum';
import { AppLogApiProvider } from './log-api.provider';
import { AppRumCredentialsProvider } from './rum-credentials.provider';

const identity = {
  application: 'field-notes',
  // Vite's mode: 'development' on the dev server, 'production' in built deployments.
  environment: import.meta.env.MODE,
  version
};

/** Read once, at startup: the same value goes to everything created here. */
const enabled = true;

/** The RUM destination. Page views stay automatic (RUM's default). */
export const destination = new UwtRumTelemetrySink({
  identity,
  credentialsProvider: new AppRumCredentialsProvider(),
  enabled
});
destination.init(); // never awaited: a slow broker never delays the page

// No overrides (scenarios / bi / logging / redaction): the library defaults fit.
export const telemetry = uwtCreateTelemetry({
  identity,
  destination,
  logApi: new AppLogApiProvider(), // the app's log service, POST/GET /api/logs
  enabled
});
