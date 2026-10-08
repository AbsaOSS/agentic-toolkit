import { Injectable } from '@angular/core';
import { Router, NavigationEnd } from '@angular/router';
import { AwsRum, AwsRumConfig } from 'aws-rum-web';
import { filter } from 'rxjs';

/**
 * Hand-written CloudWatch RUM integration. The "Desk usage" dashboard and the
 * "order-failures" metric filter query the event types below.
 */
@Injectable({ providedIn: 'root' })
export class RumService {
  private rum?: AwsRum;

  constructor(private readonly router: Router) {}

  async init(): Promise<void> {
    const res = await fetch('/rum/config');
    const { applicationId, region, identityPoolId, guestRoleArn } = await res.json();
    const config: AwsRumConfig = {
      sessionSampleRate: 1,
      identityPoolId,
      guestRoleArn,
      telemetries: ['errors', 'performance', 'http'],
      disableAutoPageView: true
    };
    this.rum = new AwsRum(applicationId, '3.2.0', region, config);

    this.router.events
      .pipe(filter((e): e is NavigationEnd => e instanceof NavigationEnd))
      .subscribe((e) => this.rum?.recordPageView(e.urlAfterRedirects));
  }

  trackOrderSubmitted(instrument: string, quantity: number): void {
    this.rum?.recordEvent('desk.order.submitted', { instrument, quantity });
  }

  trackOrderFailed(instrument: string, error: unknown): void {
    this.rum?.recordEvent('desk.order.failed', {
      instrument,
      message: error instanceof Error ? error.message : String(error)
    });
  }

  trackSearch(query: string): void {
    this.rum?.recordEvent('desk.search', { query });
  }

  setUser(email: string | undefined): void {
    if (email) {
      this.rum?.addSessionAttributes({ user: email });
    }
  }
}
