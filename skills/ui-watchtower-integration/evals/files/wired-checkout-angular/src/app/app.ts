import { Component, inject } from '@angular/core';
import { RouterLink, RouterOutlet } from '@angular/router';
import { RouteNavigationTelemetryService } from './telemetry/route-navigation-telemetry.service';

@Component({
  selector: 'app-root',
  imports: [RouterOutlet, RouterLink],
  template: `
    <nav><a routerLink="/cart" (click)="markNavigationIntent()">Cart</a></nav>
    <router-outlet />
  `
})
export class App {
  private readonly routeTelemetry = inject(RouteNavigationTelemetryService);

  /** Starts the navigation measurement at the click, not at NavigationStart. */
  protected markNavigationIntent(): void {
    this.routeTelemetry.markNavigationIntent();
  }
}
