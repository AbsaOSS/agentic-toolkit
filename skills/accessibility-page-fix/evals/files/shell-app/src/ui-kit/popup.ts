/** Places a popup under its anchor. Popups are attached to the end of <body>, outside the page's layout. */
export function placeBelow(popup: HTMLElement, anchor: HTMLElement): void {
  const box = anchor.getBoundingClientRect();
  popup.style.top = `${box.bottom + scrollY + 4}px`;
  popup.style.left = `${Math.max(8, box.right + scrollX - popup.offsetWidth)}px`;
}

/** Closes the popup on the next click outside it. */
export function closeOnOutsideClick(popup: HTMLElement, anchor: HTMLElement, close: () => void): void {
  const listener = (event: MouseEvent) => {
    if (!popup.contains(event.target as Node) && !anchor.contains(event.target as Node)) {
      document.removeEventListener('mousedown', listener);
      close();
    }
  };
  setTimeout(() => document.addEventListener('mousedown', listener));
}
