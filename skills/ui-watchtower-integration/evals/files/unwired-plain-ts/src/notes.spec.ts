import { createNote, renderNotes } from './notes';

describe('notes', () => {
  afterEach(() => vi.unstubAllGlobals());

  it('renders one list item per note', () => {
    const list = document.createElement('ul');
    renderNotes(list, [
      { id: '1', title: 'Site visit' },
      { id: '2', title: 'Follow-up' }
    ]);
    expect([...list.children].map((li) => li.textContent)).toEqual(['Site visit', 'Follow-up']);
  });

  it('creates a note, and reports a failed save with its status', async () => {
    vi.stubGlobal('fetch', async () => new Response(JSON.stringify({ id: '3', title: 'Call back' })));
    await expect(createNote('Call back')).resolves.toEqual({ id: '3', title: 'Call back' });

    vi.stubGlobal('fetch', async () => new Response('', { status: 503 }));
    await expect(createNote('Call back')).rejects.toMatchObject({ name: 'ApiError', status: 503 });
  });
});
