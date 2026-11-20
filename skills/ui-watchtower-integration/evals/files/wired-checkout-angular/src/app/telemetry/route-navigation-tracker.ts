// Side-effect import: the vocabulary declaring the scenario name used below.
import './telemetry.schema';

/**
 * Route-navigation telemetry, independent of any framework and of which ui-watchtower package
 * the app uses. One `NAVIGATION_SCENARIO` scenario per navigation, under the route TEMPLATE
 * (`/customers/:id`), never the resolved URL. A router binding turns its router's events into
 * the calls below: `route-navigation.angular.ts` for the Angular Router, or a small one written
 * for the app's own router. Used only when the app opts into route-navigation tracking.
 */

/** `<prefix>-route-navigate`, with this app's prefix, as declared in telemetry.schema.ts. */
export const NAVIGATION_SCENARIO = 'web-shop-route-navigate';

/** Beyond this, a recorded click is assumed not to have caused the navigation. */
const INTENT_MAX_AGE_MS = 2_000;

/** No end in this window (a guard, resolver, loader or chunk that never settles) → `timeout`. */
const NAVIGATION_TIMEOUT_MS = 30_000;

/** `route` of a navigation that failed before its URL matched a route. */
export const UNRECOGNIZED_ROUTE = '(unrecognized)';

/** A class-like name (`ChunkLoadError`); any other `name` could be free text. */
const SAFE_ERROR_NAME = /^[A-Z][A-Za-z0-9]{0,63}$/;

/** What the tracker settles: a ui-watchtower `UwtScenario` from either package. */
export interface NavigationScenario {
  complete(outcome?: NavigationOutcome): void;
  cancel(outcome?: NavigationOutcome): void;
  incomplete(outcome?: NavigationOutcome): void;
  fail(outcome?: NavigationOutcome): void;
  settle(status: 'timeout', outcome?: NavigationOutcome): void;
}

interface NavigationOutcome {
  reason?: string;
  error?: Error;
  statusCode?: number;
  metadata?: Record<string, string | number>;
}

export interface RouteNavigationTrackerOptions {
  /**
   * Starts the scenario: `(options) => telemetry.scenarios.start(options)` with the core, or
   * `(options) => inject(UwtScenarioTelemetryService).start(options)` in Angular.
   */
  startScenario(options: {
    name: typeof NAVIGATION_SCENARIO;
    route: string;
    startedAt: number;
  }): NavigationScenario;
  /**
   * One page view per completed navigation, under the template. Pass the RUM destination's
   * `recordPageView` only where RUM is the destination, with `disableAutoPageView: true` —
   * automatic page views report the resolved path (`/customers/42`).
   */
  recordPageView?(route: string): void;
  /** Schedules the timeout outside a framework's change detection (Angular's `NgZone`). */
  runOutside?<T>(callback: () => T): T;
  /** Arms timeouts only in a browser; default: whether there is a `window`. */
  inBrowser?: boolean;
}

/** How a navigation that didn't complete ended. */
export interface NavigationCancellation {
  /** Low-cardinality cause: `superseded`, `guard-rejected`, `blocked` … never router text. */
  reason: string;
  /** An expected dead end (a guard said no) → `incomplete`; otherwise → `abandoned`. */
  incomplete?: boolean;
}

export type NavigationId = string | number;

interface TrackedNavigation {
  /** Epoch ms: the click, the navigation's start, or the start of a redirect chain. */
  startedAt: number;
  /** Template a guard or loader redirected away from. */
  redirectedFrom?: string;
  /** Matched template, once known. */
  route?: string;
  /** When the template became known — guards, resolvers, loaders and lazy code run after it. */
  recognizedAt?: number;
  /** Already recorded (e.g. at its timeout): a late end adds only its page view. */
  recorded?: boolean;
  timeoutHandle?: ReturnType<typeof setTimeout>;
}

/** What a redirect carries into the navigation that replaces it. */
type RedirectCarry = Pick<TrackedNavigation, 'startedAt' | 'redirectedFrom' | 'recorded'>;

/**
 * Router, resolver, loader and lazy-chunk errors can quote URLs, parameters or user data, and
 * path segments are not redacted — so keep only a class-like name and an HTTP status.
 */
