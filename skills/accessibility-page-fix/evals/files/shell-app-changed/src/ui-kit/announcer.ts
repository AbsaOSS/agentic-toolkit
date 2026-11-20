let region: HTMLElement | undefined;

/**
 * Announces a message to screen readers without moving focus. The live region exists before the first message, so
 * screen readers pick up every change.
 */
export function announce(message: string, politeness: 'polite' | 'assertive' = 'polite'): void {
  region ??= createRegion();
  region.setAttribute('aria-live', politeness);
  region.textContent = '';
  setTimeout(() => (region!.textContent = message), 50);
}

function createRegion(): HTMLElement {
  const element = document.createElement('div');
  element.className = 'uk-visually-hidden';
  element.setAttribute('aria-live', 'polite');
  document.body.append(element);
  return element;
}

// Create the region at start-up, before anything is announced.
if (typeof document !== 'undefined') region = createRegion();
