import { Injectable } from '@angular/core';
import type {
  UwtRumBootstrap,
  UwtRumCredentialsProvider
} from '@absaoss-cps/ngx-ui-watchtower/rum';

/**
 * Endpoint of the backend that returns the RUM app-monitor settings and
 * short-lived AWS credentials. Adapt to the app's own broker.
 */
const RUM_BROKER_URL = '/rum/init';

/**
 * Shape returned by the backend broker. Adapt to the real response; map it
 * to `UwtRumBootstrap` in `load()`.
 */
interface RumBrokerResponse {
  enabled: boolean;
  config?: {
    applicationId: string;
    region: string;
    applicationVersion: string;
    sessionSampleRate?: number;
  };
  credentials?: {
    accessKeyId: string;
    secretAccessKey: string;
    sessionToken: string;
    expiration: string;
  };
}

/**
 * Supplies CloudWatch RUM settings and credentials from this application's
 * backend broker, so the browser never holds a long-lived AWS identity.
 *
 * Called at startup and again shortly before each credential expiry.
 */
@Injectable({ providedIn: 'root' })
export class AppRumCredentialsProvider implements UwtRumCredentialsProvider {
  /**
   * Fetches the current app-monitor settings and credentials.
   *
   * @returns the bootstrap payload, or `null` — RUM off for this session —
   *   when the broker disables RUM, is unreachable, or answers incompletely
   */
  async load(): Promise<UwtRumBootstrap | null> {
    let response: Response;
    try {
      response = await fetch(RUM_BROKER_URL, {
        headers: { Accept: 'application/json' },
        // The response carries live, temporary AWS credentials.
        cache: 'no-store'
      });
    } catch {
      // A network-level failure rejects before any response exists.
      return null;
    }

    if (!response.ok) {
      return null;
    }

    let init: RumBrokerResponse;
    try {
      init = (await response.json()) as RumBrokerResponse;
    } catch {
      return null;
    }

    // Credentials are required: without them the client would start and then
    // fail every dispatch silently.
    if (!init?.enabled || !init.config || !init.credentials) {
      return null;
    }

    return {
      config: {
        applicationId: init.config.applicationId,
        region: init.config.region,
        applicationVersion: init.config.applicationVersion,
        sessionSampleRate: init.config.sessionSampleRate
      },
      credentials: init.credentials
    };
  }
}
