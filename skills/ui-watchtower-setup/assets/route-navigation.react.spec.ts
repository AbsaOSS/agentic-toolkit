// @vitest-environment jsdom
import { act, createElement } from 'react';
import { createRoot } from 'react-dom/client';
import {
  createMemoryRouter,
  MemoryRouter,
  redirect,
  useNavigate,
  type RouteObject
} from 'react-router';
import { NavigationScenario, RouteNavigationTracker } from './route-navigation-tracker';
import { bindDataRouter, routeTemplateOf, useRouteNavigationTelemetry } from './route-navigation.react';

interface Recorded {
  route: string;
  status: string;
  outcome?: { reason?: string; error?: Error; statusCode?: number; metadata?: Record<string, unknown> };
}

function deferred(): { promise: Promise<null>; resolve: () => void } {
  let resolve!: () => void;
  const promise = new Promise<null>((done) => (resolve = () => done(null)));
  return { promise, resolve };
}

describe('React Router binding', () => {
  let recorded: Recorded[];
  let pageViews: string[];
  let tracker: RouteNavigationTracker;
  let slow: ReturnType<typeof deferred>;

  const routes: RouteObject[] = [
    {
      path: '/',
      children: [
        { index: true },
        { path: 'customers/:id' },
        { path: 'orders', loader: () => null },
        { path: 'slow', loader: () => slow.promise },
        { path: 'admin', loader: () => redirect('/login') },
        { path: 'login' },
        {
          path: 'broken',
          loader: () => {
            throw Object.assign(new Error('GET /api/customers/42 failed'), {
              name: 'HttpErrorResponse',
              status: 500
            });
          }
        }
      ]
    }
  ];

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

  beforeEach(() => {
    recorded = [];
    pageViews = [];
    slow = deferred();
    tracker = new RouteNavigationTracker({
      startScenario: ({ route }) => scenario(route),
      recordPageView: (route) => pageViews.push(route)
    });
  });

  afterEach(() => tracker.dispose());

  function bound(initialEntries = ['/']) {
    const router = createMemoryRouter(routes, { initialEntries });
    const unbind = bindDataRouter(router, tracker);
    return { router, unbind };
  }

  it('records the initial navigation, and one without a loader, under their templates', async () => {
    const { router, unbind } = bound();
    await router.navigate('/customers/42');

    expect(recorded.map((r) => [r.route, r.status])).toEqual([
      ['/', 'success'],
      ['/customers/:id', 'success']
    ]);
    expect(pageViews).toEqual(['/', '/customers/:id']);
    expect(JSON.stringify(recorded)).not.toContain('42');
    unbind();
  });

  it('records a navigation with a loader when the loader settles', async () => {
    const { router, unbind } = bound();
    await router.navigate('/orders');

    expect(recorded.at(-1)).toMatchObject({ route: '/orders', status: 'success' });
    expect(recorded.at(-1)?.outcome?.metadata).toHaveProperty('resolveMs');
    unbind();
  });

  it('records a loader redirect as one scenario under the final template', async () => {
    const { router, unbind } = bound();
    await router.navigate('/admin');

    expect(recorded.slice(1)).toEqual([
      expect.objectContaining({
        route: '/login',
        status: 'success',
        outcome: { metadata: expect.objectContaining({ redirectedFrom: '/admin' }) }
      })
    ]);
    unbind();
  });

  it('records a superseded navigation as abandoned, and the new one as success', async () => {
    const { router, unbind } = bound();
    void router.navigate('/slow');
    await router.navigate('/orders');
    slow.resolve();

    expect(recorded.slice(1).map((r) => [r.route, r.status, r.outcome?.reason])).toEqual([
      ['/slow', 'abandoned', 'superseded'],
      ['/orders', 'success', undefined]
    ]);
    unbind();
  });

  it('records a loader error as a failure, keeping only its name and status', async () => {
    const { router, unbind } = bound();
    await router.navigate('/broken');

    const failure = recorded.at(-1);
    expect(failure).toMatchObject({ route: '/broken', status: 'failure' });
    expect(failure?.outcome?.error?.name).toBe('HttpErrorResponse');
    expect(failure?.outcome?.statusCode).toBe(500);
    expect(JSON.stringify(recorded)).not.toContain('/api/');
    unbind();
  });

  it('records an unmatched URL as a failure under (unrecognized), with no URL in it', async () => {
    const { router, unbind } = bound();
    await router.navigate('/nope/42');

    expect(recorded.at(-1)).toMatchObject({ route: '(unrecognized)', status: 'failure' });
    expect(recorded.at(-1)?.outcome?.statusCode).toBe(404);
    expect(JSON.stringify(recorded)).not.toContain('nope');
    unbind();
  });

  it('records a first page whose loader is still running once it settles', async () => {
    const { router, unbind } = bound(['/slow']);
    expect(recorded).toEqual([]);
    slow.resolve();
    await vi.waitFor(() => expect(router.state.initialized).toBe(true));

    expect(recorded).toMatchObject([{ route: '/slow', status: 'success' }]);
    unbind();
  });

  it('builds templates from relative, absolute and index routes', () => {
    expect(routeTemplateOf([{ route: { path: '/' } }, { route: {} }])).toBe('/');
    expect(
      routeTemplateOf([{ route: { path: '/' } }, { route: { path: 'a/:id' } }, { route: { path: 'b' } }])
    ).toBe('/a/:id/b');
    expect(routeTemplateOf([{ route: { path: 'x' } }, { route: { path: '/abs/:id' } }])).toBe(
      '/abs/:id'
    );
    expect(routeTemplateOf(null)).toBe('(unrecognized)');
  });

  it('records each location once with a declarative router', async () => {
    let goTo: (to: string) => void = () => undefined;
    function Telemetry() {
      useRouteNavigationTelemetry(tracker, routes);
      goTo = useNavigate();
      return null;
    }
    (globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }).IS_REACT_ACT_ENVIRONMENT = true;
    const root = createRoot(document.createElement('div'));
    await act(async () =>
      root.render(
        createElement(MemoryRouter, { initialEntries: ['/'] }, createElement(Telemetry))
      )
    );
    await act(async () => goTo('/customers/7'));

    expect(recorded.map((r) => [r.route, r.status])).toEqual([
      ['/', 'success'],
      ['/customers/:id', 'success']
    ]);
    await act(async () => root.unmount());
  });
});
