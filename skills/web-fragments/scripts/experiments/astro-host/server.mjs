import express from 'express';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { FragmentGateway } from 'web-fragments/gateway';
import { getNodeMiddleware } from 'web-fragments/gateway/node';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ASTRO_DIST = path.resolve(__dirname, '../astro-fragment/dist');
const FRAGMENT_PORT = 5400;
const HOST_PORT = 5402;

// --- Fragment endpoint: static Astro build, mounted at /astro (matches Astro `base`) ---
const fragApp = express();
fragApp.use('/astro', express.static(ASTRO_DIST, { extensions: ['html'] }));
fragApp.listen(FRAGMENT_PORT, () => console.log(`fragment (astro) on http://localhost:${FRAGMENT_PORT}/astro/`));

// --- Host shell + fragment gateway ---
const gateway = new FragmentGateway();
gateway.registerFragment({
  fragmentId: 'astro',
  endpoint: `http://localhost:${FRAGMENT_PORT}`,
  piercing: false,
  routePatterns: ['/astro/:_*'],
});

const SHELL = `<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <title>Astro-in-fragment host</title>
    <style>
      body { font-family: Georgia, serif; padding: 1rem; }
      web-fragment { display:block; border:2px dashed #6c2bd9; padding:.5rem; margin-top:1rem; }
    </style>
    <script type="importmap">
      { "imports": { "web-fragments": "/_wf/elements.js" } }
    </script>
  </head>
  <body>
    <h1 id="host-h1">HOST shell (plain HTML)</h1>
    <p>The box below is an Astro site embedded as a web fragment.</p>
    <web-fragment fragment-id="astro" src="/astro/"></web-fragment>
    <script type="module">
      import { initializeWebFragments } from 'web-fragments';
      initializeWebFragments();
    </script>
  </body>
</html>`;

const app = express();
app.use('/_wf', express.static(path.join(__dirname, 'node_modules/web-fragments/dist')));
app.use(getNodeMiddleware(gateway, { mode: 'development' }));
app.get('/', (_req, res) => res.type('html').send(SHELL));
app.listen(HOST_PORT, () => console.log(`host on http://localhost:${HOST_PORT}/`));
