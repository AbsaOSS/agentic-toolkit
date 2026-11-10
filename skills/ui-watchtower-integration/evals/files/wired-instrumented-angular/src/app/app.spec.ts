import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import {
  provideUwtTelemetry,
  provideUwtTelemetrySink,
  withScenarios
} from '@absaoss-cps/ngx-ui-watchtower';
import { App } from './app';

describe('App', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [App],
      providers: [
        provideRouter([]),
        // App starts route-navigation telemetry in its constructor.
        provideUwtTelemetry(
          { application: 'customer-portal-test', environment: 'test', version: '0.0.0' },
          withScenarios({ defaultTimeoutMs: 0 }) // no scenario timers left running in tests
        ),
        provideUwtTelemetrySink('noop')
      ]
    }).compileComponents();
  });

  it('should create the app', () => {
    expect(TestBed.createComponent(App).componentInstance).toBeTruthy();
  });
});
