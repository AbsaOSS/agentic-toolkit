import { resolve } from 'node:path';
import { defineConfig } from 'vite';

// PORT lets a second copy of the app (for example the base branch) run next to this one.
// Two entry pages: the real host (/host/…) and the fragment on its own (/curation/…).
export default defineConfig({
  server: { port: Number(process.env.PORT ?? 5173), strictPort: true },
  preview: { port: Number(process.env.PORT ?? 5173), strictPort: true },
  appType: 'mpa',
  plugins: [
    {
      name: 'route-to-entry',
      configureServer(server) {
        server.middlewares.use((req, _res, next) => {
          if (req.url?.startsWith('/host/')) req.url = '/host.html';
          else if (req.url?.startsWith('/curation/')) req.url = '/index.html';
          next();
        });
      },
    },
  ],
  build: { rollupOptions: { input: { index: resolve(import.meta.dirname, 'index.html'), host: resolve(import.meta.dirname, 'host.html') } } },
});
