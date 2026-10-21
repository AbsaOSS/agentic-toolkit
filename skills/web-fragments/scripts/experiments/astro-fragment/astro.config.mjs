import { defineConfig } from 'astro/config';

// Namespace everything (pages + assets) under /astro so the fragment gateway can route
// all fragment requests with a single pattern: /astro/:_*
export default defineConfig({
  base: '/astro',
  trailingSlash: 'always',
  build: {
    // default assets dir is _astro; under base it becomes /astro/_astro/...
    format: 'directory',
  },
});
