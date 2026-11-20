import './ui-kit';
import './pages/pages.css';
import { renderError } from './pages/error';
import { renderHome } from './pages/home';
import { renderPricing } from './pages/pricing';
import { renderProjects } from './pages/projects';
import { renderReports } from './pages/reports';
import { renderSupportNew } from './pages/support-new';
import { startRouter } from './router';
import { renderShell, setCurrentPage } from './shell/shell';

const content = renderShell(document.getElementById('app')!);
startRouter(
  {
    '/home': { title: 'Home', render: renderHome },
    '/projects': { title: 'Projects', render: renderProjects },
    '/reports': { title: 'Reports', render: renderReports },
    '/pricing': { title: 'Pricing', render: renderPricing },
    '/support/new': { title: 'Support', render: renderSupportNew },
    '/error': { title: 'Error', render: renderError },
  },
  async (path, page) => {
    setCurrentPage(path, page.title);
    content.scrollTop = 0;
    await page.render(content);
  }
);
