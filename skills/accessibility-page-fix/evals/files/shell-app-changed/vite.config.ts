import { defineConfig } from 'vite';

// PORT lets a second copy of the app (for example the base branch) run next to this one.
export default defineConfig({
  server: { port: Number(process.env.PORT ?? 5173), strictPort: true },
  preview: { port: Number(process.env.PORT ?? 5173), strictPort: true },
});
