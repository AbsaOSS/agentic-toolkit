import { AppRumCredentialsProvider } from './rum-credentials.provider';

const valid = {
  enabled: true,
  config: { applicationId: 'app-1', region: 'eu-west-1', applicationVersion: '1.4.0', sessionSampleRate: 1 },
  credentials: {
    accessKeyId: 'AKIA', secretAccessKey: 'secret', sessionToken: 'token',
    expiration: new Date(Date.now() + 3_600_000).toISOString()
  }
};

function answer(body: unknown, status = 200): void {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(
    new Response(typeof body === 'string' ? body : JSON.stringify(body), { status })
  ));
}

describe('AppRumCredentialsProvider', () => {
  afterEach(() => vi.unstubAllGlobals());
  const load = () => new AppRumCredentialsProvider().load();

  it('maps a complete answer and turns automatic page views off', async () => {
    answer(valid);
    await expect(load()).resolves.toEqual({
      config: {
        applicationId: 'app-1', region: 'eu-west-1', applicationVersion: '1.4.0',
        sessionSampleRate: 1, disableAutoPageView: true
      },
      credentials: valid.credentials
    });
  });

  it.each([
    ['empty config and credentials', { enabled: true, config: {}, credentials: {} }],
    ['missing credentials', { enabled: true, config: valid.config }],
    ['empty region', { ...valid, config: { ...valid.config, region: '' } }],
    ['non-string token', { ...valid, credentials: { ...valid.credentials, sessionToken: 42 } }],
    ['unparseable expiration', { ...valid, credentials: { ...valid.credentials, expiration: 'soon' } }],
    ['already expired credentials', { ...valid, credentials: { ...valid.credentials, expiration: '2020-01-01T00:00:00Z' } }],
    ['disabled', { ...valid, enabled: false }],
    ['enabled as a string', { ...valid, enabled: 'true' }],
    ['an array body', [valid]],
    ['null body', null]
  ])('returns null for %s', async (_label, body) => {
    answer(body);
    await expect(load()).resolves.toBeNull();
  });

  it.each([
    ['invalid JSON', () => answer('<html>')],
    ['an error status', () => answer(valid, 503)],
    ['a network failure', () => vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('offline')))]
  ])('rejects on %s', async (_label, arrange) => {
    arrange();
    await expect(load()).rejects.toThrow();
  });

  it('carries the typed optional settings through', async () => {
    const settings = {
      telemetries: ['errors', 'performance', ['http', { recordAllRequests: true }]],
      sessionAttributes: { tenant: 'emea', beta: true, tier: 2 },
      applicationAttributes: { team: 'desk' },
      allowCookies: true,
      sessionEventLimit: 500,
      pageIdFormat: 'PATH_AND_HASH',
      endpoint: 'https://dataplane.rum.eu-west-1.amazonaws.com',
      headers: { 'x-tenant': 'emea' },
      cookieAttributes: { secure: true, sameSite: 'Strict' },
      compressionStrategy: { enabled: true }
    };
    answer({ ...valid, config: { ...valid.config, ...settings } });
    expect((await load())?.config).toEqual({
      ...valid.config,
      ...settings,
      disableAutoPageView: true
    });
  });

  it('drops wrongly typed and unknown settings, and keeps automatic page views off', async () => {
    answer({
      ...valid,
      config: {
        ...valid.config,
        disableAutoPageView: false,
        allowCookies: 'yes',
        sessionEventLimit: '500',
        pageIdFormat: 'FULL_URL',
        sessionAttributes: { nested: { a: 1 } },
        telemetries: [42],
        identityPoolId: 'eu-west-1:pool'
      }
    });
    expect((await load())?.config).toEqual({ ...valid.config, disableAutoPageView: true });
  });

  it.each([
    ['a number entry', [42]],
    ['a tuple without a name', [[42]]],
    ['a tuple with a non-object option', [['http', 'all']]],
    ['an empty tuple', [[]]],
    ['a tuple with extra entries', [['http', {}, 'extra']]]
  ])('drops malformed telemetries: %s', async (_label, telemetries) => {
    answer({ ...valid, config: { ...valid.config, telemetries } });
    expect((await load())?.config).not.toHaveProperty('telemetries');
  });

  it('drops an out-of-range sample rate instead of passing it on', async () => {
    answer({ ...valid, config: { ...valid.config, sessionSampleRate: 5 } });
    expect((await load())?.config.sessionSampleRate).toBeUndefined();
  });
});
