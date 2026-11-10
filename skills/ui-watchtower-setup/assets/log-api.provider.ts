import { DOCUMENT, isPlatformBrowser } from '@angular/common';
import { inject, Injectable, PLATFORM_ID } from '@angular/core';
import type {
  UwtLogApiProvider,
  UwtLogQuery,
  UwtLogRecord
} from '@absaoss-cps/ngx-ui-watchtower';

/** The app's log-ingestion and log-query endpoint. Adapt to the real backend. */
const LOG_API_URL = '/api/logs';

/**
 * Sends this application's log records to its own log backend.
 *
 * Only for apps that have a log backend. Without one, bind
 * `UwtNoopLogApiProvider` (shells) or leave logging out entirely.
 *
 * Bound with `{ provide: UWT_LOG_API_PROVIDER, useExisting: AppLogApiProvider }`.
 * One request per record. If that is too many for a busy app, batch here and add a
 * `flush()` — the library calls it when the page is hidden or closed.
 */
@Injectable({ providedIn: 'root' })
export class AppLogApiProvider implements UwtLogApiProvider {
  private readonly isBrowser = isPlatformBrowser(inject(PLATFORM_ID));
  private readonly document = inject(DOCUMENT);

  /** @inheritdoc */
  send(record: UwtLogRecord): void {
    // Server-side rendering has no relative URL to post to.
    if (!this.isBrowser) {
      return;
    }
    fetch(LOG_API_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(record),
      // Only while the page is hidden (it may be closing): keepalive lets the request outlive it,
      // but browsers reject keepalive requests once all in flight exceed 64 KiB, so a burst would
      // be lost.
      keepalive: this.document.visibilityState === 'hidden'
    }).catch(() => undefined);
  }

  /** @inheritdoc */
  async query(filter: UwtLogQuery): Promise<UwtLogRecord[]> {
    if (!this.isBrowser) {
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
