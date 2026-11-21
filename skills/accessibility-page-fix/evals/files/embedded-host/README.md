# curation-fragment

The "Curation" fragment of the partner portal (TypeScript + Vite, no framework). In production the portal (the
host) loads it into an **open shadow root** under `/host/…`. For local work it also runs on its own.

```bash
npm install
npm run dev          # http://localhost:5173 (PORT=5174 npm run dev for a second copy)
npm run test:e2e     # Playwright functional tests
npm run typecheck
npm run build
```

| URL | What it is |
|---|---|
| `/host/curation/orders` | The real host page: portal header, navigation and `main`, with the fragment inside `<curation-app>` (open shadow root) |
| `/curation/orders` | Standalone mode: the fragment alone. It imitates the host's URL and its `host-portal` body class, but not the host itself |

There are no accessibility tests yet.

## States

- all orders (default), each filter chip selected
- a note expanded ("Show note")
