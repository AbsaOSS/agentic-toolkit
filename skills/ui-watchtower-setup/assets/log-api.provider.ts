// Types only: in an Angular app, import them from '@absaoss-cps/ngx-ui-watchtower'.
import type {
  UwtLogApiProvider,
  UwtLogQuery,
  UwtLogRecord
} from '@absaoss-cps/ui-watchtower';

/** The app's log-ingestion and log-query endpoint. Adapt to the real backend. */
const LOG_API_URL = '/api/logs';

/**
 * Sends this application's log records to its own log backend.
 *
 * Only for apps that have a log backend. Without one, use `UwtNoopLogApiProvider` (shells) or
 * leave logging out entirely.
 *
 * Pass an instance as the engine's `logApi`; in Angular, bind it with
 * `{ provide: UWT_LOG_API_PROVIDER, useClass: AppLogApiProvider }`.
 *
 * One request per record. If that is too many for a busy app, batch here and add a `flush()` —
 * the library calls it when the page is hidden or closed — sending from it with
 * `navigator.sendBeacon` or a `keepalive` request every time.
 */
export class AppLogApiProvider implements UwtLogApiProvider {
  /** Server-side rendering has no relative URL to post to. */
  private readonly inBrowser = typeof window !== 'undefined' && typeof document !== 'undefined';

  /** @inheritdoc */
  send(record: UwtLogRecord): void {
    if (!this.inBrowser) {
      return;
    }
    fetch(LOG_API_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(record),
      // Only while the page is hidden (it may be closing): keepalive lets the request outlive it,
      // but browsers reject keepalive requests once all in flight exceed 64 KiB, so a burst would
      // be lost. Safari still says `visible` while a reloading or navigating page hides, so a
      // record written as the page goes can be lost there.
      keepalive: document.visibilityState === 'hidden'
    }).catch(() => undefined);
  }

  /** @inheritdoc */
  async query(filter: UwtLogQuery): Promise<UwtLogRecord[]> {
    if (!this.inBrowser) {
      return [];
    }
    const params = new URLSearchParams();
    for (const [key, value] of Object.entries(filter)) {
      if (value !== undefined) {
        params.set(key, String(value));
      }
    }
    try {
      const response = await fetch(`${LOG_API_URL}?${params}`);
      return response.ok ? ((await response.json()) as UwtLogRecord[]) : [];
    } catch {
      return [];
    }
  }
}
