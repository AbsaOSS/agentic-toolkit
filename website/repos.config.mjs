/**
 * Multi-repo content sources.
 *
 * Each entry defines a repository whose docs/ and skills/ directories
 * are merged into the website at build time.
 *
 * - `local`  — relative path from website/ to the repo root (used when the
 *              directory exists on disk; skips cloning for local dev and CI)
 * - `url`    — git remote used when `local` path is not found
 * - `ref`    — branch or tag to clone
 * - `paths`  — folder mapping inside the repo
 */
export default {
  repos: [
    {
      name: 'agentic-toolkit',
      url: 'https://github.com/AbsaOSS/agentic-toolkit',
      ref: 'master',
      local: '..',
      paths: {
        docs: 'docs',
        skills: 'skills',
        extraDocs: ['CONTRIBUTING.md'],
      },
    },
    // Add more repos with the same folder structure:
    // {
    //   name: 'another-repo',
    //   url: 'https://github.com/AbsaOSS/another-repo',
    //   ref: 'main',
    //   paths: { docs: 'docs', skills: 'skills' },
    // },
  ],
};
