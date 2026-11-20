/** The current root font size in px (16 unless the user or the browser changed it). */
export function rootFontSize(): number {
  return parseFloat(getComputedStyle(document.documentElement).fontSize);
}

/** Calls `callback` with the new root font size whenever it changes. Returns a function that stops listening. */
export function onRootFontSizeChange(callback: (px: number) => void): () => void {
  const probe = document.createElement('div');
  probe.style.cssText = 'position:absolute;visibility:hidden;width:1rem;height:0;';
  document.body.append(probe);
  const observer = new ResizeObserver(() => callback(rootFontSize()));
  observer.observe(probe);
  return () => {
    observer.disconnect();
    probe.remove();
  };
}
