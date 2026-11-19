import { onAccountChange } from './auth';
import { createNote, loadNotes, renderNotes, type Note } from './notes';

const app = document.getElementById('app')!;
app.innerHTML = `
  <h1>Field Notes</h1>
  <p id="who"></p>
  <form id="new-note">
    <input name="title" required placeholder="New note" />
    <button type="submit">Create note</button>
    <span id="form-status" role="status"></span>
  </form>
  <ul id="notes"></ul>`;

let notes: Note[] = [];
const list = app.querySelector<HTMLUListElement>('#notes')!;
const form = app.querySelector<HTMLFormElement>('#new-note')!;
const status = app.querySelector<HTMLSpanElement>('#form-status')!;

onAccountChange((account) => {
  app.querySelector('#who')!.textContent = account ? `Signed in as ${account.name}` : 'Not signed in';
});

loadNotes()
  .then((loaded) => {
    notes = loaded;
    renderNotes(list, notes);
  })
  .catch(() => {
    list.textContent = 'Could not load notes.';
  });

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  const title = String(new FormData(form).get('title') ?? '').trim();
  try {
    notes = [...notes, await createNote(title)];
    renderNotes(list, notes);
    form.reset();
    status.textContent = '';
  } catch {
    status.textContent = 'Could not save the note.';
  }
});
