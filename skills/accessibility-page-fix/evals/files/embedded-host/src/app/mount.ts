import { ORDERS, type Order } from './orders-data';
import { FOCUS_CSS, FRAGMENT_CSS } from './styles';

interface MountOptions {
  /** Path prefix of the page the fragment runs in ('' standalone, '/host' in the partner portal). */
  basePath: string;
}

/** Renders the curation fragment into `root`: a plain element standalone, an open shadow root inside the host. */
export function mountCuration(root: HTMLElement | ShadowRoot, options: MountOptions): void {
  const style = document.createElement('style');
  style.textContent = FRAGMENT_CSS;
  root.append(style);
  const focusStyle = document.createElement('style');
  focusStyle.textContent = FOCUS_CSS;
  document.head.append(focusStyle);

  const app = document.createElement('main');
  app.className = 'curation';
  root.append(app);
  let filter: Order['status'] | 'all' = 'all';
  const render = () => {
    const rows = ORDERS.filter(order => filter === 'all' || order.status === filter);
    app.innerHTML = `
      <div class="curation__title">Orders to curate <a class="help-link" href="${options.basePath}/help">Help</a></div>
      <div class="filters">
        ${['all', 'new', 'review', 'approved', 'rejected']
          .map(value => `<span class="chip${value === filter ? ' chip--active' : ''}" data-filter="${value}">${value}</span>`)
          .join('')}
      </div>
      <table class="orders">
        <tr><td class="head">Order</td><td class="head">Customer</td><td class="head">Items</td><td class="head">Status</td><td class="head"></td></tr>
        ${rows
          .map(
            order => `
          <tr class="order-row">
            <td><a class="order-link" href="/curation/orders/${order.id}">#${order.id}</a></td>
            <td>${order.customer}</td>
            <td>${order.items}</td>
            <td><span class="status status--${order.status}">${order.status}</span></td>
            <td><span class="toggle-note" data-id="${order.id}">Show note</span><div class="note" hidden>${order.note}</div></td>
          </tr>`
          )
          .join('')}
      </table>`;
    app.querySelectorAll<HTMLElement>('[data-filter]').forEach(chip =>
      chip.addEventListener('click', () => {
        filter = chip.dataset.filter as typeof filter;
        render();
      })
    );
    app.querySelectorAll<HTMLElement>('.toggle-note').forEach(toggle =>
      toggle.addEventListener('click', () => {
        const note = toggle.nextElementSibling as HTMLElement;
        note.hidden = !note.hidden;
        toggle.textContent = note.hidden ? 'Show note' : 'Hide note';
      })
    );
  };
  render();
}
