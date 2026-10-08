import { Injectable } from '@angular/core';
import type {
  UwtRumAppMonitorConfig,
  UwtRumBootstrap,
  UwtRumCredentialsProvider
} from '@absaoss-cps/ngx-ui-watchtower/rum';

/** The app's broker: RUM app-monitor settings plus short-lived AWS credentials. */
const RUM_BROKER_URL = '/rum/init';

/**
 * Expected answer — adapt to the real one:
 *
 * ```json
 * {
 *   "enabled": true,
 *   "config": { "applicationId": "…", "region": "eu-west-1", "applicationVersion": "1.4.0",
 *               "sessionSampleRate": 1, "telemetries": ["errors", "performance", "http"] },
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

/**
 * Optional settings a broker can send as JSON, kept only when correctly typed. Functions,
 * `RegExp`s and plugins (`pagesToInclude`, `eventPluginsToLoad`, …) can't travel as JSON.
 */
const NUMBER_SETTINGS = [
  'sessionLengthSeconds',
  'sessionEventLimit',
  'userIdRetentionDays',
  'batchLimit',
  'dispatchInterval',
  'eventCacheSize',
  'candidatesCacheSize',
  'retries',
  'routeChangeComplete',
  'routeChangeTimeout'
] as const;
const BOOLEAN_SETTINGS = [
  'suppressSessionStartEvent',
  'enableXRay',
  'enableW3CTraceId',
  'recordResourceUrl',
  'useBeacon',
  'signing',
  'allowCookies',
  'debug',
  'enableRumClient'
] as const;
const STRING_SETTINGS = ['endpoint', 'alias', 'client', 'releaseId'] as const;
const PAGE_ID_FORMATS = ['PATH', 'HASH', 'PATH_AND_HASH'];

function isFlatRecord<T>(
  value: unknown,
  isEntry: (entry: unknown) => entry is T
): value is Record<string, T> {
  return isRecord(value) && Object.values(value).every(isEntry);
}
const isPrimitive = (v: unknown): v is string | number | boolean =>
  ['string', 'number', 'boolean'].includes(typeof v);
const isString = (v: unknown): v is string => typeof v === 'string';
const isStringOrBoolean = (v: unknown): v is string | boolean =>
  typeof v === 'string' || typeof v === 'boolean';

function optionalSettings(config: Record<string, unknown>): Partial<UwtRumAppMonitorConfig> {
  const settings: Record<string, unknown> = {};
  const keep = (key: string, ok: boolean): void => {
    if (ok) {
      settings[key] = config[key];
    }
  };
  for (const key of NUMBER_SETTINGS) {
    keep(key, typeof config[key] === 'number' && Number.isFinite(config[key]));
  }
  for (const key of BOOLEAN_SETTINGS) {
    keep(key, typeof config[key] === 'boolean');
  }
  for (const key of STRING_SETTINGS) {
    keep(key, isString(config[key]) && config[key] !== '');
  }
  const rate = config['sessionSampleRate'];
  keep('sessionSampleRate', typeof rate === 'number' && rate >= 0 && rate <= 1);
  keep('pageIdFormat', PAGE_ID_FORMATS.includes(config['pageIdFormat'] as string));
  keep('sessionAttributes', isFlatRecord(config['sessionAttributes'], isPrimitive));
  keep('applicationAttributes', isFlatRecord(config['applicationAttributes'], isPrimitive));
  keep('headers', isFlatRecord(config['headers'], isString));
  keep('cookieAttributes', isFlatRecord(config['cookieAttributes'], isStringOrBoolean));
  const telemetries = config['telemetries'];
  keep(
    'telemetries',
    Array.isArray(telemetries) && telemetries.every((t) => isString(t) || Array.isArray(t))
  );
  const compression = config['compressionStrategy'];
  if (isRecord(compression) && typeof compression['enabled'] === 'boolean') {
    settings['compressionStrategy'] = { enabled: compression['enabled'] };
  }
  return settings as Partial<UwtRumAppMonitorConfig>;
}

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
 * Called at startup and ~5 min before each credential expiry, so the browser never holds a
 * long-lived AWS identity.
 */
@Injectable({ providedIn: 'root' })
export class AppRumCredentialsProvider implements UwtRumCredentialsProvider {
  /** `null` (RUM off for the session) unless the answer is complete, valid and unexpired. */
  async load(): Promise<UwtRumBootstrap | null> {
    let response: Response;
    try {
      response = await fetch(RUM_BROKER_URL, {
        headers: { Accept: 'application/json' },
        cache: 'no-store' // live AWS credentials
      });
    } catch {
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

    // Validate, don't cast: a half-filled answer would start a client that silently fails.
    if (!isRecord(body) || body['enabled'] !== true) {
      return null;
    }
    const { config, credentials } = body;
    if (
      !hasStrings(config, REQUIRED_CONFIG) ||
      !hasStrings(credentials, REQUIRED_CREDENTIALS) ||
      // Unparseable or already expired: RUM would reject every dispatch.
      !(Date.parse(credentials.expiration) > Date.now())
    ) {
      return null;
    }

    return {
      config: {
        ...optionalSettings(config),
        applicationId: config.applicationId,
        region: config.region,
        applicationVersion: config.applicationVersion,
        // Always: page views come from the route service, under the template — automatic ones
        // would send the resolved path (/customers/42).
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
