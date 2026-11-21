export interface Page {
  title: string;
  render: (content: HTMLElement) => void | Promise<void>;
}

let pages: Record<string, Page> = {};
let onShow: (path: string, page: Page) => Promise<void> = async () => {};

export function startRouter(table: Record<string, Page>, show: (path: string, page: Page) => Promise<void>): void {
  pages = table;
  onShow = show;
  // Same-origin links are handled by the router instead of reloading the page
  document.addEventListener('click', event => {
    const link = (event.target as HTMLElement).closest('a');
    if (!link || link.origin !== location.origin || event.metaKey || event.ctrlKey) return;
    event.preventDefault();
    navigate(link.pathname + link.search);
  });
  addEventListener('popstate', () => void render());
  void render();
}

export function navigate(url: string): void {
  history.pushState(null, '', url);
  void render();
}

async function render(): Promise<void> {
  const path = location.pathname;
  const page = pages[path] ?? pages['/home'];
  if (!pages[path]) history.replaceState(null, '', '/home');
  await onShow(pages[path] ? path : '/home', page);
}
