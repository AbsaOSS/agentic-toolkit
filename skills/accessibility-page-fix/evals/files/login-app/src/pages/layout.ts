import { currentSession, signOut } from '../auth';
import { navigate } from '../router';

/** Header bar shared by the signed-in pages. */
export function renderLayout(root: HTMLElement, title: string): HTMLElement {
  root.innerHTML = `
    <div class="topbar">
      <img class="logo" src="/logo.svg" />
      <span class="topbar__link" data-to="/home">Home</span>
      <span class="topbar__link" data-to="/account/settings">Settings</span>
      <span class="topbar__user"></span>
      <span class="topbar__signout">Sign out</span>
    </div>
    <div class="page">
      <div class="page__title"></div>
      <div class="page__content"></div>
    </div>`;
  root.querySelector('.topbar__user')!.textContent = currentSession()?.username ?? '';
  root.querySelector('.page__title')!.textContent = title;
  root.querySelectorAll<HTMLElement>('[data-to]').forEach(link => link.addEventListener('click', () => navigate(link.dataset.to!)));
  root.querySelector('.topbar__signout')!.addEventListener('click', () => {
    signOut();
    navigate('/login');
  });
  return root.querySelector('.page__content')!;
}