export function safeNavigationFailure(
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

/**
 * Records each navigation when it ends — a scenario's `route` can't change after it starts, and
 * only the end knows the final template — or at its timeout if it hasn't ended, backdated to the
 * click or the navigation's start. Navigations are kept by id, never in one "current" field:
 * they supersede each other.
 */
export class RouteNavigationTracker {
  private readonly navigations = new Map<NavigationId, TrackedNavigation>();
  private readonly inBrowser: boolean;
  private pendingRedirect?: RedirectCarry;
  private navigationIntentAt?: number;

  constructor(private readonly options: RouteNavigationTrackerOptions) {
    this.inBrowser = options.inBrowser ?? typeof window !== 'undefined';
  }

  /**
   * Call from click handlers that navigate: the router's start comes after event handling and
   * rendering, and the user's wait starts at the click.
   */
  markIntent(): void {
    this.navigationIntentAt = Date.now();
  }

  /** A navigation started. A redirect carried from the one it replaces keeps its start. */
  start(id: NavigationId): void {
    const startedAt = this.navigationStartedAt();
    const redirect = this.consumePendingRedirect();
    const navigation: TrackedNavigation = {
      startedAt: redirect?.startedAt ?? startedAt,
      redirectedFrom: redirect?.redirectedFrom,
      recorded: redirect?.recorded
    };
    this.navigations.set(id, navigation);
    if (!navigation.recorded) {
      this.armTimeout(id, navigation);
    }
  }

  /** Its URL matched `route` (a template); what runs from here on counts as `resolveMs`. */
  recognized(id: NavigationId, route: string): void {
    const navigation = this.navigations.get(id);
    if (navigation) {
      navigation.route = route;
      navigation.recognizedAt = Date.now();
    }
  }

  /** It completed — under `route` if given, else the recognized template — plus a page view. */
  end(id: NavigationId, route?: string): void {
    const navigation = this.take(id);
    const template = route ?? navigation?.route;
    if (navigation && template) {
      this.record(navigation, template, (scenario, metadata) => scenario.complete({ metadata }));
      this.options.recordPageView?.(template);
    }
  }

  /**
   * A redirect replaces it with a navigation under a new id: carry its start, so the journey
   * stays one scenario, recorded under the final template with `redirectedFrom`.
   */
  redirected(id: NavigationId): void {
    const navigation = this.take(id);
    if (navigation) {
      this.pendingRedirect = {
        startedAt: navigation.startedAt,
        redirectedFrom: navigation.redirectedFrom ?? navigation.route,
        recorded: navigation.recorded
      };
    }
  }

  /** It ended without completing. Recorded only once its URL was recognized. */
  cancel(id: NavigationId, cancellation: NavigationCancellation): void {
    const navigation = this.take(id);
    // Superseded before its URL was recognized: nothing to attribute it to.
    if (!navigation?.route) {
      return;
    }
    const { reason, incomplete } = cancellation;
    this.record(navigation, navigation.route, (scenario, metadata) =>
      incomplete ? scenario.incomplete({ reason, metadata }) : scenario.cancel({ reason, metadata })
    );
  }

  /**
   * The router never ran it (e.g. the current URL again). A redirect back to the current URL
   * ends here: release the carried redirect, and drop the click so it can't backdate an
   * unrelated navigation.
   */
  skip(id: NavigationId, reason: string): void {
    this.navigationIntentAt = undefined;
    const redirect = this.consumePendingRedirect();
    if (redirect?.redirectedFrom) {
      this.record(redirect, redirect.redirectedFrom, (scenario, metadata) =>
        scenario.cancel({ reason, metadata })
      );
    }
    const navigation = this.take(id);
    if (navigation?.route) {
      this.record(navigation, navigation.route, (scenario, metadata) =>
        scenario.cancel({ reason, metadata })
      );
    }
  }

  /** It failed; only a class-like error name and an HTTP status are kept. */
  fail(id: NavigationId, error: unknown): void {
    const navigation = this.take(id);
    if (navigation) {
      const failure = safeNavigationFailure(error, navigation.route !== undefined);
      this.record(navigation, navigation.route ?? UNRECOGNIZED_ROUTE, (scenario, metadata) =>
        scenario.fail({ ...failure, metadata })
      );
    }
  }

  /** Clears pending timeouts; for the router binding's teardown. */
  dispose(): void {
    for (const navigation of this.navigations.values()) {
      clearTimeout(navigation.timeoutHandle);
    }
    this.navigations.clear();
  }

  /** Starts and settles the scenario at once, backdated to the journey's start; once per journey. */
  private record(
    navigation: TrackedNavigation,
    route: string,
    settle: (scenario: NavigationScenario, metadata: Record<string, string | number>) => void
  ): void {
    if (navigation.recorded) {
      return;
    }
    navigation.recorded = true;
    const metadata: Record<string, string | number> = {};
    if (navigation.redirectedFrom) {
      metadata['redirectedFrom'] = navigation.redirectedFrom;
    }
    if (navigation.recognizedAt !== undefined) {
      metadata['resolveMs'] = Date.now() - navigation.recognizedAt;
    }
    settle(
      this.options.startScenario({
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

  /** Records a hung navigation once as `timeout`; a late end then adds only its page view. */
  private armTimeout(id: NavigationId, navigation: TrackedNavigation): void {
    if (!this.inBrowser) {
      return;
    }
    const remainingMs = Math.max(0, navigation.startedAt + NAVIGATION_TIMEOUT_MS - Date.now());
    const arm = () =>
      setTimeout(() => {
        const hung = this.navigations.get(id);
        if (hung) {
          this.record(hung, hung.route ?? UNRECOGNIZED_ROUTE, (scenario, metadata) =>
            scenario.settle('timeout', { reason: 'navigation-timeout', metadata })
          );
        }
      }, remainingMs);
    navigation.timeoutHandle = this.options.runOutside ? this.options.runOutside(arm) : arm();
  }

  private take(id: NavigationId): TrackedNavigation | undefined {
    const navigation = this.navigations.get(id);
    this.navigations.delete(id);
    clearTimeout(navigation?.timeoutHandle);
    return navigation;
  }
}
