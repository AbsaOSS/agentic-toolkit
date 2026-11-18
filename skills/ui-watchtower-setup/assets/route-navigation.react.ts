// React Router 7 exports these from 'react-router'; with React Router 6, import them from
// 'react-router-dom'.
import { useEffect, useRef } from 'react';
import { matchRoutes, useLocation } from 'react-router';
import {
  RouteNavigationTracker,
  UNRECOGNIZED_ROUTE
} from './route-navigation-tracker';

/** The parts of a React Router route object a template is built from. */
interface RouteLike {
  path?: string;
  children?: RouteLike[];
}

interface LocationLike {
  pathname: string;
  key: string;
  state?: unknown;
}

/** The parts of a data router (`createBrowserRouter`) the binding reads. */
interface DataRouterLike {
  readonly routes: RouteLike[];
  readonly state: DataRouterStateLike;
  subscribe(listener: (state: DataRouterStateLike) => void): () => void;
}

interface DataRouterStateLike {
  initialized: boolean;
  location: LocationLike;
  matches: { route: RouteLike }[];
  navigation: { state: 'idle' | 'loading' | 'submitting'; location?: LocationLike };
  errors: Record<string, unknown> | null;
}

/**
 * Template of a match chain: `/customers/:id`. Child paths are relative to their parent unless
 * absolute; index routes and pathless layouts add nothing.
 */
export function routeTemplateOf(matches: readonly { route: RouteLike }[] | null): string {
  if (!matches?.length) {
    return UNRECOGNIZED_ROUTE;
  }
  let template = '';
  for (const { route } of matches) {
    if (route.path) {
      template = route.path.startsWith('/') ? route.path : `${template}/${route.path}`;
    }
  }
  return template.replace(/\/{2,}/g, '/').replace(/(.)\/$/, '$1') || '/';
}

/** React Router marks a loader or action redirect on the location it navigates to. */
function isRedirect(location: LocationLike): boolean {
  return (location.state as { _isRedirect?: boolean } | null)?._isRedirect === true;
}

/**
 * Binds a data router (`createBrowserRouter`, `createMemoryRouter`) to the tracker: a navigation
 * starts when the router starts loading, and ends when it settles, or at once when no loader
 * runs. Call it right after creating the router, before rendering, so the initial navigation
 * counts. Returns the unsubscribe function.
 */
export function bindDataRouter(
  router: DataRouterLike,
  tracker: RouteNavigationTracker
): () => void {
  let sequence = 0;
  let current: { id: number; target: LocationLike } | undefined;
  let lastLocationKey = router.state.location.key;

  const begin = (target: LocationLike) => {
    const id = ++sequence;
    current = { id, target };
    tracker.start(id);
    const matches = matchRoutes(router.routes, target);
    if (matches) {
      tracker.recognized(id, routeTemplateOf(matches));
    }
  };

  /** Ends the current navigation as the settled `state` shows it. */
  const settle = (state: DataRouterStateLike) => {
    if (!current) {
      return;
    }
    const { id, target } = current;
    current = undefined;
    const error = state.errors ? Object.values(state.errors)[0] : undefined;
    if (error !== undefined) {
      tracker.fail(id, error);
    } else if (state.location.key === target.key) {
      tracker.end(id, routeTemplateOf(state.matches));
    } else if (isRedirect(state.location)) {
      // Redirected to a page without a loader: it settled in the same update.
      tracker.redirected(id);
      const next = ++sequence;
      tracker.start(next);
      tracker.end(next, routeTemplateOf(state.matches));
    } else {
      // Settled without moving (e.g. a blocker kept the user on the page).
      tracker.cancel(id, { reason: 'blocked', incomplete: true });
    }
  };

  // The initial navigation: still loading when the first page has loaders, else already done.
  begin(router.state.location);
  if (router.state.initialized) {
    settle(router.state);
  }

  return router.subscribe((state) => {
    const { navigation } = state;
    if (navigation.state !== 'idle' && navigation.location) {
      if (current && current.target.key !== navigation.location.key) {
        // Replaced before it settled: by its own redirect, or by a newer navigation.
        if (isRedirect(navigation.location)) {
          tracker.redirected(current.id);
        } else {
          tracker.cancel(current.id, { reason: 'superseded' });
        }
        current = undefined;
      }
      if (!current) {
        begin(navigation.location);
      }
      return;
    }

    const changed = state.location.key !== lastLocationKey;
    lastLocationKey = state.location.key;
    if (!current && changed) {
      // No loader ran: the navigation started and ended in this one update.
      begin(state.location);
    }
    if (state.initialized) {
      settle(state);
    }
  });
}

/**
 * For a declarative router (`<BrowserRouter>`, no data router): it has no navigation events, so
 * each navigation is recorded when its location renders, from the click (`markIntent`) when
 * there was one. `routes` is the app's route objects, as passed to `useRoutes` or produced by
 * `createRoutesFromElements`. Call it once, in a component inside the router.
 */
export function useRouteNavigationTelemetry(
  tracker: RouteNavigationTracker,
  routes: RouteLike[]
): void {
  const location = useLocation();
  // Once per location, even when the effect runs again (StrictMode, a new `routes` array).
  const recordedKey = useRef<string | undefined>(undefined);
  useEffect(() => {
    if (recordedKey.current === location.key) {
      return;
    }
    recordedKey.current = location.key;
    tracker.start(location.key);
    tracker.end(location.key, routeTemplateOf(matchRoutes(routes, location)));
  }, [location, routes, tracker]);
}
