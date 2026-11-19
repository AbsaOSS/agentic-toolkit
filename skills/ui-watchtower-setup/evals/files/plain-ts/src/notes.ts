export interface Note {
  id: string;
  title: string;
}

/** A failed API call; `status` is the HTTP status. */
export class ApiError extends Error {
  override name = 'ApiError';
  constructor(
    readonly status: number,
    request: string
  ) {
    super(`${request} failed with ${status}`);
  }
}

export async function loadNotes(): Promise<Note[]> {
  const response = await fetch('/api/notes');
  if (!response.ok) {
    throw new ApiError(response.status, 'GET /api/notes');
  }
  return (await response.json()) as Note[];
}

export async function createNote(title: string): Promise<Note> {
  const response = await fetch('/api/notes', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title })
  });
  if (!response.ok) {
    throw new ApiError(response.status, 'POST /api/notes');
  }
  return (await response.json()) as Note;
}

export function renderNotes(target: HTMLElement, notes: Note[]): void {
  target.replaceChildren(
    ...notes.map((note) => {
      const item = document.createElement('li');
      item.textContent = note.title;
      return item;
    })
  );
}
