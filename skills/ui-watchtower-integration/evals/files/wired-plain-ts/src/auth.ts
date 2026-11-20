/** The signed-in account, as the identity SDK reports it. */
export interface Account {
  /** Opaque, stable account id (a UUID). */
  localAccountId: string;
  /** The user's email address. */
  username: string;
  name: string;
}

type Listener = (account: Account | undefined) => void;

const listeners = new Set<Listener>();
let current: Account | undefined;

/** Calls `listener` now with the current account, and again on every sign-in and sign-out. */
export function onAccountChange(listener: Listener): () => void {
  listeners.add(listener);
  listener(current);
  return () => listeners.delete(listener);
}

export function signIn(account: Account): void {
  current = account;
  listeners.forEach((listener) => listener(current));
}

export function signOut(): void {
  current = undefined;
  listeners.forEach((listener) => listener(current));
}
