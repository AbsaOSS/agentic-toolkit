import { isPlatformBrowser } from '@angular/common';
import {
  DestroyRef,
  inject,
  Injectable,
  InjectionToken,
  NgZone,
  PLATFORM_ID
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
import {
  UwtScenario,
  UwtScenarioTelemetryService
} from '@absaoss-cps/ngx-ui-watchtower';
// Side-effect import: the vocabulary declaring the names used below.
import './telemetry.schema';

/**
 * Records one page view per completed navigation, under the route template. Bind it to
 * `UwtRumTelemetrySink.recordPageView` only where RUM is the destination, with
 * `disableAutoPageView: true` — automatic page views report the resolved path (`/customers/42`).
 */
export const ROUTE_PAGE_VIEW_RECORDER = new InjectionToken<(route: string) => void>(
  'ROUTE_PAGE_VIEW_RECORDER'
);

const NAVIGATION_SCENARIO = 'route-navigation';

/** Beyond this, a recorded click is assumed not to have caused the navigation. */
const INTENT_MAX_AGE_MS = 2_000;

/** No end event in this window (a guard, resolver or chunk that never settles) → `timeout`. */
const NAVIGATION_TIMEOUT_MS = 30_000;

/** `route` of a navigation that failed before its URL matched a route. */
const UNRECOGNIZED_ROUTE = '(unrecognized)';

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

/** A class-like name (`ChunkLoadError`); any other `name` could be free text. */
const SAFE_ERROR_NAME = /^[A-Z][A-Za-z0-9]{0,63}$/;

/**
 * Router, resolver and lazy-chunk errors can quote URLs, parameters or user data, and path
 * segments are not redacted — so keep only a class-like name and an HTTP status.
 */
function safeNavigationFailure(
  error: unknown,
  recognized: boolean
): { error: Error; statusCode?: number } {
  const safe = new Error(
    recognized ? 'Navigation failed' : 'Navigation failed before the URL matched a route'
  );
  const { name, status } = (error ?? {}) as { name?: unknown; status?: unknown };
  if (typeof name === 'string' && SAFE_ERROR_NAME.test(name)) {
    safe.name = name;
  }
  return { error: safe, statusCode: typeof status === 'number' ? status : undefined };
}

interface TrackedNavigation {
  /** Epoch ms: the click, `NavigationStart`, or the start of a redirect chain. */
  startedAt: number;
  /** Template a guard or resolver redirected away from. */
  redirectedFrom?: string;
  /** Matched template, known from `RoutesRecognized`. */
  route?: string;
  /** `RoutesRecognized` time — guards, resolvers and lazy components run after it. */
  recognizedAt?: number;
  timeoutHandle?: ReturnType<typeof setTimeout>;
}

/** What a guard or resolver redirect carries into the next navigation. */
type RedirectCarry = Pick<TrackedNavigation, 'startedAt' | 'redirectedFrom'>;

/**
 * One `route-navigation` scenario per navigation, recorded when it ends — `route` can't change
 * after a scenario starts, and only the end knows the final template — and backdated to the click
 * or the first `NavigationStart`. Call {@link start} once from the root component; call
 * {@link markNavigationIntent} from nav-link click handlers.
 */
@Injectable({ providedIn: 'root' })
export class RouteNavigationTelemetryService {
  private readonly router = inject(Router);
  private readonly scenarioTelemetry = inject(UwtScenarioTelemetryService);
  private readonly recordPageView = inject(ROUTE_PAGE_VIEW_RECORDER, { optional: true });
  private readonly destroyRef = inject(DestroyRef);
  private readonly zone = inject(NgZone);
  private readonly isBrowser = isPlatformBrowser(inject(PLATFORM_ID));

  /** By navigation id, never one "current" field: navigations supersede each other. */
  private readonly navigations = new Map<number, TrackedNavigation>();

  private pendingRedirect?: RedirectCarry;
  private navigationIntentAt?: number;

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
    this.destroyRef.onDestroy(() => {
      for (const navigation of this.navigations.values()) {
        clearTimeout(navigation.timeoutHandle);
      }
    });
  }

  /** `NavigationStart` comes after event handling and change detection; count that wait too. */
  markNavigationIntent(): void {
    this.navigationIntentAt = Date.now();
  }

  private onRouterEvent(event: RouterEvent): void {
    if (event instanceof NavigationStart) {
      const startedAt = this.navigationStartedAt();
      const redirect = this.consumePendingRedirect();
      const navigation: TrackedNavigation = {
        startedAt: redirect?.startedAt ?? startedAt,
        redirectedFrom: redirect?.redirectedFrom
      };
      this.navigations.set(event.id, navigation);
      this.armTimeout(event.id, navigation);
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
        // Restarts under a new id: carry the start so the journey stays one scenario.
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
      // A redirect back to the current URL ends here, not in a NavigationStart: release the carried
      // redirect, and drop the click intent so it can't backdate an unrelated navigation.
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
        const failure = safeNavigationFailure(event.error, navigation.route !== undefined);
        this.record(navigation, navigation.route ?? UNRECOGNIZED_ROUTE, (scenario, metadata) =>
          scenario.fail({ ...failure, metadata })
        );
      }
    }
  }

  /** Starts and settles the scenario at once, backdated to the journey's start. */
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

  /** The click time if fresh enough, else now; consumes the click. */
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

  /**
   * Records a hung navigation once as `timeout`; a late end event then finds nothing. Browser only
   * and outside Angular, so it never delays app stability or server rendering.
   */
  private armTimeout(navigationId: number, navigation: TrackedNavigation): void {
    if (!this.isBrowser) {
      return;
    }
    const remainingMs = Math.max(0, navigation.startedAt + NAVIGATION_TIMEOUT_MS - Date.now());
    navigation.timeoutHandle = this.zone.runOutsideAngular(() =>
      setTimeout(() => {
        const hung = this.take(navigationId);
        if (hung) {
          this.record(hung, hung.route ?? UNRECOGNIZED_ROUTE, (scenario, metadata) =>
            scenario.settle('timeout', { reason: 'navigation-timeout', metadata })
          );
        }
      }, remainingMs)
    );
  }

  private take(navigationId: number): TrackedNavigation | undefined {
    const navigation = this.navigations.get(navigationId);
    this.navigations.delete(navigationId);
    clearTimeout(navigation?.timeoutHandle);
    return navigation;
  }
}
