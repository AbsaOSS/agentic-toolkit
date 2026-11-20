import {
  NAVIGATION_SCENARIO,
  NavigationScenario,
  RouteNavigationTracker,
  UNRECOGNIZED_ROUTE
} from './route-navigation-tracker';

interface Recorded {
  name: string;
  route: string;
  startedAt: number;
  status: string;
  outcome?: { reason?: string; error?: Error; statusCode?: number; metadata?: Record<string, unknown> };
}

describe('RouteNavigationTracker', () => {
  let recorded: Recorded[];
  let pageViews: string[];
  let tracker: RouteNavigationTracker;

  function scenario(entry: Omit<Recorded, 'status'>): NavigationScenario {
    const settle = (status: string) => (outcome?: Recorded['outcome']) =>
      recorded.push({ ...entry, status, outcome });
    return {
      complete: settle('success'),
      cancel: settle('abandoned'),
      incomplete: settle('incomplete'),
      fail: settle('failure'),
      settle: (status, outcome) => settle(status)(outcome)
    };
  }

  beforeEach(() => {
    vi.useFakeTimers();
    vi.setSystemTime(1_000_000);
    recorded = [];
    pageViews = [];
    tracker = new RouteNavigationTracker({
      startScenario: (options) => scenario(options),
      recordPageView: (route) => pageViews.push(route),
      inBrowser: true
    });
  });

  afterEach(() => {
    tracker.dispose();
    vi.useRealTimers();
  });

  it('records a completed navigation under its template, with one page view', () => {
    tracker.start(1);
    tracker.recognized(1, '/customers/:id');
    vi.advanceTimersByTime(40);
    tracker.end(1);

    expect(recorded).toEqual([
      {
        name: NAVIGATION_SCENARIO,
        route: '/customers/:id',
        startedAt: 1_000_000,
        status: 'success',
        outcome: { metadata: { resolveMs: 40 } }
      }
    ]);
    expect(pageViews).toEqual(['/customers/:id']);
  });

  it('takes the template given at the end, for routers that only know it then', () => {
    tracker.start('key-1');
    tracker.end('key-1', '/orders');

    expect(recorded).toMatchObject([{ route: '/orders', status: 'success' }]);
  });

  it('backdates to a recent click, and ignores one older than 2 s', () => {
    tracker.markIntent();
    vi.advanceTimersByTime(300);
    tracker.start(1);
    tracker.end(1, '/a');

    tracker.markIntent();
    vi.advanceTimersByTime(2_500);
    tracker.start(2);
    tracker.end(2, '/b');

    expect(recorded.map((r) => r.startedAt)).toEqual([1_000_000, 1_002_800]);
  });

  it('records a redirect as one scenario under the final template, from where it started', () => {
    tracker.start(1);
    tracker.recognized(1, '/admin');
    vi.advanceTimersByTime(100);
    tracker.redirected(1);
    tracker.start(2);
    tracker.recognized(2, '/login');
    tracker.end(2);

    expect(recorded).toHaveLength(1);
    expect(recorded[0]).toMatchObject({
      route: '/login',
      startedAt: 1_000_000,
      status: 'success',
      outcome: { metadata: { redirectedFrom: '/admin' } }
    });
  });

  it('records a guard rejection as incomplete and a superseded navigation as abandoned', () => {
    tracker.start(1);
    tracker.recognized(1, '/admin');
    tracker.cancel(1, { reason: 'guard-rejected', incomplete: true });
    tracker.start(2);
    tracker.recognized(2, '/reports');
    tracker.cancel(2, { reason: 'superseded' });

    expect(recorded.map((r) => [r.route, r.status, r.outcome?.reason])).toEqual([
      ['/admin', 'incomplete', 'guard-rejected'],
      ['/reports', 'abandoned', 'superseded']
    ]);
  });

  it('records nothing for a navigation cancelled before its URL was recognized', () => {
    tracker.start(1);
    tracker.cancel(1, { reason: 'superseded' });

    expect(recorded).toEqual([]);
  });

  it('releases a redirect back to the current URL as abandoned under its source template', () => {
    tracker.start(1);
    tracker.recognized(1, '/admin');
    tracker.redirected(1);
    tracker.skip(2, 'same-url');

    expect(recorded).toMatchObject([
      { route: '/admin', status: 'abandoned', outcome: { reason: 'same-url' } }
    ]);
  });

  it('keeps only a class-like error name and an HTTP status from a failure', () => {
    tracker.start(1);
    tracker.recognized(1, '/customers/:id');
    tracker.fail(1, Object.assign(new Error('GET /api/customers/42 failed'), {
      name: 'HttpErrorResponse',
      status: 404
    }));
    tracker.start(2);
    tracker.fail(2, { name: 'not a class name', message: 'user@example.com' });

    expect(recorded[0]).toMatchObject({ route: '/customers/:id', status: 'failure' });
    expect(recorded[0].outcome?.error?.name).toBe('HttpErrorResponse');
    expect(recorded[0].outcome?.statusCode).toBe(404);
    expect(recorded[1]).toMatchObject({ route: UNRECOGNIZED_ROUTE, status: 'failure' });
    expect(recorded[1].outcome?.error?.name).toBe('Error');
    expect(JSON.stringify(recorded)).not.toMatch(/42|example\.com/);
  });

  it('records a hung navigation once as timeout, and only its page view when it ends late', () => {
    tracker.start(1);
    tracker.recognized(1, '/reports');
    vi.advanceTimersByTime(30_000);
    tracker.end(1);

    expect(recorded).toMatchObject([
      { route: '/reports', status: 'timeout', outcome: { reason: 'navigation-timeout' } }
    ]);
    expect(pageViews).toEqual(['/reports']);
  });

  it('arms no timeout outside a browser, and clears pending ones on dispose', () => {
    const server = new RouteNavigationTracker({
      startScenario: (options) => scenario(options),
      inBrowser: false
    });
    server.start(1);
    tracker.start(2);
    tracker.dispose();
    vi.advanceTimersByTime(60_000);

    expect(recorded).toEqual([]);
  });

  it('schedules its timeout through runOutside when given one', () => {
    let scheduled = 0;
    const zoned = new RouteNavigationTracker({
      startScenario: (options) => scenario(options),
      runOutside: (callback) => {
        scheduled++;
        return callback();
      },
      inBrowser: true
    });
    zoned.start(1);

    expect(scheduled).toBe(1);
    zoned.dispose();
  });
});
