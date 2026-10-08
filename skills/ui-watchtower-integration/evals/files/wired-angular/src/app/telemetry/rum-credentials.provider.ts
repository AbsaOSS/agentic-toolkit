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
 * Shape expected from the backend broker. Adapt to the real response; `load()`
 * checks every required field before using it.
 *
 * ```json
 * {
 *   "enabled": true,
 *   "config": { "applicationId": "…", "region": "eu-west-1", "applicationVersion": "1.4.0",
 *               "sessionSampleRate": 1 },
 *   "credentials": { "accessKeyId": "…", "secretAccessKey": "…", "sessionToken": "…",
 *                    "expiration": "2026-10-08T12:00:00Z" }
 * }
 * ```
 */
const REQUIRED_CONFIG = ['applicationId', 'region', 'applicationVersion'] as const;
const REQUIRED_CREDENTIALS = [
  'accessKeyId',
  'secretAccessKey',
  'sessionToken',
  'expiration'
] as const;

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

/** Whether `value` is an object whose `keys` are all non-empty strings. */
function hasStrings<K extends string>(
  value: unknown,
  keys: readonly K[]
): value is Record<K, string> & Record<string, unknown> {
  return (
    isRecord(value) &&
    keys.every((key) => typeof value[key] === 'string' && value[key] !== '')
  );
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
   *   when the broker disables RUM, is unreachable, or answers with anything
   *   missing or malformed
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

    let body: unknown;
    try {
      body = await response.json();
    } catch {
      return null;
    }

    // Validate, don't cast: a half-filled answer must turn RUM off, not start
    // a client that fails every dispatch silently.
    if (!isRecord(body) || body['enabled'] !== true) {
      return null;
    }
    const { config, credentials } = body;
    if (
      !hasStrings(config, REQUIRED_CONFIG) ||
      !hasStrings(credentials, REQUIRED_CREDENTIALS) ||
      Number.isNaN(Date.parse(credentials.expiration))
    ) {
      return null;
    }

    const rate = config['sessionSampleRate'];
    return {
      config: {
        applicationId: config.applicationId,
        region: config.region,
        applicationVersion: config.applicationVersion,
        sessionSampleRate: typeof rate === 'number' && rate >= 0 && rate <= 1 ? rate : undefined,
        // Page views are recorded under the route template by
        // RouteNavigationTelemetryService; automatic ones would send the
        // resolved path (/customers/42).
        disableAutoPageView: true
      },
      credentials: {
        accessKeyId: credentials.accessKeyId,
        secretAccessKey: credentials.secretAccessKey,
        sessionToken: credentials.sessionToken,
        expiration: credentials.expiration
      }
    };
  }
}
