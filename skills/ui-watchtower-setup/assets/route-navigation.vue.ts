import {
  isNavigationFailure,
  NavigationFailureType,
  type RouteLocationNormalized,
  type Router
} from 'vue-router';
import {
  RouteNavigationTracker,
  UNRECOGNIZED_ROUTE
} from './route-navigation-tracker';

/** The matched record's full path: `/customers/:id`, the template, never the resolved URL. */
export function routeTemplateOf(route: RouteLocationNormalized): string {
  return route.matched[route.matched.length - 1]?.path ?? UNRECOGNIZED_ROUTE;
}

/**
 * Binds a Vue Router to the tracker. Call it right after `createRouter(...)`, before
 * `app.use(router)`, so the initial navigation counts. Returns a function that removes the
 * router hooks.
 */
export function bindVueRouter(router: Router, tracker: RouteNavigationTracker): () => void {
  // Each navigation's own `to` object reaches beforeEach, afterEach and onError, and is the
  // `redirectedFrom` of the navigation a guard redirects it to.
  const ids = new WeakMap<object, number>();
  let sequence = 0;

  const removeBefore = router.beforeEach((to) => {
    // A guard redirect: the journey goes on under the new target.
    const redirectedId = to.redirectedFrom ? ids.get(to.redirectedFrom) : undefined;
    if (redirectedId !== undefined) {
      tracker.redirected(redirectedId);
    }
    const id = ++sequence;
    ids.set(to, id);
    tracker.start(id);
    tracker.recognized(id, routeTemplateOf(to));
  });

  const removeAfter = router.afterEach((to, _from, failure) => {
    const id = ids.get(to);
    if (id === undefined) {
      // A navigation to the current location never reaches beforeEach: nothing to record.
      return;
    }
    ids.delete(to);
    if (!failure) {
      tracker.end(id);
    } else if (isNavigationFailure(failure, NavigationFailureType.aborted)) {
      // A guard returned false.
      tracker.cancel(id, { reason: 'guard-rejected', incomplete: true });
    } else if (isNavigationFailure(failure, NavigationFailureType.cancelled)) {
      tracker.cancel(id, { reason: 'superseded' });
    } else if (isNavigationFailure(failure, NavigationFailureType.duplicated)) {
      tracker.skip(id, 'same-url');
    } else {
      tracker.cancel(id, { reason: 'navigation-cancelled' });
    }
  });

  const removeError = router.onError((error, to) => {
    const id = ids.get(to);
    if (id !== undefined) {
      ids.delete(to);
      tracker.fail(id, error);
    }
  });

  return () => {
    removeBefore();
    removeAfter();
    removeError();
  };
}
