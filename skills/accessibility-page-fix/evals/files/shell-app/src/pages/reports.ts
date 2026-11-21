import { api } from '../api';
import { createMenuButton, openDialog, showToast } from '../ui-kit';

export async function renderReports(content: HTMLElement): Promise<void> {
  const readonly = new URLSearchParams(location.search).get('view') === 'readonly';
  content.innerHTML = `
    <div class="page">
      <div class="page__title">Reports</div>
      <div class="reports__toolbar">
        <span class="uk-chip">Type: All</span>
        <span class="uk-chip">Last 30 days</span>
        <span class="toolbar__spacer"></span>
        <button class="uk-btn uk-btn--outline reports__add-filter" type="button">Add filter</button>
        ${readonly ? '' : '<button class="uk-btn uk-btn--outline reports__export" type="button">Export</button>'}
      </div>
      <div class="reports__list"><div class="loading">Loading reports…</div></div>
    </div>`;
  content.querySelector('.reports__add-filter')!.addEventListener('click', openFilterDialog);
  content.querySelector('.reports__export')?.addEventListener('click', openExportDialog);
  const list = content.querySelector('.reports__list')!;
  try {
    const reports = await api.reports();
    list.innerHTML = `
      <table class="reports__table">
        <thead><tr><th>Name</th><th>Type</th><th>Rows</th><th>Created</th><th></th></tr></thead>
        <tbody>${reports.map(report => `<tr data-id="${report.id}"><td>${report.name}</td><td>${report.type}</td><td>${report.rows}</td><td>${report.created}</td><td class="actions"></td></tr>`).join('')}</tbody>
      </table>`;
    for (const report of reports) {
      list.querySelector(`tr[data-id="${report.id}"] .actions`)!.append(
        createMenuButton({
          tooltip: 'More actions',
          items: [
            { label: 'Download', onSelect: () => showToast(`Downloading ${report.name}`) },
            { label: 'Duplicate', onSelect: () => showToast(`Duplicated ${report.name}`) },
          ],
        })
      );
    }
  } catch {
    list.innerHTML = '<div class="load-error">Could not load reports.</div>';
  }
}

function button(label: string): HTMLButtonElement {
  const element = document.createElement('button');
  element.type = 'button';
  element.textContent = label;
  return element;
}

function openExportDialog(): void {
  let step = 1;
  const body = document.createElement('div');
  const back = button('Back');
  const next = button('Next');
  const exportButton = button('Export');
  const render = () => {
    body.innerHTML = `
      <div class="uk-stepper">
        <div class="uk-stepper__step${step === 1 ? ' uk-stepper__step--current' : ''}"><span class="uk-stepper__number">1</span>Choose a format</div>
        <div class="uk-stepper__step${step === 2 ? ' uk-stepper__step--current' : ''}"><span class="uk-stepper__number">2</span>Template and options</div>
      </div>
      ${
        step === 1
          ? `<div class="formats">
              <label class="radio"><input type="radio" name="format" value="csv" checked /><span class="radio__dot"></span>CSV</label>
              <label class="radio"><input type="radio" name="format" value="xlsx" /><span class="radio__dot"></span>Excel (XLSX)</label>
            </div>`
          : `<div class="template">
              <div>Template (optional)</div>
              <input type="file" class="template__file" accept=".csv,.xlsx" />
              <div class="hint">Choose a CSV or XLSX file, up to 5 MB.</div>
            </div>`
      }`;
    back.hidden = step === 1;
    next.hidden = step === 2;
    exportButton.hidden = step === 1;
    body.querySelector('.template__file')?.addEventListener('click', () => showToast('Choose a CSV or XLSX file, up to 5 MB.'));
  };
  render();
  const dialog = openDialog({ title: 'Export reports', width: '760px', body, actions: [back, next, exportButton] });
  back.addEventListener('click', () => ((step = 1), render()));
  next.addEventListener('click', () => ((step = 2), render()));
  exportButton.addEventListener('click', async () => {
    try {
      await api.exportReports('csv');
      dialog.close();
      showToast('Export started', { type: 'success' });
    } catch {
      showToast('Export failed. Check the template and try again.', { type: 'error' });
    }
  });
}

function openFilterDialog(): void {
  const body = document.createElement('div');
  body.innerHTML = `
    <div class="filter-row">
      <select style="width: 300px"><option>Type</option><option>Rows</option><option>Created</option></select>
      <select style="width: 200px"><option>is</option><option>is not</option><option>greater than</option></select>
      <input style="width: 360px" placeholder="Value, for example Usage" />
    </div>`;
  const cancel = button('Cancel');
  const add = button('Add filter');
  const dialog = openDialog({ title: 'Add filter', width: '990px', height: '270px', body, actions: [cancel, add] });
  cancel.addEventListener('click', dialog.close);
  add.addEventListener('click', () => {
    dialog.close();
    showToast('Filter added', { type: 'success' });
  });
}
