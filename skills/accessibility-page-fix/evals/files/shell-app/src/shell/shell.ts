import './shell.css';
import { createMenuButton, showToast } from '../ui-kit';

const NAV = [
  ['/home', 'Home'],
  ['/projects', 'Projects'],
  ['/reports', 'Reports'],
  ['/pricing', 'Pricing'],
  ['/support/new', 'Support'],
] as const;

/** Renders the app shell once and returns the element pages render into. */
export function renderShell(root: HTMLElement): HTMLElement {
  root.innerHTML = `
    <div class="shell__topbar">
      <img class="shell__logo" src="/logo.svg" />
      <span class="shell__name">Workbench</span>
      <span class="shell__breadcrumb"></span>
      <span class="shell__version">v3.2.1</span>
      <span class="shell__user">Dana Whitfield</span>
    </div>
    <div class="shell__sidebar">
      <div class="shell__nav">${NAV.map(([path, label]) => `<a href="${path}">${label}</a>`).join('')}</div>
    </div>
    <div class="shell__content"></div>`;
  root.querySelector('.shell__user')!.append(
    createMenuButton({
      tooltip: 'Account',
      items: [
        { label: 'Profile', onSelect: () => showToast('Profile is not available in this demo') },
        { label: 'Sign out', onSelect: () => showToast('Signed out') },
      ],
    })
  );
  return root.querySelector('.shell__content')!;
}

/** Marks the current page in the navigation and the breadcrumb. */
export function setCurrentPage(path: string, title: string): void {
  document.querySelectorAll<HTMLAnchorElement>('.shell__nav a').forEach(link => link.classList.toggle('active', link.pathname === path));
  document.querySelector('.shell__breadcrumb')!.textContent = `/ ${title}`;
}
