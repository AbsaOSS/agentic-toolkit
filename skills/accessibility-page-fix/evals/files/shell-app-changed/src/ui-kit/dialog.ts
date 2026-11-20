export interface DialogRef {
  element: HTMLElement;
  close: () => void;
}

/**
 * Opens a dialog at the end of <body>. `width` and `height` are CSS lengths, for example '760px'.
 * `onClose` runs when the dialog closes for any reason.
 */
export function openDialog(options: { title: string; width: string; height?: string; body: HTMLElement; actions?: HTMLElement[]; onClose?: () => void }): DialogRef {
  const overlay = document.createElement('div');
  overlay.className = 'uk-overlay';
  const dialog = document.createElement('div');
  dialog.className = 'uk-dialog';
  dialog.style.width = options.width;
  if (options.height) {
    dialog.style.height = options.height;
    dialog.style.overflow = 'hidden';
  }
  const header = document.createElement('div');
  header.className = 'uk-dialog__header';
  header.innerHTML = '<div class="uk-dialog__title"></div><span class="uk-dialog__close">×</span>';
  header.querySelector('.uk-dialog__title')!.textContent = options.title;
  const body = document.createElement('div');
  body.className = 'uk-dialog__body';
  body.append(options.body);
  dialog.append(header, body);
  if (options.actions?.length) {
    const actions = document.createElement('div');
    actions.className = 'uk-dialog__actions';
    actions.append(...options.actions);
    dialog.append(actions);
  }
  overlay.append(dialog);
  document.body.append(overlay);
  const close = () => {
    overlay.remove();
    options.onClose?.();
  };
  header.querySelector('.uk-dialog__close')!.addEventListener('click', close);
  return { element: dialog, close };
}
