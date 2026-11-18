import { createMemoryHistory, createRouter, type Router } from 'vue-router';
import { NavigationScenario, RouteNavigationTracker } from './route-navigation-tracker';
import { bindVueRouter } from './route-navigation.vue';

interface Recorded {
  route: string;
  status: string;
  outcome?: { reason?: string; error?: Error; statusCode?: number; metadata?: Record<string, unknown> };
}

const Page = { render: () => null };

describe('Vue Router binding', () => {
  let recorded: Recorded[];
  let pageViews: string[];
  let tracker: RouteNavigationTracker;
  let router: Router;
  let unbind: () => void;
  let releaseSlowGuard: () => void;
  let slowGuardEntered: Promise<void>;
  let enterSlowGuard: () => void;

  function scenario(route: string): NavigationScenario {
    const settle = (status: string) => (outcome?: Recorded['outcome']) =>
      recorded.push({ route, status, outcome });
    return {
      complete: settle('success'),
      cancel: settle('abandoned'),
      incomplete: settle('incomplete'),
      fail: settle('failure'),
      settle: (status, outcome) => settle(status)(outcome)
    };
  }

  beforeEach(async () => {
    recorded = [];
    pageViews = [];
    tracker = new RouteNavigationTracker({
      startScenario: ({ route }) => scenario(route),
      recordPageView: (route) => pageViews.push(route)
    });
    router = createRouter({
      history: createMemoryHistory(),
      routes: [
        { path: '/', component: Page },
        { path: '/customers/:id', component: Page },
        { path: '/orders', component: Page },
        { path: '/login', component: Page },
        { path: '/admin', component: Page, beforeEnter: () => '/login' },
        { path: '/closed', component: Page, beforeEnter: () => false },
        {
          path: '/slow',
          component: Page,
          beforeEnter: () => {
            enterSlowGuard();
            return new Promise<boolean>((resolve) => (releaseSlowGuard = () => resolve(true)));
          }
        },
        {
          path: '/broken',
          component: Page,
          beforeEnter: () => {
            throw Object.assign(new Error('GET /api/customers/42 failed'), {
              name: 'HttpErrorResponse',
              status: 500
            });
          }
        }
      ]
    });
    slowGuardEntered = new Promise((resolve) => (enterSlowGuard = resolve));
    unbind = bindVueRouter(router, tracker);
    await router.push('/');
    recorded.length = 0;
    pageViews.length = 0;
  });

  afterEach(() => {
    unbind();
    tracker.dispose();
  });

  it('records a navigation under its template, never the id, with one page view', async () => {
    await router.push('/customers/42');

    expect(recorded).toEqual([
      expect.objectContaining({ route: '/customers/:id', status: 'success' })
    ]);
    expect(pageViews).toEqual(['/customers/:id']);
    expect(JSON.stringify(recorded)).not.toContain('42');
  });

  it('records a guard rejection as incomplete', async () => {
    await router.push('/closed');

    expect(recorded).toMatchObject([
      { route: '/closed', status: 'incomplete', outcome: { reason: 'guard-rejected' } }
    ]);
  });

  it('records a guard redirect as one scenario under the final template', async () => {
    await router.push('/admin');

    expect(recorded).toEqual([
      expect.objectContaining({
        route: '/login',
        status: 'success',
        outcome: { metadata: expect.objectContaining({ redirectedFrom: '/admin' }) }
      })
    ]);
  });

  it('records a superseded navigation as abandoned, and the new one as success', async () => {
    const first = router.push('/slow');
    await slowGuardEntered;
    await router.push('/orders');
    releaseSlowGuard();
    await first;

    expect(recorded.map((r) => [r.route, r.status, r.outcome?.reason])).toEqual([
      ['/orders', 'success', undefined],
      ['/slow', 'abandoned', 'superseded']
    ]);
  });

  it('records a guard error as a failure, keeping only its name and status', async () => {
    await router.push('/broken').catch(() => undefined);

    expect(recorded).toHaveLength(1);
    expect(recorded[0]).toMatchObject({ route: '/broken', status: 'failure' });
    expect(recorded[0].outcome?.error?.name).toBe('HttpErrorResponse');
    expect(recorded[0].outcome?.statusCode).toBe(500);
    expect(JSON.stringify(recorded)).not.toContain('/api/');
  });

  it('records nothing for a navigation to the current location', async () => {
    await router.push('/');

    expect(recorded).toEqual([]);
  });

  it('records the initial navigation when bound before it', async () => {
    const fresh = createRouter({
      history: createMemoryHistory(),
      routes: [{ path: '/customers/:id', component: Page }]
    });
    const unbindFresh = bindVueRouter(fresh, tracker);
    await fresh.push('/customers/1');

    expect(recorded).toMatchObject([{ route: '/customers/:id', status: 'success' }]);
    unbindFresh();
  });
});
