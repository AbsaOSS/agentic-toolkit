import { closeOnOutsideClick, placeBelow } from './popup';

export interface MenuItem {
  label: string;
  onSelect: () => void;
}

const DOTS = '<svg viewBox="0 0 16 16"><circle cx="8" cy="3" r="1.5" fill="currentColor"/><circle cx="8" cy="8" r="1.5" fill="currentColor"/><circle cx="8" cy="13" r="1.5" fill="currentColor"/></svg>';

/** An icon button that opens a menu of actions. */
export function createMenuButton(options: { items: MenuItem[]; tooltip?: string }): HTMLButtonElement {
  const trigger = document.createElement('button');
  trigger.type = 'button';
  trigger.className = 'uk-menu-trigger';
  trigger.innerHTML = DOTS;
  if (options.tooltip) trigger.dataset.tooltip = options.tooltip;
  let menu: HTMLElement | undefined;
  const close = () => {
    menu?.remove();
    menu = undefined;
  };
  trigger.addEventListener('click', event => {
    event.stopPropagation();
    if (menu) return close();
    menu = document.createElement('div');
    menu.className = 'uk-menu';
    for (const item of options.items) {
      const entry = document.createElement('div');
      entry.className = 'uk-menu__item';
      entry.textContent = item.label;
      entry.addEventListener('click', () => {
        close();
        item.onSelect();
      });
      menu.append(entry);
    }
    document.body.append(menu);
    placeBelow(menu, trigger);
    closeOnOutsideClick(menu, trigger, close);
  });
  return trigger;
}
