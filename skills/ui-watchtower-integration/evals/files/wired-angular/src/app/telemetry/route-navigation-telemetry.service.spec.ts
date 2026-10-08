import { Component, inject, Injectable } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { provideRouter, Router, UrlSegment } from '@angular/router';
import {
  provideUwtTelemetry,
  provideUwtTelemetryDestination,
  UwtTelemetrySink,
  withScenarios
} from '@absaoss-cps/ngx-ui-watchtower';
import {
  RouteNavigationTelemetryService,
  ROUTE_PAGE_VIEW_RECORDER
} from './route-navigation-telemetry.service';

const events: { eventType: string; payload: Record<string, unknown> }[] = [];
const pageViews: string[] = [];

@Injectable()
class RecordingSink extends UwtTelemetrySink {
  record(eventType: string, payload: object): void {
    events.push({ eventType, payload: payload as Record<string, unknown> });
  }
  recordError(): void {}
  getSessionId(): string | undefined { return 'session-1'; }
  setUserId(): void {}
  getUserId(): string | undefined { return undefined; }
  flush(): void {}
}

@Component({ template: '' })
class Page {}

let releaseSlowGuard: (value: boolean) => void = () => undefined;
let releaseHangGuard: (value: boolean) => void = () => undefined;

function filesMatcher(segments: UrlSegment[]) {
  return segments[0]?.path === 'files'
    ? { consumed: segments, posParams: { path: segments[segments.length - 1] } }
    : null;
}

const scenarios = () => events.map((e) => e.payload);

