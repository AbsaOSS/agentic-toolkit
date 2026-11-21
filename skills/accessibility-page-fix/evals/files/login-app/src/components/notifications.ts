let container: HTMLElement | undefined;

/** Shows a notification at the bottom right. It announces itself (role="alert") and closes after `duration` ms. */
export function notify(message: string, type: 'error' | 'success' = 'error', duration = 4000): void {
  if (!container) {
    container = document.createElement('div');
    container.className = 'notifications';
    document.body.append(container);
  }
  const item = document.createElement('div');
  item.className = `notification notification--${type}`;
  item.setAttribute('role', 'alert');
  item.textContent = message;
  container.append(item);
  setTimeout(() => item.remove(), duration);
}
