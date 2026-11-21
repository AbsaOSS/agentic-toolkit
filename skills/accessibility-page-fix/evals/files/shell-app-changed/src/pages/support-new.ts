import Quill from 'quill';
import 'quill/dist/quill.snow.css';
import { showToast } from '../ui-kit';

export function renderSupportNew(content: HTMLElement): void {
  content.innerHTML = `
    <div class="page">
      <div class="page__title">New support request</div>
      <form class="support">
        <label class="support__label" for="subject">Subject</label>
        <input class="uk-input" id="subject" name="subject" />
        <div class="support__label">Message</div>
        <div class="support__editor"></div>
        <div><button class="uk-btn uk-btn--solid" type="submit">Send</button></div>
      </form>
    </div>`;
  const editor = new Quill(content.querySelector<HTMLElement>('.support__editor')!, {
    theme: 'snow',
    modules: {
      toolbar: [[{ header: [1, 2, false] }], ['bold', 'italic'], [{ list: 'ordered' }, { list: 'bullet' }], ['blockquote'], [{ color: [] }]],
    },
  });
  content.querySelector('form')!.addEventListener('submit', event => {
    event.preventDefault();
    if (!editor.getText().trim()) return showToast('Write a message first', { type: 'error' });
    showToast('Request sent', { type: 'success' });
  });
}
