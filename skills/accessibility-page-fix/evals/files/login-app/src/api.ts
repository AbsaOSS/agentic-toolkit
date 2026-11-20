import { currentSession } from './auth';
import { getConfig } from './config';

export class ApiError extends Error {
  constructor(readonly status: number) {
    super(`Request failed (${status})`);
  }
}

async function request<T>(method: string, path: string, body?: unknown): Promise<T> {
  const response = await fetch(`${getConfig().apiUrl}${path}`, {
    method,
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${currentSession()?.token ?? ''}` },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  if (response.status === 401) {
    location.assign('/login');
    throw new ApiError(401);
  }
  if (!response.ok) throw new ApiError(response.status);
  return (await response.json()) as T;
}

export interface Settings {
  displayName: string;
  email: string;
  language: 'en' | 'de' | 'fr';
  emailNotifications: boolean;
  smsNotifications: boolean;
}

export const getSettings = () => request<Settings>('GET', '/settings');
export const saveSettings = (settings: Settings) => request<Settings>('PUT', '/settings', settings);
