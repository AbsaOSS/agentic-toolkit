import { DestroyRef, inject, Injectable, InjectionToken } from '@angular/core';
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
import {
  UwtScenario,
  UwtScenarioTelemetryService
} from '@absaoss-cps/ngx-ui-watchtower';
// Side-effect import: the vocabulary declaring the names used below.
import './telemetry.schema';

/**
 * Records one page view per completed navigation, under the route template.
 *
 * Bind it only where AWS CloudWatch RUM is the destination, together with
 * `disableAutoPageView: true` in the app-monitor config — automatic page
 * views would report the resolved path (`/customers/42`):
 *
 * ```ts
 * {
 *   provide: ROUTE_PAGE_VIEW_RECORDER,
 *   useFactory: () => {
 *     const rum = inject(UwtRumTelemetrySink);
 *     return (route: string) => rum.recordPageView(route);
 *   }
 * }
 * ```
 */
export const ROUTE_PAGE_VIEW_RECORDER = new InjectionToken<(route: string) => void>(
  'ROUTE_PAGE_VIEW_RECORDER'
);

/** Name shared by every route-navigation scenario. */
const NAVIGATION_SCENARIO = 'route-navigation';

/** Beyond this, a recorded click is assumed not to have caused the navigation. */
const INTENT_MAX_AGE_MS = 2_000;

/** `route` of a navigation that failed before its URL matched a route. */
const UNRECOGNIZED_ROUTE = '(unrecognized)';

/**
 * Route `data` key naming a `matcher` route's segment in the template — a
 * matcher has no `path` to report.
 */
const TELEMETRY_PATH_DATA_KEY = 'telemetryPath';

/**
 * Stable, low-cardinality causes, derived from the router's `code`. The
 * router's `reason` text is never sent: it is empty in production builds and
 * can contain URLs in development builds.
 */
const CANCEL_REASON: Partial<Record<NavigationCancellationCode, string>> = {
  [NavigationCancellationCode.Redirect]: 'redirect',
  [NavigationCancellationCode.SupersededByNewNavigation]: 'superseded',
  [NavigationCancellationCode.NoDataFromResolver]: 'no-data-from-resolver',
  [NavigationCancellationCode.GuardRejected]: 'guard-rejected',
  [NavigationCancellationCode.Aborted]: 'aborted'
};

/**
 * Cancellations that are an expected dead end of the journey (`incomplete`),
 * not the user leaving it (`abandoned`).
 */
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

/**
 * The matched route's template, from the `routeConfig` chain of the primary
 * outlet: `/customers/42` → `/customers/:id`. Exact after `redirectTo` and lazy
 * `loadChildren`, because the router has done the matching.
 */
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
 * The router's error for a URL that matched nothing quotes the URL; replace it
 * so no path segment reaches telemetry. Its name is kept for grouping.
 */
function unrecognizedError(error: unknown): Error {
  const generic = new Error('Navigation failed before the URL matched a route');
  if (error instanceof Error) {
    generic.name = error.name;
  }
  return generic;
}

/** One router navigation being tracked. */
interface TrackedNavigation {
  /** Epoch ms the journey started: the click, `NavigationStart`, or the first navigation of a redirect chain. */
  startedAt: number;
  /** Template of the route a guard or resolver redirected away from. */
  redirectedFrom?: string;
  /** The matched route template, known from `RoutesRecognized` on. */
  route?: string;
  /** Epoch ms of `RoutesRecognized`: guards, resolvers and lazy components run after it. */
  recognizedAt?: number;
}

/** What a guard or resolver redirect carries into the next navigation. */
type RedirectCarry = Pick<TrackedNavigation, 'startedAt' | 'redirectedFrom'>;

/**
 * Measures every router navigation as one `route-navigation` scenario.
 *
 * The scenario is recorded when the navigation ends, so `route` is always the
 * final matched template — after `redirectTo`, lazy routes, and guard or
 * resolver redirects — and backdated to the click or the first
 * `NavigationStart`, so its duration covers the whole wait.
 *
 * Call {@link start} once, from the root component's constructor. Call
 * {@link markNavigationIntent} from navigation-link click handlers.
 */
@Injectable({ providedIn: 'root' })
export class RouteNavigationTelemetryService {
  private readonly router = inject(Router);
  private readonly scenarioTelemetry = inject(UwtScenarioTelemetryService);
  private readonly recordPageView = inject(ROUTE_PAGE_VIEW_RECORDER, { optional: true });
  private readonly destroyRef = inject(DestroyRef);

  /**
   * Keyed by navigation id, never a single "current" field: one navigation
   * can supersede another, and a single field would attribute the wrong
   * duration.
   */
  private readonly navigations = new Map<number, TrackedNavigation>();

  /** A redirected navigation, continued by the next `NavigationStart`. */
  private pendingRedirect?: RedirectCarry;

  /** When the user last did something expected to start a navigation. */
  private navigationIntentAt?: number;

  private started = false;

