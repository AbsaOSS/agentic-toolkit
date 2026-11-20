import { renderLayout } from './layout';

export function renderHome(root: HTMLElement): void {
  const content = renderLayout(root, 'Welcome');
  content.innerHTML = '<p>Use the menu to manage your account.</p>';
}
