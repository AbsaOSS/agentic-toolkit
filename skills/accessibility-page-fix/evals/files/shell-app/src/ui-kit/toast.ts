export type ToastType = 'info' | 'success' | 'error';

const MAX_TOASTS = 3;
let container: HTMLElement | undefined;

/**
 * Shows a toast at the bottom right. The container is a polite live region, so toasts announce themselves.
 * At most three are shown: a new toast removes the oldest one.
 */
export function showToast(message: string, options: { type?: ToastType; duration?: number } = {}): void {
  if (!container) {
    container = document.createElement('div');
    container.className = 'uk-toasts';
    container.setAttribute('role', 'status');
    document.body.append(container);
  }
  const toast = document.createElement('div');
  toast.className = `uk-toast uk-toast--${options.type ?? 'info'}`;
  toast.innerHTML = '<span class="uk-toast__text"></span><span class="uk-toast__close">✕</span>';
  toast.querySelector('.uk-toast__text')!.textContent = message;
  toast.querySelector('.uk-toast__close')!.addEventListener('click', () => toast.remove());
  container.append(toast);
  while (container.children.length > MAX_TOASTS) container.firstElementChild!.remove();
  setTimeout(() => toast.remove(), options.duration ?? 5000);
}
