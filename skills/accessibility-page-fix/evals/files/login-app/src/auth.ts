import { getConfig } from './config';

const KEY = 'portal.session';

interface Session {
  token: string;
  username: string;
  expiresAt: number;
}

export class SignInError extends Error {
  constructor(readonly status: number) {
    super(status === 401 ? 'Wrong username or password.' : `Sign-in failed (${status}). Try again later.`);
  }
}

export async function signIn(username: string, password: string): Promise<void> {
  const response = await fetch(`${getConfig().apiUrl}/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  });
  if (!response.ok) throw new SignInError(response.status);
  const body = (await response.json()) as { token: string; expiresIn: number };
  const session: Session = { token: body.token, username, expiresAt: Date.now() + body.expiresIn * 1000 };
  sessionStorage.setItem(KEY, JSON.stringify(session));
}

export function currentSession(): Session | null {
  const raw = sessionStorage.getItem(KEY);
  if (!raw) return null;
  const session = JSON.parse(raw) as Session;
  return session.expiresAt > Date.now() ? session : null;
}

export function secondsLeft(): number {
  const session = currentSession();
  return session ? Math.round((session.expiresAt - Date.now()) / 1000) : 0;
}

export function signOut(): void {
  sessionStorage.removeItem(KEY);
}
