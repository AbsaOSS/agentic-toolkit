import { getSettings, saveSettings, type Settings } from '../api';
import { renderLayout } from './layout';

export async function renderSettings(root: HTMLElement): Promise<void> {
  const content = renderLayout(root, 'Account settings');
  content.innerHTML = '<div class="loading">Loading…</div>';
  let settings: Settings;
  try {
    settings = await getSettings();
  } catch {
    content.innerHTML = '<div class="load-error">Could not load your settings.</div>';
    return;
  }
  content.innerHTML = `
    <form class="settings">
      <label for="displayName">Display name</label>
      <input id="displayName" name="displayName" />
      <label>Email</label>
      <input name="email" type="email" />
      <label for="language">Language</label>
      <select id="language" name="language">
        <option value="en">English</option><option value="de">Deutsch</option><option value="fr">Français</option>
      </select>
      <div class="group-title">Notifications</div>
      <label class="toggle"><input type="checkbox" name="emailNotifications" /><span class="toggle__box"></span>Email</label>
      <label class="toggle"><input type="checkbox" name="smsNotifications" /><span class="toggle__box"></span>SMS</label>
      <button type="submit" class="save">Save</button>
      <div class="saved" hidden>Settings saved</div>
    </form>`;
  const form = content.querySelector<HTMLFormElement>('form')!;
  (form.elements.namedItem('displayName') as HTMLInputElement).value = settings.displayName;
  (form.elements.namedItem('email') as HTMLInputElement).value = settings.email;
  (form.elements.namedItem('language') as HTMLSelectElement).value = settings.language;
  (form.elements.namedItem('emailNotifications') as HTMLInputElement).checked = settings.emailNotifications;
  (form.elements.namedItem('smsNotifications') as HTMLInputElement).checked = settings.smsNotifications;
  const saved = form.querySelector<HTMLElement>('.saved')!;
  form.addEventListener('submit', async event => {
    event.preventDefault();
    const data = new FormData(form);
    try {
      await saveSettings({
        displayName: String(data.get('displayName')),
        email: String(data.get('email')),
        language: data.get('language') as Settings['language'],
        emailNotifications: data.has('emailNotifications'),
        smsNotifications: data.has('smsNotifications'),
      });
      saved.textContent = 'Settings saved';
    } catch {
      saved.textContent = 'Saving failed. Try again.';
    }
    saved.hidden = false;
  });
}