describe('RouteNavigationTelemetryService', () => {
  let router: Router;

  beforeEach(() => {
    events.length = 0;
    pageViews.length = 0;
    TestBed.configureTestingModule({
      providers: [
        provideRouter([
          { path: '', pathMatch: 'full', redirectTo: 'customers' },
          { path: 'customers', component: Page },
          { path: 'customers/:id', component: Page },
          {
            path: 'orders',
            loadChildren: () => Promise.resolve([{ path: ':orderId', component: Page }])
          },
          { path: 'blocked', component: Page, canActivate: [() => false] },
          {
            path: 'old',
            component: Page,
            canActivate: [() => inject(Router).parseUrl('/customers')]
          },
          {
            path: 'legacy/:id',
            component: Page,
            canActivate: [
              (route: { paramMap: { get(k: string): string | null } }) =>
                inject(Router).parseUrl(`/customers/${route.paramMap.get('id')}`)
            ]
          },
          {
            path: 'broken',
            component: Page,
            resolve: { data: () => Promise.reject(new Error('resolver failed for cust-SECRET-7')) }
          },
          {
            path: 'http-broken',
            component: Page,
            resolve: {
              data: () =>
                Promise.reject({ name: 'HttpErrorResponse', status: 503, message: 'GET /api/cust-SECRET-7 failed' })
            }
          },
          {
            path: 'back-home',
            component: Page,
            canActivate: [() => inject(Router).parseUrl('/customers')]
          },
          {
            path: 'slow',
            component: Page,
            canActivate: [() => new Promise<boolean>((resolve) => (releaseSlowGuard = resolve))]
          },
          { matcher: filesMatcher, component: Page, data: { telemetryPath: 'files/:path' } },
          {
            path: 'hang',
            component: Page,
            canActivate: [() => new Promise<boolean>((resolve) => (releaseHangGuard = resolve))]
          },
          { path: 'never-loads', loadChildren: () => new Promise<never>(() => undefined) }
        ]),
        provideUwtTelemetry(
          { application: 'customer-portal-test', environment: 'test', version: '0.0.0' },
          withScenarios({ defaultTimeoutMs: 0 })
        ),
        provideUwtTelemetryDestination(RecordingSink),
        { provide: ROUTE_PAGE_VIEW_RECORDER, useValue: (route: string) => pageViews.push(route) }
      ]
    });
    TestBed.inject(RouteNavigationTelemetryService).start();
    router = TestBed.inject(Router);
  });

  it('records a static route without query, matrix or fragment, plus one page view', async () => {
    await router.navigateByUrl('/customers;view=grid?tab=open#top');
    expect(events).toEqual([
      expect.objectContaining({
        eventType: 'com.uwt.scenario',
        payload: expect.objectContaining({
          scenarioName: 'route-navigation',
          status: 'success',
          route: '/customers',
          metadata: expect.objectContaining({ resolveMs: expect.any(Number) })
        })
      })
    ]);
    expect(pageViews).toEqual(['/customers']);
  });

  it('reports a :param route as its template, never the id', async () => {
    await router.navigateByUrl('/customers/cust-SECRET-7');
    expect(scenarios()).toEqual([
      expect.objectContaining({ status: 'success', route: '/customers/:id' })
    ]);
    expect(pageViews).toEqual(['/customers/:id']);
    expect(JSON.stringify(events)).not.toContain('SECRET');
  });

  it('reports a lazy loadChildren route as its template on first load', async () => {
    await router.navigateByUrl('/orders/A-77');
    expect(scenarios()).toEqual([
      expect.objectContaining({ status: 'success', route: '/orders/:orderId' })
    ]);
  });

  it('reports a config redirect as the target template', async () => {
    await router.navigateByUrl('/');
    expect(scenarios()).toEqual([
      expect.objectContaining({ status: 'success', route: '/customers' })
    ]);
  });

  it('records a guard rejection as incomplete, without the router reason text', async () => {
    await router.navigateByUrl('/blocked');
    expect(scenarios()).toEqual([
      expect.objectContaining({ status: 'incomplete', reason: 'guard-rejected', route: '/blocked' })
    ]);
    expect(scenarios()[0]['message']).toBeUndefined();
    expect(pageViews).toEqual([]);
  });

  it('records a guard redirect as one scenario under the final template', async () => {
    await router.navigateByUrl('/old');
    expect(scenarios()).toEqual([
      expect.objectContaining({
        status: 'success',
        route: '/customers',
        metadata: expect.objectContaining({ redirectedFrom: '/old' })
      })
    ]);
    expect(pageViews).toEqual(['/customers']);
  });

  it('records a parameterised guard redirect under the final template, without ids', async () => {
    await router.navigateByUrl('/legacy/cust-SECRET-7');
    expect(scenarios()).toEqual([
      expect.objectContaining({
        status: 'success',
        route: '/customers/:id',
        metadata: expect.objectContaining({ redirectedFrom: '/legacy/:id' })
      })
    ]);
    expect(JSON.stringify(events)).not.toContain('SECRET');
  });

  it('records an unmatched URL as a failure with no URL anywhere in the payload', async () => {
    await router.navigateByUrl('/no-such-page/cust-SECRET-7').catch(() => false);
    expect(scenarios()).toEqual([
      expect.objectContaining({ status: 'failure', route: '(unrecognized)' })
    ]);
    const wire = JSON.stringify(events);
    expect(wire).not.toContain('no-such-page');
    expect(wire).not.toContain('SECRET');
  });

  it('replaces a matched route\'s error with a generic one, keeping only its name', async () => {
    await router.navigateByUrl('/broken').catch(() => false);
    expect(scenarios()).toEqual([
      expect.objectContaining({ status: 'failure', route: '/broken' })
    ]);
    expect(JSON.stringify(events)).not.toContain('SECRET');
    expect(JSON.stringify(events)).not.toContain('resolver failed');
  });

  it('keeps the HTTP status of a resolver error, not its message', async () => {
    await router.navigateByUrl('/http-broken').catch(() => false);
    expect(scenarios()).toEqual([
      expect.objectContaining({ status: 'failure', route: '/http-broken', statusCode: 503 })
    ]);
    expect(JSON.stringify(events)).not.toContain('SECRET');
    expect(JSON.stringify(events)).toContain('HttpErrorResponse');
  });

  it('records nothing more for a navigation to the current URL', async () => {
    await router.navigateByUrl('/customers');
    await router.navigateByUrl('/customers');
    expect(scenarios()).toEqual([expect.objectContaining({ status: 'success', route: '/customers' })]);
  });

  it('releases a guard redirect back to the current URL as abandoned under its source template', async () => {
    await router.navigateByUrl('/customers');
    events.length = 0;
    await router.navigateByUrl('/back-home');
    expect(scenarios()).toEqual([
      expect.objectContaining({ status: 'abandoned', reason: 'same-url', route: '/back-home' })
    ]);
  });

  it('names a matcher route from its data', async () => {
    await router.navigateByUrl('/files/a/b/report.pdf');
    expect(scenarios()).toEqual([
      expect.objectContaining({ status: 'success', route: '/files/:path' })
    ]);
  });

  it('records a superseded navigation as abandoned, and the new one as success', async () => {
    const first = router.navigateByUrl('/slow');
    await new Promise((r) => setTimeout(r));
    await router.navigateByUrl('/customers');
    releaseSlowGuard(true);
    await first;
    expect(scenarios()).toEqual([
      expect.objectContaining({ status: 'abandoned', reason: 'superseded', route: '/slow' }),
      expect.objectContaining({ status: 'success', route: '/customers' })
    ]);
    // The router's reason text ("Navigation ID 1 is not equal to …") never reaches telemetry.
    expect(scenarios()[0]['message']).toBeUndefined();
  });

  it('keeps the start time across a guard redirect', async () => {
    TestBed.inject(RouteNavigationTelemetryService).markNavigationIntent();
    await new Promise((r) => setTimeout(r, 60));
    await router.navigateByUrl('/old');
    expect((scenarios()[0] as { delta: number }).delta).toBeGreaterThanOrEqual(50);
  });

  it('backdates to a recent navigation intent', async () => {
    TestBed.inject(RouteNavigationTelemetryService).markNavigationIntent();
    await new Promise((r) => setTimeout(r, 60));
    await router.navigateByUrl('/customers');
    expect((scenarios()[0] as { delta: number }).delta).toBeGreaterThanOrEqual(50);
  });

  describe('a navigation that never ends', () => {
    beforeEach(() => vi.useFakeTimers({ toFake: ['setTimeout', 'clearTimeout', 'Date'] }));
    afterEach(() => vi.useRealTimers());

    it('records a hung guard once as timeout under its template, and nothing when it ends late', async () => {
      const pending = router.navigateByUrl('/hang');
      await vi.advanceTimersByTimeAsync(29_000);
      expect(scenarios()).toEqual([]);
      await vi.advanceTimersByTimeAsync(1_000);
      expect(scenarios()).toEqual([
        expect.objectContaining({ status: 'timeout', reason: 'navigation-timeout', route: '/hang' })
      ]);
      releaseHangGuard(true);
      await pending;
      expect(scenarios()).toHaveLength(1);
      expect(pageViews).toEqual([]);
    });

    it('records a lazy route that never loads as timeout under (unrecognized)', async () => {
      void router.navigateByUrl('/never-loads/x');
      await vi.advanceTimersByTimeAsync(30_000);
      expect(scenarios()).toEqual([
        expect.objectContaining({ status: 'timeout', route: '(unrecognized)' })
      ]);
    });

    it('clears the timer when a navigation ends', async () => {
      await router.navigateByUrl('/customers');
      await vi.advanceTimersByTimeAsync(60_000);
      expect(scenarios()).toEqual([expect.objectContaining({ status: 'success' })]);
    });
  });
});
