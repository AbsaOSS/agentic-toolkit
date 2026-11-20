import { api, type Project } from '../api';
import { createDropdown, createMenuButton, createPaginator, openDialog, showToast } from '../ui-kit';

const PAGE_SIZE = 12;
const SORTS = [
  { value: 'name', label: 'Name' },
  { value: 'updated', label: 'Last updated' },
  { value: 'owner', label: 'Owner' },
];

export async function renderProjects(content: HTMLElement): Promise<void> {
  content.innerHTML = `
    <div class="page">
      <div class="page__title">Projects</div>
      <div class="toolbar">
        <input class="uk-input projects__search" placeholder="Search projects" />
        <span class="toolbar__sort"></span>
        <span class="toolbar__spacer"></span>
        <button class="uk-btn uk-btn--solid projects__new" type="button">New project</button>
      </div>
      <div class="projects__list"><div class="loading">Loading projects…</div></div>
    </div>
    <div class="projects__paginator"></div>`;
  const listElement = content.querySelector<HTMLElement>('.projects__list')!;
  const paginatorSlot = content.querySelector<HTMLElement>('.projects__paginator')!;
  const search = content.querySelector<HTMLInputElement>('.projects__search')!;
  content.querySelector('.projects__new')!.addEventListener('click', () => showToast('Creating projects is not available yet'));

  let projects: Project[];
  let versions: Record<string, string[]> | null = null;
  try {
    [projects, versions] = await Promise.all([api.projects(), api.versions().catch(() => null)]);
  } catch {
    listElement.innerHTML = '<div class="load-error">Could not load projects. Try again later.</div>';
    return;
  }

  let page = 1;
  let sort = 'name';
  content.querySelector('.toolbar__sort')!.append(createDropdown({ options: SORTS, value: sort, onChange: value => ((sort = value), (page = 1), render()) }));
  search.addEventListener('input', () => ((page = 1), render()));

  const render = () => {
    const query = search.value.trim().toLowerCase();
    const shown = projects
      .filter(project => project.name.toLowerCase().includes(query))
      .sort((a, b) => String(a[sort as keyof Project]).localeCompare(String(b[sort as keyof Project])));
    const pages = Math.max(1, Math.ceil(shown.length / PAGE_SIZE));
    page = Math.min(page, pages);
    listElement.innerHTML = '<div class="cards"></div>';
    const cards = listElement.querySelector('.cards')!;
    for (const project of shown.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE)) cards.append(renderCard(project));
    if (!shown.length) cards.innerHTML = '<div class="loading">No projects match your search.</div>';
    paginatorSlot.replaceChildren(createPaginator({ page, pages, total: shown.length, pageSize: PAGE_SIZE, onChange: next => ((page = next), render()) }));
  };

  const renderCard = (project: Project): HTMLElement => {
    const card = document.createElement('div');
    card.className = 'card';
    card.innerHTML = `
      <div class="card__head"><span class="card__name"></span></div>
      <div class="card__meta"></div>
      <div class="card__foot"><span class="uk-chip"></span></div>`;
    card.querySelector('.card__name')!.textContent = project.name;
    card.querySelector('.card__meta')!.textContent = `${project.owner} · updated ${project.updated}`;
    card.querySelector('.uk-chip')!.textContent = project.status;
    card.addEventListener('click', () => showToast(`Opening ${project.name}`));
    const projectVersions = versions?.[project.id] ?? ['N/A'];
    const dropdown = createDropdown({ options: projectVersions.map(v => ({ value: v, label: v })), value: projectVersions[0], onChange: v => showToast(`${project.name}: ${v} selected`) });
    card.querySelector('.card__foot')!.append(dropdown);
    card.querySelector('.card__head')!.append(
      createMenuButton({
        tooltip: 'More actions',
        items: [
          { label: 'Rename', onSelect: () => renameProject(project) },
          { label: 'Delete', onSelect: () => deleteProject(project) },
        ],
      })
    );
    return card;
  };

  const deleteProject = async (project: Project) => {
    try {
      await api.deleteProject(project.id);
      projects = projects.filter(p => p.id !== project.id);
      render();
    } catch {
      showToast(`Could not delete ${project.name}`, { type: 'error' });
    }
  };

  const renameProject = (project: Project) => {
    const body = document.createElement('div');
    body.className = 'rename';
    body.innerHTML = `
      <div class="rename__label">Name</div>
      <input class="uk-input rename__input" />
      <div class="field-error" hidden>Enter a name.</div>
      <div class="name-check"></div>`;
    const input = body.querySelector<HTMLInputElement>('.rename__input')!;
    const error = body.querySelector<HTMLElement>('.field-error')!;
    const check = body.querySelector<HTMLElement>('.name-check')!;
    input.value = project.name;
    let timer: ReturnType<typeof setTimeout> | undefined;
    input.addEventListener('input', () => {
      clearTimeout(timer);
      check.textContent = 'Checking…';
      timer = setTimeout(async () => {
        try {
          const { matches } = await api.projectNamesLike(input.value);
          check.innerHTML = `<span class="count">${matches}</span><span>projects have a similar name</span>`;
        } catch {
          check.textContent = '';
        }
      }, 600);
    });
    const cancel = document.createElement('button');
    cancel.type = 'button';
    cancel.textContent = 'Cancel';
    const save = document.createElement('button');
    save.type = 'button';
    save.textContent = 'Save';
    const dialog = openDialog({ title: 'Rename project', width: '480px', body, actions: [cancel, save] });
    cancel.addEventListener('click', dialog.close);
    save.addEventListener('click', async () => {
      if (!input.value.trim()) {
        error.hidden = false;
        return;
      }
      dialog.close();
      try {
        const renamed = await api.renameProject(project.id, input.value.trim());
        project.name = renamed.name;
        render();
        showToast('Project renamed', { type: 'success' });
      } catch {
        showToast(`Could not rename ${project.name}`, { type: 'error' });
      }
    });
  };

  render();
}