  /** Begins tracking router navigations. Safe to call more than once. */
  start(): void {
    if (this.started) {
      return;
    }
    this.started = true;

    this.router.events
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe((event) => this.onRouterEvent(event));
  }

  /**
   * Records that the user just did something expected to start a
   * navigation. The router raises `NavigationStart` after event handling,
   * guards and change detection; measuring from the click keeps that wait
   * inside the recorded duration.
   */
  markNavigationIntent(): void {
    this.navigationIntentAt = Date.now();
  }

  private onRouterEvent(event: RouterEvent): void {
    if (event instanceof NavigationStart) {
      const startedAt = this.navigationStartedAt();
      const redirect = this.consumePendingRedirect();
      this.navigations.set(event.id, {
        startedAt: redirect?.startedAt ?? startedAt,
        redirectedFrom: redirect?.redirectedFrom
      });
      return;
    }

    if (event instanceof RoutesRecognized) {
      const navigation = this.navigations.get(event.id);
      if (navigation) {
        navigation.route = routeTemplateOf(event.state.root);
        navigation.recognizedAt = Date.now();
      }
      return;
    }

    if (event instanceof NavigationEnd) {
      const navigation = this.take(event.id);
      if (navigation?.route) {
        this.record(navigation, navigation.route, (scenario, metadata) =>
          scenario.complete({ metadata })
        );
        this.recordPageView?.(navigation.route);
      }
      return;
    }

    if (event instanceof NavigationCancel) {
      const navigation = this.take(event.id);
      if (!navigation) {
        return;
      }
      if (event.code === NavigationCancellationCode.Redirect) {
        // A guard or resolver redirect restarts under a new id: carry the
        // start time, so one journey stays one scenario under its final route.
        this.pendingRedirect = {
          startedAt: navigation.startedAt,
          redirectedFrom: navigation.redirectedFrom ?? navigation.route
        };
        return;
      }
      // Superseded before its URL was recognized: nothing to attribute it to.
      if (!navigation.route) {
        return;
      }
      const reason = causeOf(CANCEL_REASON, event.code, 'navigation-cancelled');
      this.record(navigation, navigation.route, (scenario, metadata) =>
        event.code !== undefined && INCOMPLETE_CODES.has(event.code)
          ? scenario.incomplete({ reason, metadata })
          : scenario.cancel({ reason, metadata })
      );
      return;
    }

    if (event instanceof NavigationSkipped) {
      // A redirect back to the current URL ends in NavigationSkipped instead
      // of the NavigationStart the carried redirect waits for. Release it, and
      // drop the click intent so it can't backdate an unrelated navigation.
      this.navigationIntentAt = undefined;
      const reason = causeOf(SKIP_REASON, event.code, 'navigation-skipped');
      const redirect = this.consumePendingRedirect();
      if (redirect?.redirectedFrom) {
        this.record(redirect, redirect.redirectedFrom, (scenario, metadata) =>
          scenario.cancel({ reason, metadata })
        );
      }
      const navigation = this.take(event.id);
      if (navigation?.route) {
        this.record(navigation, navigation.route, (scenario, metadata) =>
          scenario.cancel({ reason, metadata })
        );
      }
      return;
    }

    if (event instanceof NavigationError) {
      const navigation = this.take(event.id);
      if (navigation) {
        const recognized = navigation.route !== undefined;
        this.record(navigation, navigation.route ?? UNRECOGNIZED_ROUTE, (scenario, metadata) =>
          scenario.fail({
            error: recognized ? event.error : unrecognizedError(event.error),
            metadata
          })
        );
      }
    }
  }

  /**
   * Starts and settles the scenario in one go, backdated to the journey's
   * start, once the final route template is known.
   */
  private record(
    navigation: TrackedNavigation,
    route: string,
    settle: (scenario: UwtScenario, metadata: Record<string, string | number>) => void
  ): void {
    const metadata: Record<string, string | number> = {};
    if (navigation.redirectedFrom) {
      metadata['redirectedFrom'] = navigation.redirectedFrom;
    }
    if (navigation.recognizedAt !== undefined) {
      metadata['resolveMs'] = Date.now() - navigation.recognizedAt;
    }
    settle(
      this.scenarioTelemetry.start({
        name: NAVIGATION_SCENARIO,
        route,
        startedAt: navigation.startedAt
      }),
      metadata
    );
  }

  /**
   * Consumes the click timestamp, if fresh enough.
   *
   * @returns epoch ms to backdate to: the click, or now
   */
  private navigationStartedAt(): number {
    const at = this.navigationIntentAt;
    this.navigationIntentAt = undefined;
    const now = Date.now();

    return at === undefined || now - at > INTENT_MAX_AGE_MS ? now : at;
  }

  private consumePendingRedirect(): RedirectCarry | undefined {
    const redirect = this.pendingRedirect;
    this.pendingRedirect = undefined;
    return redirect;
  }

  private take(navigationId: number): TrackedNavigation | undefined {
    const navigation = this.navigations.get(navigationId);
    this.navigations.delete(navigationId);
    return navigation;
  }
}
