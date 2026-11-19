import { loadCatalogue, renderCatalogue } from './catalogue';

describe('catalogue', () => {
  afterEach(() => vi.unstubAllGlobals());

  it('lists the products from the API', async () => {
    vi.stubGlobal('fetch', async () => new Response(JSON.stringify([{ sku: 'A1', title: 'Desk lamp' }])));
    const list = document.createElement('ul');
    renderCatalogue(list, await loadCatalogue());
    expect(list.textContent).toBe('Desk lamp');
  });
});
