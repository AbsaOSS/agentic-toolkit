import './styles.css';
import { currentSession, secondsLeft } from './auth';
import { openSessionDialog } from './components/session-dialog';
import { getConfig, loadConfig } from './config';
import { renderHome } from './pages/home';
import { renderLogin } from './pages/login';
import { renderSettings } from './pages/settings';
import { defineRoutes, show } from './router';

await loadConfig();
const root = document.getElementById('app')!;
defineRoutes(root, () => currentSession() !== null, {
  '/login': { render: renderLogin, signedIn: false },
  '/home': { render: renderHome, signedIn: true },
  '/account/settings': { render: renderSettings, signedIn: true },
});
await show(location.pathname);

// Ask for the password again shortly before the session ends, on whatever page the user is on.
setInterval(() => {
  if (location.pathname !== '/login' && currentSession() && secondsLeft() <= getConfig().sessionWarningSeconds) {
    openSessionDialog(() => {});
  }
}, 1000);
