type Render = (root: HTMLElement) => void | Promise<void>;

const routes = new Map<string, { render: Render; signedIn: boolean }>();
let root: HTMLElement;
let isSignedIn: () => boolean = () => false;

export function defineRoutes(appRoot: HTMLElement, signedIn: () => boolean, table: Record<string, { render: Render; signedIn: boolean }>): void {
  root = appRoot;
  isSignedIn = signedIn;
  for (const [path, route] of Object.entries(table)) routes.set(path, route);
  addEventListener('popstate', () => void show(location.pathname));
}

export function navigate(path: string): void {
  history.pushState(null, '', path);
  void show(path);
}

export async function show(path: string): Promise<void> {
  let route = routes.get(path);
  if (!route) {
    history.replaceState(null, '', '/home');
    route = routes.get('/home')!;
  }
  if (route.signedIn && !isSignedIn()) {
    history.replaceState(null, '', '/login');
    route = routes.get('/login')!;
  }
  await route.render(root);
}
