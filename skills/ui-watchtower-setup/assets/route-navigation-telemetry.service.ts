import { DestroyRef, inject, Injectable } from '@angular/core';
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

/** Name shared by every route-navigation scenario. */
const NAVIGATION_SCENARIO = 'route-navigation';

/** Beyond this, a recorded click is assumed not to have caused the navigation. */
const INTENT_MAX_AGE_MS = 2_000;

/**
 * Neither completed nor superseded within this window means a stuck chunk
 * load, not a slow one.
 */
const NAVIGATION_TIMEOUT_MS = 30_000;

/** `route` of a navigation whose URL matched no route. */
const UNRECOGNIZED_ROUTE = '(unrecognized)';

/**
 * Route `data` key naming a `matcher` route's segment in the template — a
 * matcher has no `path` to report.
 */
const TELEMETRY_PATH_DATA_KEY = 'telemetryPath';

/**
 * Stable, low-cardinality causes, derived from the router's `code`. The
 * router's `reason` text is dev-mode only — empty in a production build — so
 * it can't be the grouping key.
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
 * outlet: `/customers/42` → `/customers/:id`. Exact after redirects and lazy
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

/** One router navigation being tracked. */
interface TrackedNavigation {
  /** Epoch ms the journey started: the click, or `NavigationStart`. */
  startedAt: number;
  /** Started once the URL is recognized — the route template is known only then. */
  scenario?: UwtScenario;
}

/**
 * Measures every router navigation as a `route-navigation` scenario.
 *
 * The scenario starts when the router has recognized the URL, so `route` is
 * the matched template (`/customers/:id`), and is backdated to the click or
 * `NavigationStart`, so the duration covers the whole wait.
 *
 * Call {@link start} once, from the root component's constructor. Call
 * {@link markNavigationIntent} from navigation-link click handlers.
 */
@Injectable({ providedIn: 'root' })
export class RouteNavigationTelemetryService {
  private readonly router = inject(Router);
  private readonly scenarioTelemetry = inject(UwtScenarioTelemetryService);
  private readonly destroyRef = inject(DestroyRef);

  /**
   * Keyed by navigation id, never a single "current" field: one navigation
   * can supersede another, and a single field would attribute the wrong
   * duration.
   */
  private readonly navigations = new Map<number, TrackedNavigation>();

  /** A redirected navigation's scenario, continued by the next navigation. */
  private pendingRedirectScenario?: UwtScenario;

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
      this.navigations.set(event.id, {
        startedAt: this.navigationStartedAt(),
        scenario: this.consumePendingRedirectScenario()
      });
      return;
    }

    if (event instanceof RoutesRecognized) {
      const navigation = this.navigations.get(event.id);
      if (navigation) {
        navigation.scenario ??= this.startScenario(
          navigation.startedAt,
          routeTemplateOf(event.state.root)
        );
        navigation.scenario.step('resolve-route');
      }
      return;
    }

    if (event instanceof NavigationEnd) {
      this.settle(event.id, (scenario) => {
        scenario.step('activate');
        scenario.complete({
          metadata: {
            finalRoute: routeTemplateOf(this.router.routerState.snapshot.root)
          }
        });
      });
      return;
    }

    if (event instanceof NavigationCancel) {
      const scenario = this.navigations.get(event.id)?.scenario;
      if (scenario && event.code === NavigationCancellationCode.Redirect) {
        // A redirect restarts under a new id: continue this scenario on the
        // next NavigationStart, so one journey stays one scenario.
        this.navigations.delete(event.id);
        this.pendingRedirectScenario = scenario;
        return;
      }

      const outcome = {
        reason: causeOf(CANCEL_REASON, event.code, 'navigation-cancelled'),
        message: event.reason || undefined
      };
      this.settle(event.id, (scenario) =>
        event.code !== undefined && INCOMPLETE_CODES.has(event.code)
          ? scenario.incomplete(outcome)
          : scenario.cancel(outcome)
      );
      return;
    }

    if (event instanceof NavigationSkipped) {
      // A redirect back to the current URL ends in NavigationSkipped instead
      // of the NavigationStart the stashed scenario waits for. Release it, and
      // drop the click intent so it can't backdate an unrelated navigation.
      this.navigationIntentAt = undefined;
      const outcome = {
        reason: causeOf(SKIP_REASON, event.code, 'navigation-skipped'),
        message: event.reason || undefined
      };
      this.consumePendingRedirectScenario()?.cancel(outcome);
      this.settle(event.id, (scenario) => scenario.cancel(outcome));
      return;
    }

    if (event instanceof NavigationError) {
      // An unmatched URL fails before recognition, so no scenario exists yet.
      const navigation = this.navigations.get(event.id);
      if (navigation && !navigation.scenario) {
        navigation.scenario = this.startScenario(
          navigation.startedAt,
          UNRECOGNIZED_ROUTE
        );
      }
      this.settle(event.id, (scenario) =>
        scenario.fail({ error: event.error })
      );
    }
  }

  private startScenario(startedAt: number, route: string): UwtScenario {
    return this.scenarioTelemetry.start({
      name: NAVIGATION_SCENARIO,
      route,
      startedAt,
      timeoutMs: NAVIGATION_TIMEOUT_MS
    });
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

  private consumePendingRedirectScenario(): UwtScenario | undefined {
    const scenario = this.pendingRedirectScenario;
    this.pendingRedirectScenario = undefined;
    return scenario;
  }

  /**
   * Ends tracking of one navigation. One that never reached recognition
   * (superseded or skipped first) has no scenario and records nothing — it
   * would only spend the session's event budget.
   */
  private settle(
    navigationId: number,
    apply: (scenario: UwtScenario) => void
  ): void {
    const scenario = this.navigations.get(navigationId)?.scenario;
    this.navigations.delete(navigationId);
    if (scenario) {
      apply(scenario);
    }
  }
}
