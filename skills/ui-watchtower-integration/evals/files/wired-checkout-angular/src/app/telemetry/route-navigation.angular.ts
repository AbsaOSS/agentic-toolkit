import { isPlatformBrowser } from '@angular/common';
import {
  DestroyRef,
  EnvironmentProviders,
  inject,
  Injectable,
  InjectionToken,
  NgZone,
  PLATFORM_ID,
  provideEnvironmentInitializer
} from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import {
  ActivatedRouteSnapshot,
  Event as RouterEvent,
  NavigationCancel,
  NavigationCancellationCode,
  NavigationEnd,
  NavigationError,
  NavigationSkipped,
  NavigationSkippedCode,
  NavigationStart,
  PRIMARY_OUTLET,
  Router,
  RoutesRecognized
} from '@angular/router';
import { UwtScenarioTelemetryService } from '@absaoss-cps/ngx-ui-watchtower';
import { RouteNavigationTracker } from './route-navigation-tracker';

/**
 * Records one page view per completed navigation, under the route template. Bind it to
 * `UwtRumTelemetrySink.recordPageView` only where RUM is the destination, with
 * `disableAutoPageView: true` — automatic page views report the resolved path (`/customers/42`).
 */
export const ROUTE_PAGE_VIEW_RECORDER = new InjectionToken<(route: string) => void>(
  'ROUTE_PAGE_VIEW_RECORDER'
);

/** Route `data` key naming a `matcher` route's segment — a matcher has no `path`. */
const TELEMETRY_PATH_DATA_KEY = 'telemetryPath';

/**
 * Low-cardinality causes from the router's `code`. Its `reason` text is never sent: empty in
 * production, and it can contain URLs in development.
 */
const CANCEL_REASON: Partial<Record<NavigationCancellationCode, string>> = {
  [NavigationCancellationCode.Redirect]: 'redirect',
  [NavigationCancellationCode.SupersededByNewNavigation]: 'superseded',
  [NavigationCancellationCode.NoDataFromResolver]: 'no-data-from-resolver',
  [NavigationCancellationCode.GuardRejected]: 'guard-rejected',
  [NavigationCancellationCode.Aborted]: 'aborted'
};

/** Expected dead ends (`incomplete`), not the user leaving (`abandoned`). */
const INCOMPLETE_CODES = new Set<NavigationCancellationCode>([
  NavigationCancellationCode.GuardRejected,
  NavigationCancellationCode.NoDataFromResolver
]);

/** As {@link CANCEL_REASON}, for a navigation the router never ran. */
const SKIP_REASON: Partial<Record<NavigationSkippedCode, string>> = {
  [NavigationSkippedCode.IgnoredSameUrlNavigation]: 'same-url',
  [NavigationSkippedCode.IgnoredByUrlHandlingStrategy]: 'url-handling-strategy'
};

/** `code` is optional, and a future Angular may add one not mapped here. */
function causeOf<TCode extends number>(
  causes: Partial<Record<TCode, string>>,
  code: TCode | undefined,
  fallback: string
): string {
  return (code === undefined ? undefined : causes[code]) ?? fallback;
}

/** Matched template from the primary outlet's `routeConfig` chain: `/customers/:id`. */
function routeTemplateOf(root: ActivatedRouteSnapshot): string {
  const parts: string[] = [];
  for (
    let route: ActivatedRouteSnapshot | null = root;
    route;
    route = route.children.find((child) => child.outlet === PRIMARY_OUTLET) ?? null
  ) {
    const config = route.routeConfig;
    if (!config) {
      continue;
    }
    const path = config.matcher
      ? ((config.data?.[TELEMETRY_PATH_DATA_KEY] as string | undefined) ?? '(matcher)')
      : config.path;
    if (path) {
      parts.push(path);
    }
  }
  return `/${parts.join('/')}`;
}

/**
 * The Angular Router binding of `RouteNavigationTracker`. Start it with
 * {@link provideRouteNavigationTelemetry}; call {@link markNavigationIntent} from click handlers
 * that navigate.
 */
@Injectable({ providedIn: 'root' })
export class RouteNavigationTelemetryService {
  private readonly router = inject(Router);
  private readonly destroyRef = inject(DestroyRef);
  private readonly zone = inject(NgZone);
  private readonly scenarioTelemetry = inject(UwtScenarioTelemetryService);
  private readonly tracker = new RouteNavigationTracker({
    startScenario: (options) => this.scenarioTelemetry.start(options),
    recordPageView: inject(ROUTE_PAGE_VIEW_RECORDER, { optional: true }) ?? undefined,
    // Outside Angular, so a pending timeout never delays app stability or server rendering.
    runOutside: (callback) => this.zone.runOutsideAngular(callback),
    inBrowser: isPlatformBrowser(inject(PLATFORM_ID))
  });

  private started = false;

  /** Safe to call more than once. */
  start(): void {
    if (this.started) {
      return;
    }
    this.started = true;

    this.router.events
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe((event) => this.onRouterEvent(event));
    this.destroyRef.onDestroy(() => this.tracker.dispose());
  }

  /** `NavigationStart` comes after event handling and change detection; count that wait too. */
  markNavigationIntent(): void {
    this.tracker.markIntent();
  }

  private onRouterEvent(event: RouterEvent): void {
    if (event instanceof NavigationStart) {
      this.tracker.start(event.id);
    } else if (event instanceof RoutesRecognized) {
      this.tracker.recognized(event.id, routeTemplateOf(event.state.root));
    } else if (event instanceof NavigationEnd) {
      this.tracker.end(event.id);
    } else if (event instanceof NavigationCancel) {
      if (event.code === NavigationCancellationCode.Redirect) {
        // Restarts under a new id.
        this.tracker.redirected(event.id);
      } else {
        this.tracker.cancel(event.id, {
          reason: causeOf(CANCEL_REASON, event.code, 'navigation-cancelled'),
          incomplete: event.code !== undefined && INCOMPLETE_CODES.has(event.code)
        });
      }
    } else if (event instanceof NavigationSkipped) {
      this.tracker.skip(event.id, causeOf(SKIP_REASON, event.code, 'navigation-skipped'));
    } else if (event instanceof NavigationError) {
      this.tracker.fail(event.id, event.error);
    }
  }
}

/**
 * Starts route-navigation telemetry before any navigation runs — including a blocking initial
 * navigation (`withEnabledBlockingInitialNavigation()`), which starts before the root component
 * exists. Add it next to `provideRouter(...)`.
 */
export function provideRouteNavigationTelemetry(): EnvironmentProviders {
  return provideEnvironmentInitializer(() => inject(RouteNavigationTelemetryService).start());
}
