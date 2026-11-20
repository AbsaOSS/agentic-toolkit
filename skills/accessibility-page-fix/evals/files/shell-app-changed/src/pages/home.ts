import { api } from '../api';
import { createMenuButton, showToast } from '../ui-kit';

export async function renderHome(content: HTMLElement): Promise<void> {
  content.innerHTML = `
    <div class="page">
      <div class="page__title">Home</div>
      <div class="summary"></div>
      <div class="page__title">Recent activity</div>
      <div class="activity"><div class="loading">Loading…</div></div>
    </div>`;
  const summary = content.querySelector('.summary')!;
  for (const [value, label] of [['58', 'Projects'], ['8', 'Reports'], ['5', 'Team members']]) {
    const card = document.createElement('div');
    card.className = 'summary__card';
    card.innerHTML = `<div><div class="summary__value">${value}</div><div class="summary__label">${label}</div></div>`;
    card.append(createMenuButton({ tooltip: 'More actions', items: [{ label: `Open ${label.toLowerCase()}`, onSelect: () => showToast(`Opening ${label.toLowerCase()}`) }] }));
    summary.append(card);
  }
  const list = content.querySelector('.activity')!;
  try {
    const items = await api.activity();
    list.innerHTML = items.map(item => `<div class="activity__item"><span>${item.text}</span><span class="activity__when">${item.when}</span></div>`).join('');
  } catch {
    list.innerHTML = '<div class="load-error">Could not load activity.</div>';
  }
}
