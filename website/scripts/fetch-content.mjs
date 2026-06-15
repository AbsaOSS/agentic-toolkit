#!/usr/bin/env node
/**
 * Fetches docs and skills from configured repositories and transforms them
 * into Starlight-compatible content pages.
 *
 * Usage:
 *   node scripts/fetch-content.mjs          # uses local path if available, else clones
 *   npm run fetch                            # same
 *   npm run build                            # fetch + astro build
 */
import { execSync } from 'node:child_process';
import {
  existsSync, mkdirSync, readFileSync, rmSync,
  writeFileSync, readdirSync, statSync,
} from 'node:fs';
import { join, dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { base } from '../site.config.mjs';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(__dirname, '..');
const CONTENT = join(ROOT, 'src', 'content', 'docs');
const CACHE = join(ROOT, '.repos-cache');

async function main() {
  const cfgPath = `file://${resolve(ROOT, 'repos.config.mjs').replace(/\\/g, '/')}`;
  const { default: config } = await import(cfgPath);
  const repos = [...config.repos, ...parseMergeRepos(process.env.MERGE_REPOS)];

  for (const dir of ['guidelines', 'skills']) {
    const p = join(CONTENT, dir);
    if (existsSync(p)) rmSync(p, { recursive: true, force: true });
    mkdirSync(p, { recursive: true });
  }

  const allSkills = [];
  const allDocs = [];

  for (const repo of repos) {
    console.log(`  ${repo.name}...`);
    const repoDir = resolveRepoDir(repo);

    collectDocs(repoDir, repo, allDocs);
    collectExtraDocs(repoDir, repo, allDocs);
    collectSkills(repoDir, repo, allSkills);
  }

  writeSkillsIndex(allSkills);
  writeGuidelinesIndex(allDocs);

  if (existsSync(CACHE)) rmSync(CACHE, { recursive: true, force: true });
  const uniqDocs = new Set(allDocs.map((d) => d.slug)).size;
  const uniqSkills = new Set(allSkills.map((s) => s.slug)).size;
  console.log(`✓ ${uniqDocs} guides, ${uniqSkills} skills from ${repos.length} repo(s)`);
}

/**
 * Extra repos injected at build time via the MERGE_REPOS env var.
 *
 * JSON form (full control — used by CI, which checks repos out itself so
 * private repos work without leaking tokens into clone URLs):
 *   MERGE_REPOS='[{"local":".external/extra","url":"https://github.com/org/repo"}]'
 *
 * Shorthand form (comma-separated, for quick local use):
 *   - local checkout path relative to website/  (e.g. "../some-checkout")
 *   - clone URL with optional ref               (e.g. "https://github.com/org/repo#main")
 *
 * Each repo is expected to follow the standard docs/ + skills/ layout.
 * Same-named skills or guides override earlier repos (last one wins).
 */
function parseMergeRepos(spec) {
  if (!spec) return [];
  const defaults = { paths: { docs: 'docs', skills: 'skills' } };

  if (spec.trim().startsWith('[')) {
    return JSON.parse(spec).map((r) => ({
      name:
        r.name ||
        (r.url || r.local).split(/[/\\]/).filter(Boolean).pop().replace(/\.git$/, ''),
      ref: r.ref || 'main',
      ...defaults,
      ...r,
      paths: { ...defaults.paths, ...(r.paths || {}) },
    }));
  }

  return spec
    .split(',')
    .map((s) => s.trim())
    .filter(Boolean)
    .map((item) => {
      if (item.includes('://')) {
        const [url, ref] = item.split('#');
        const name = url.split('/').filter(Boolean).pop().replace(/\.git$/, '');
        return { name, url, ref: ref || 'main', ...defaults };
      }
      return {
        name: item.split(/[/\\]/).filter(Boolean).pop(),
        local: item,
        ...defaults,
      };
    });
}

/** Warn when a later repo overwrites a page produced by an earlier one. */
function warnOnOverwrite(target, slug, repo) {
  if (existsSync(target)) {
    console.warn(`  ⚠ "${slug}" overwritten by ${repo.name}`);
  }
}

// ---------------------------------------------------------------------------
// Repo resolution
// ---------------------------------------------------------------------------

function resolveRepoDir(repo) {
  if (repo.local) {
    const localDir = resolve(ROOT, repo.local);
    const hasContent =
      existsSync(join(localDir, repo.paths.docs)) ||
      existsSync(join(localDir, repo.paths.skills));
    if (hasContent) return localDir;
    if (!repo.url) {
      throw new Error(
        `Repo "${repo.name}": local path "${repo.local}" has no ${repo.paths.docs}/ or ${repo.paths.skills}/ and no url to clone from`,
      );
    }
  }
  const dest = join(CACHE, repo.name);
  if (existsSync(dest)) rmSync(dest, { recursive: true, force: true });
  mkdirSync(CACHE, { recursive: true });
  execSync(
    `git clone --depth 1 --branch ${repo.ref} "${repo.url}" "${dest}"`,
    { stdio: 'pipe' },
  );
  return dest;
}

// ---------------------------------------------------------------------------
// Content collectors
// ---------------------------------------------------------------------------

function collectDocs(repoDir, repo, allDocs) {
  const docsDir = join(repoDir, repo.paths.docs);
  if (!existsSync(docsDir)) return;

  for (const file of readdirSync(docsDir)) {
    if (!file.endsWith('.md') || file === 'README.md') continue;
    const fp = join(docsDir, file);
    if (!statSync(fp).isFile()) continue;

    const parsed = parseMarkdown(readFileSync(fp, 'utf-8'), file);
    const slug = file.replace('.md', '');

    const target = join(CONTENT, 'guidelines', file);
    warnOnOverwrite(target, slug, repo);
    writeFileSync(
      target,
      toPage(parsed.title, parsed.body, {
        order: guideOrder(slug),
        description: parsed.frontmatter.description || firstParagraph(parsed.body),
      }),
    );
    allDocs.push({ title: parsed.title, slug });
  }
}

function collectExtraDocs(repoDir, repo, allDocs) {
  for (const rel of repo.paths.extraDocs || []) {
    const fp = join(repoDir, rel);
    if (!existsSync(fp)) continue;

    const fname = rel.split(/[/\\]/).pop();
    const parsed = parseMarkdown(readFileSync(fp, 'utf-8'), fname);
    const slug = fname.replace('.md', '').toLowerCase();

    const target = join(CONTENT, 'guidelines', `${slug}.md`);
    warnOnOverwrite(target, slug, repo);
    writeFileSync(
      target,
      toPage(parsed.title, parsed.body, {
        order: guideOrder(slug),
        description: parsed.frontmatter.description || firstParagraph(parsed.body),
      }),
    );
    allDocs.push({ title: parsed.title, slug });
  }
}

function collectSkills(repoDir, repo, allSkills) {
  const skillsDir = join(repoDir, repo.paths.skills);
  if (!existsSync(skillsDir)) return;

  for (const entry of readdirSync(skillsDir)) {
    const ep = join(skillsDir, entry);
    if (!statSync(ep).isDirectory()) continue;

    const sm = join(ep, 'SKILL.md');
    if (!existsSync(sm)) continue;

    const parsed = parseMarkdown(readFileSync(sm, 'utf-8'), `${entry}.md`);
    const desc = parsed.frontmatter.description || '';
    const bodyNoH1 = parsed.body.replace(/^#\s+.+\n*/m, '');

    let page = `---\ntitle: "${esc(parsed.title)}"\n`;
    if (desc) page += `description: "${esc(desc)}"\n`;
    page += `---\n\n`;
    if (desc) page += `:::note\n${desc}\n:::\n\n`;
    page += installSection(repo.url, entry);
    page += rewriteLinks(bodyNoH1);

    const target = join(CONTENT, 'skills', `${entry}.md`);
    warnOnOverwrite(target, entry, repo);
    writeFileSync(target, page);
    allSkills.push({ name: parsed.title, description: desc, slug: entry });
  }
}

// ---------------------------------------------------------------------------
// Markdown / YAML helpers
// ---------------------------------------------------------------------------

function parseMarkdown(raw, filename) {
  const content = raw.replace(/\r\n/g, '\n');

  if (!content.startsWith('---\n')) {
    const m = content.match(/^#\s+(.+)/m);
    return { frontmatter: {}, body: content, title: m ? m[1] : filename.replace('.md', '') };
  }

  const end = content.indexOf('\n---\n', 4);
  if (end === -1) {
    return { frontmatter: {}, body: content, title: filename.replace('.md', '') };
  }

  const fmStr = content.substring(4, end);
  const body = content.substring(end + 5);
  const frontmatter = parseSimpleYaml(fmStr);

  const m = body.match(/^#\s+(.+)/m);
  const title = frontmatter.title || (m ? m[1] : filename.replace('.md', ''));
  return { frontmatter, body, title };
}

function parseSimpleYaml(str) {
  const result = {};
  let key = null;
  let val = '';

  for (const line of str.split('\n')) {
    const m = line.match(/^([\w-]+):\s*>?\s*(.*)$/);
    if (m) {
      if (key) result[key] = val.trim();
      key = m[1];
      val = m[2];
    } else if (key && /^\s/.test(line)) {
      val += ' ' + line.trim();
    }
  }
  if (key) result[key] = val.trim();
  return result;
}

// ---------------------------------------------------------------------------
// Page generation
// ---------------------------------------------------------------------------

function toPage(title, body, opts = {}) {
  const noH1 = body.replace(/^#\s+.+\n*/m, '');
  let fm = `---\ntitle: "${esc(title)}"\n`;
  if (opts.description) fm += `description: "${esc(opts.description)}"\n`;
  if (opts.order != null) fm += `sidebar:\n  order: ${opts.order}\n`;
  fm += `---\n\n`;
  return fm + rewriteLinks(noH1);
}

/** First plain-text paragraph of a markdown body, for meta descriptions. */
function firstParagraph(body) {
  const noH1 = body.replace(/^#\s+.+\n*/m, '');
  for (const block of noH1.split(/\n\s*\n/)) {
    const t = block.trim();
    if (!t || /^[#>\-*`\d|!<[]/.test(t)) continue;
    return t
      .replace(/\s+/g, ' ')
      .replace(/\[([^\]]+)\]\([^)]*\)/g, '$1')
      .replace(/[*_`]/g, '')
      .substring(0, 300);
  }
  return '';
}

/** Per-skill install instructions injected into every skill page. */
function installSection(repoUrl, skill) {
  if (!repoUrl) return '';
  return [
    '## Install',
    '',
    '```bash',
    '# Global — available in every project',
    `npx skills add ${repoUrl} -g --skill ${skill}`,
    '',
    '# Project-scoped — current repository only',
    `npx skills add ${repoUrl} --skill ${skill}`,
    '```',
    '',
    `Verify with \`/skills list\` in your agent client. See [Getting Started](${base}/guidelines/getting-started/) for details.`,
    '',
    '',
  ].join('\n');
}

function guideOrder(slug) {
  const map = {
    'getting-started': 1,
    'contributing': 2,
    'skill-testing': 3,
    'token-saving': 4,
    'troubleshooting': 5,
  };
  return map[slug] ?? 10;
}

function rewriteLinks(s) {
  // Absolute links must carry the GitHub Pages base prefix, otherwise they
  // resolve to the domain root instead of /agentic-toolkit/.
  return s
    .replace(/\(\.\/docs\/([\w-]+)\.md\)/g, `(${base}/guidelines/$1/)`)
    .replace(/\(\.\.\/CONTRIBUTING\.md\)/gi, `(${base}/guidelines/contributing/)`)
    .replace(/\(\.\/([\w-]+)\.md\)/g, `(${base}/guidelines/$1/)`)
    .replace(/\(\.\.\/README\.md\)/g, `(${base}/)`);
}

// ---------------------------------------------------------------------------
// Index page generation (MDX with Starlight components)
// ---------------------------------------------------------------------------

// The index pages carry no per-item data — SkillsGrid/GuidesGrid components
// render the catalog straight from the content collection at build time,
// so descriptions live in exactly one place (the skill/guide pages).

function writeSkillsIndex() {
  writeFileSync(
    join(CONTENT, 'skills', 'index.mdx'),
    [
      '---',
      'title: Skills Catalog',
      'description: Browse available skills for AI-assisted engineering',
      'sidebar:',
      '  label: Overview',
      '  order: 0',
      '---',
      '',
      "import SkillsGrid from '../../../components/SkillsGrid.astro';",
      '',
      'Browse available skills. Each skill is a self-contained instruction set that AI agents load on demand, with per-skill install instructions on its page.',
      '',
      '<SkillsGrid />',
      '',
    ].join('\n'),
  );
}

function writeGuidelinesIndex() {
  writeFileSync(
    join(CONTENT, 'guidelines', 'index.mdx'),
    [
      '---',
      'title: Guidelines',
      'description: Guides and best practices for AI-assisted engineering',
      'sidebar:',
      '  label: Overview',
      '  order: 0',
      '---',
      '',
      "import GuidesGrid from '../../../components/GuidesGrid.astro';",
      '',
      'Guides covering skill authoring, testing, installation, and troubleshooting.',
      '',
      '<GuidesGrid />',
      '',
    ].join('\n'),
  );
}

// ---------------------------------------------------------------------------

function esc(s) {
  return s.replace(/"/g, '\\"').replace(/\n/g, ' ');
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
