export type InputModality = 'keyboard' | 'mouse';

let modality: InputModality = 'mouse';
addEventListener('keydown', () => (modality = 'keyboard'), true);
addEventListener('mousedown', () => (modality = 'mouse'), true);

/** How the user last interacted: the keyboard or a pointer. */
export function inputModality(): InputModality {
  return modality;
}

/** Moves focus to `element`. A heading or container gets tabindex="-1" first so it can take focus. */
export function focusElement(element: HTMLElement, options: { preventScroll?: boolean } = {}): void {
  if (element.tabIndex < 0 && !element.hasAttribute('tabindex')) element.tabIndex = -1;
  element.focus({ preventScroll: options.preventScroll ?? false });
}
