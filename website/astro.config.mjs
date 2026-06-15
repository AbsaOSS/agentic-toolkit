import starlight from '@astrojs/starlight';
import { defineConfig } from 'astro/config';
import { site, base, repoUrl } from './site.config.mjs';

export default defineConfig({
  site,
  base,
  legacy: { collections: true },
  integrations: [
    starlight({
      title: 'Agentic Toolkit',
      description:
        'Skills, guidelines, and best practices for AI-assisted engineering',
      customCss: ['./src/styles/custom.css'],
      head: [
        {
          tag: 'link',
          attrs: { rel: 'preconnect', href: 'https://fonts.googleapis.com' },
        },
        {
          tag: 'link',
          attrs: {
            rel: 'preconnect',
            href: 'https://fonts.gstatic.com',
            crossorigin: true,
          },
        },
        {
          tag: 'link',
          attrs: {
            rel: 'stylesheet',
            href: 'https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,400;12..96,600;12..96,800&family=DM+Sans:ital,opsz,wght@0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700;1,9..40,400&family=JetBrains+Mono:wght@400;500;600&display=swap',
          },
        },
      ],
      social: [
        {
          icon: 'github',
          label: 'GitHub',
          href: repoUrl,
        },
      ],
      sidebar: [
        {
          label: 'Guidelines',
          autogenerate: { directory: 'guidelines' },
        },
        {
          label: 'Skills',
          autogenerate: { directory: 'skills' },
        },
      ],
      editLink: {
        baseUrl:
          'https://github.com/AbsaOSS/agentic-toolkit/edit/master/',
      },
    }),
  ],
});
