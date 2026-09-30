#!/usr/bin/env node
// scaffold-fragment.mjs — generate a minimal Vite fragment app skeleton + the matching
// gateway registration snippet for the host. Mirrors the party-button-fragment layout.
//
// Usage:
//   node scaffold-fragment.mjs <fragment-id> [targetDir] [--org <slug>]
//
// Example:
//   node scaffold-fragment.mjs party-button ./party-button --org acme.shop
//
// Creates: index.html, src/main.ts, vite.config.ts, package.json, tsconfig.json
// Prints:  the FragmentGateway.registerFragment(...) snippet to paste into the host,
//          with the asset routePattern already aligned to the fragment's assetsDir.

import { mkdirSync, writeFileSync, existsSync } from 'node:fs';
import { join } from 'node:path';

const args = process.argv.slice(2);
const positional = args.filter((a) => !a.startsWith('--'));
const orgIdx = args.indexOf('--org');
const org = orgIdx !== -1 ? args[orgIdx + 1] : 'dev.web-fragments.demos';

const fragmentId = positional[0];
if (!fragmentId || !/^[a-z0-9][a-z0-9-]*$/.test(fragmentId)) {
  console.error('Usage: node scaffold-fragment.mjs <fragment-id> [targetDir] [--org <slug>]');
  console.error('  <fragment-id> must be lowercase kebab-case, e.g. party-button');
  process.exit(1);
}
const targetDir = positional[1] || `./${fragmentId}`;
const assetsDir = `__wf/${org}.${fragmentId}/`;
const assetRoutePattern = `/${assetsDir}:_*`;

if (existsSync(targetDir)) {
  console.error(`Refusing to overwrite existing directory: ${targetDir}`);
  process.exit(1);
}

const files = {
  'index.html': `<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>${fragmentId} fragment</title>
  </head>
  <body>
    <div id="app">${fragmentId} fragment</div>
    <script type="module" src="/src/main.ts"></script>
  </body>
</html>
`,
  'src/main.ts': `// The fragment's client code. A fragment is a normal standalone app — it does NOT
// import 'web-fragments'. The host embeds it through a web-fragment element whose
// fragment-id is "${fragmentId}".
const app = document.getElementById('app');
if (app) {
  app.addEventListener('click', () => {
    app.textContent = 'Hello from the ${fragmentId} fragment! ' + new Date().toLocaleTimeString();
  });
}
`,
  'vite.config.ts': `import { defineConfig } from 'vite';

// The ONE rule that matters for a fragment: emit assets under a unique path so the host
// gateway can proxy them on its own origin without colliding with other fragments.
// This must stay in sync with the asset routePattern registered in the host gateway.
export default defineConfig({
  build: {
    assetsDir: '${assetsDir}',
  },
});
`,
  'package.json': JSON.stringify({
    name: `${fragmentId}-fragment`,
    private: true,
    type: 'module',
    license: 'MIT',
    scripts: {
      dev: 'vite',
      build: 'tsc && vite build',
      preview: 'vite build && vite preview',
    },
    devDependencies: {
      typescript: '~5.7.2',
      vite: '^6.2.0',
    },
  }, null, 2) + '\n',
  'tsconfig.json': JSON.stringify({
    compilerOptions: {
      target: 'ES2022',
      module: 'ESNext',
      moduleResolution: 'bundler',
      strict: true,
      skipLibCheck: true,
      noEmit: true,
    },
    include: ['src'],
  }, null, 2) + '\n',
};

for (const [relPath, content] of Object.entries(files)) {
  const full = join(targetDir, relPath);
  mkdirSync(join(full, '..'), { recursive: true });
  writeFileSync(full, content);
}

console.log(`✓ Scaffolded fragment '${fragmentId}' at ${targetDir}`);
console.log(`  Run:  cd ${targetDir} && npm install && npm run dev   (serves on http://localhost:5173)\n`);
console.log('Paste this into the HOST app gateway (asset pattern is already aligned):\n');
console.log(`  import { FragmentGateway } from 'web-fragments/gateway';

  export const gateway = new FragmentGateway();
  gateway.registerFragment({
    fragmentId: '${fragmentId}',
    endpoint: process.env.${fragmentId.toUpperCase().replace(/-/g, '_')}_ENDPOINT ?? 'http://localhost:5173',
    routePatterns: [
      '${assetRoutePattern}', // fragment assets (matches vite assetsDir)
      '/',                    // TODO: host route(s) where <web-fragment fragment-id="${fragmentId}"> is placed
    ],
  });
`);
console.log('And in the host markup:');
console.log(`  <web-fragment fragment-id="${fragmentId}"></web-fragment>\n`);
