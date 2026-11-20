import { navigate } from './router';

/** A failed request. Pages decide what to show; 401 and 403 go to the app's shared error page. */
export class ApiError extends Error {
  constructor(readonly status: number, readonly url: string) {
    super(`Request to ${url} failed (${status})`);
  }
}

async function request<T>(method: string, url: string, body?: unknown): Promise<T> {
  const response = await fetch(url, {
    method,
    headers: body === undefined ? {} : { 'Content-Type': 'application/json' },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  if (response.status === 401 || response.status === 403) {
    navigate('/error');
    throw new ApiError(response.status, url);
  }
  if (!response.ok) throw new ApiError(response.status, url);
  return (await response.json()) as T;
}

export interface Project {
  id: number;
  name: string;
  owner: string;
  status: 'active' | 'paused' | 'archived';
  updated: string;
}

export interface Report {
  id: number;
  name: string;
  type: string;
  rows: number;
  created: string;
}

export interface Activity {
  id: number;
  text: string;
  when: string;
}

// Reads come from static JSON in public/api (a stand-in backend). Writes have no backend in development.
export const api = {
  projects: () => request<Project[]>('GET', '/api/projects.json'),
  versions: () => request<Record<string, string[]>>('GET', '/api/versions.json'),
  projectNamesLike: (name: string) => request<{ matches: number }>('GET', `/api/project-names.json?q=${encodeURIComponent(name)}`),
  renameProject: (id: number, name: string) => request<Project>('PUT', `/api/projects/${id}`, { name }),
  deleteProject: (id: number) => request<void>('DELETE', `/api/projects/${id}`),
  reports: () => request<Report[]>('GET', '/api/reports.json'),
  exportReports: (format: string) => request<{ url: string }>('POST', '/api/reports/export', { format }),
  activity: () => request<Activity[]>('GET', '/api/activity.json'),
};
