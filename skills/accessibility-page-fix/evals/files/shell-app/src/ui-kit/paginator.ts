/** A paginator that stays at the bottom of its scroll container (position: sticky). */
export function createPaginator(options: { page: number; pages: number; total: number; pageSize: number; onChange: (page: number) => void }): HTMLElement {
  const bar = document.createElement('div');
  bar.className = 'uk-paginator';
  const add = (label: string, page: number, current = false) => {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'uk-paginator__page' + (current ? ' uk-paginator__page--current' : '');
    button.textContent = label;
    button.disabled = page < 1 || page > options.pages;
    button.addEventListener('click', () => options.onChange(page));
    bar.append(button);
  };
  add('Previous', options.page - 1);
  for (let page = 1; page <= options.pages; page++) add(String(page), page, page === options.page);
  add('Next', options.page + 1);
  const info = document.createElement('span');
  info.className = 'uk-paginator__info';
  const first = options.total ? (options.page - 1) * options.pageSize + 1 : 0;
  info.textContent = `Showing ${first}–${Math.min(options.page * options.pageSize, options.total)} of ${options.total} projects`;
  bar.append(info);
  return bar;
}
