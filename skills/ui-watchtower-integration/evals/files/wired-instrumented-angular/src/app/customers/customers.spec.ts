import { Injectable } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import {
  provideUwtTelemetry,
  provideUwtTelemetryDestination,
  UwtTelemetrySink,
  withScenarios
} from '@absaoss-cps/ngx-ui-watchtower';
import { Customers } from './customers';

const events: { eventType: string; payload: Record<string, unknown> }[] = [];

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

describe('Customers customers-load scenario', () => {
  let http: HttpTestingController;

  beforeEach(() => {
    events.length = 0;
    TestBed.configureTestingModule({
      imports: [Customers],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        provideUwtTelemetry(
          { application: 'customer-portal-test', environment: 'test', version: '0.0.0' },
          withScenarios({ defaultTimeoutMs: 0 })
        ),
        provideUwtTelemetryDestination(RecordingSink)
      ]
    });
    http = TestBed.inject(HttpTestingController);
  });

  function load() {
    const fixture = TestBed.createComponent(Customers);
    fixture.detectChanges();
    return { fixture, request: http.expectOne('/api/customers') };
  }

  const loads = () =>
    events.map((e) => e.payload).filter((p) => p['scenarioName'] === 'customers-load');

  it('records success with the row count', () => {
    load().request.flush([{ id: '1', name: 'Ada' }]);
    expect(loads()).toEqual([
      expect.objectContaining({ status: 'success', metadata: expect.objectContaining({ count: 1 }) })
    ]);
  });

  it('records an empty list as incomplete', () => {
    load().request.flush([]);
    expect(loads()).toEqual([expect.objectContaining({ status: 'incomplete', reason: 'no-results' })]);
  });

  it('records an HTTP error as failure with its status', () => {
    load().request.flush('boom', { status: 503, statusText: 'Unavailable' });
    expect(loads()).toEqual([expect.objectContaining({ status: 'failure', statusCode: 503 })]);
  });

  it('records leaving mid-load as abandoned', () => {
    load().fixture.destroy();
    expect(loads()).toEqual([
      expect.objectContaining({ status: 'abandoned', reason: 'component-destroyed' })
    ]);
  });
});
