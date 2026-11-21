import { closeOnOutsideClick, placeBelow } from './popup';

export interface DropdownOption {
  value: string;
  label: string;
}

/** A select-like control whose list opens at the end of <body>. */
export function createDropdown(options: { options: DropdownOption[]; value: string; onChange: (value: string) => void }): HTMLElement {
  const trigger = document.createElement('div');
  trigger.className = 'uk-dropdown';
  trigger.tabIndex = 0;
  let value = options.value;
  const render = () => (trigger.textContent = options.options.find(option => option.value === value)?.label ?? '');
  render();
  let list: HTMLElement | undefined;
  const close = () => {
    list?.remove();
    list = undefined;
  };
  const open = () => {
    if (list) return close();
    list = document.createElement('div');
    list.className = 'uk-dropdown__list';
    list.style.minWidth = `${trigger.offsetWidth}px`;
    for (const option of options.options) {
      const item = document.createElement('div');
      item.className = 'uk-dropdown__option' + (option.value === value ? ' uk-dropdown__option--selected' : '');
      item.textContent = option.label;
      item.addEventListener('click', () => {
        value = option.value;
        render();
        close();
        options.onChange(value);
      });
      list.append(item);
    }
    document.body.append(list);
    placeBelow(list, trigger);
    closeOnOutsideClick(list, trigger, close);
  };
  trigger.addEventListener('click', event => {
    event.stopPropagation();
    open();
  });
  trigger.addEventListener('keydown', event => {
    if (event.key === 'Enter') open();
  });
  return trigger;
}
