import { Component, Injectable } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { provideRouter, Router, Routes } from '@angular/router';
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

/** Records everything handed to the destination, so tests assert on the wire. */
@Injectable()
class RecordingSink extends UwtTelemetrySink {
  override record(eventType: string, payload: object): void {
    events.push({ eventType, payload: payload as Record<string, unknown> });
  }
  override recordError(): void {}
  override getSessionId(): string | undefined {
    return 'session-1';
  }
  override setUserId(): void {}
  override getUserId(): string | undefined {
    return undefined;
  }
  override flush(): void {}
}

@Component({ template: '' })
class Stub {}

/** Mirrors the app's route shapes (redirect, static, `:param`) plus failure paths. */
const routes: Routes = [
  { path: '', pathMatch: 'full', redirectTo: 'customers' },
  { path: 'customers', component: Stub },
  { path: 'customers/:customerId', component: Stub },
  { path: 'blocked', canActivate: [() => false], component: Stub },
  {
    path: 'broken',
    canActivate: [
      () => {
        throw new Error('guard exploded');
      }
    ],
    component: Stub
  }
];

function scenarios(): Record<string, unknown>[] {
  return events.filter((e) => e.eventType === 'com.uwt.scenario').map((e) => e.payload);
}

describe('RouteNavigationTelemetryService', () => {
  let router: Router;

  beforeEach(() => {
    events.length = 0;
    pageViews.length = 0;
    TestBed.configureTestingModule({
      providers: [
        provideRouter(routes),
        provideUwtTelemetry(
          { application: 'customer-portal-test', environment: 'test', version: '0.0.0' },
          withScenarios({ defaultTimeoutMs: 0 })
        ),
        provideUwtTelemetryDestination(RecordingSink),
        { provide: ROUTE_PAGE_VIEW_RECORDER, useValue: (route: string) => pageViews.push(route) }
      ]
    });
    router = TestBed.inject(Router);
    TestBed.inject(RouteNavigationTelemetryService).start();
  });

  it('reports a successful navigation under its route template, never the resolved id', async () => {
    await router.navigateByUrl('/customers/cust-SECRET-7?tab=orders');

    expect(scenarios()).toEqual([
      expect.objectContaining({
        scenarioName: 'route-navigation',
        status: 'success',
        route: '/customers/:customerId'
      })
    ]);
    expect(pageViews).toEqual(['/customers/:customerId']);
    expect(JSON.stringify(events)).not.toContain('SECRET');
  });

  it('reports the redirect from the empty path under the target template', async () => {
    await router.navigateByUrl('/');

    expect(scenarios()).toEqual([
      expect.objectContaining({ status: 'success', route: '/customers' })
    ]);
  });

  it('reports a guard rejection as incomplete, not as a failure', async () => {
    await router.navigateByUrl('/blocked');

    expect(scenarios()).toEqual([
      expect.objectContaining({ status: 'incomplete', reason: 'guard-rejected', route: '/blocked' })
    ]);
  });

  it('records nothing for a navigation superseded before the URL was recognized', async () => {
    const first = router.navigateByUrl('/customers/1');
    const second = router.navigateByUrl('/customers/2');
    await Promise.all([first, second]);

    expect(scenarios()).toEqual([
      expect.objectContaining({ status: 'success', route: '/customers/:customerId' })
    ]);
  });

  it('reports a navigation error as a failure', async () => {
    await router.navigateByUrl('/broken').catch(() => undefined);

    expect(scenarios()).toEqual([
      expect.objectContaining({ status: 'failure', route: '/broken' })
    ]);
  });

  it('reports an unknown URL under a placeholder template, with no URL in the payload', async () => {
    await router.navigateByUrl('/nope/cust-SECRET-7').catch(() => undefined);

    expect(scenarios()).toEqual([
      expect.objectContaining({ status: 'failure', route: '(unrecognized)' })
    ]);
    expect(JSON.stringify(events)).not.toContain('SECRET');
  });
});
