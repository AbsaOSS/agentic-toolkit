#!/usr/bin/env node
// doctor.mjs — static-analyze a Web Fragments host/fragment project for the common
// v0.8.x wiring mistakes, without deploying or reading library source.
//
// Usage:  node doctor.mjs [projectDir]   (defaults to cwd)
// Exit code: 0 = no errors, 1 = at least one ERROR-level finding.
//
// Heuristic, not a compiler. It greps source files and reports likely problems with a
// fix for each. False positives are possible — treat findings as leads, not verdicts.

import { readdirSync, readFileSync, statSync } from 'node:fs';
import { join, relative, extname } from 'node:path';

const root = process.argv[2] || process.cwd();
const SKIP_DIRS = new Set(['node_modules', '.git', 'dist', 'build', '.next', '.astro', 'out', 'coverage']);
const TEXT_EXT = new Set(['.ts', '.tsx', '.js', '.jsx', '.mjs', '.cjs', '.html', '.vue', '.svelte', '.astro', '.json', '.jsonc']);

const findings = []; // { level: 'error'|'warn'|'info', msg, fix, file? }
const add = (level, msg, fix, file) => findings.push({ level, msg, fix, file });

/** Collect candidate source files. */
function walk(dir, acc = []) {
  let entries;
  try { entries = readdirSync(dir, { withFileTypes: true }); } catch { return acc; }
  for (const e of entries) {
    if (e.name.startsWith('.') && e.name !== '.') continue;
    const full = join(dir, e.name);
    if (e.isDirectory()) {
      if (!SKIP_DIRS.has(e.name)) walk(full, acc);
    } else if (TEXT_EXT.has(extname(e.name))) {
      acc.push(full);
    }
  }
  return acc;
}

const files = walk(root);
const sources = files.map((f) => {
  try { return { f, text: readFileSync(f, 'utf8') }; } catch { return { f, text: '' }; }
});
const rel = (f) => relative(root, f) || f;
const any = (re) => sources.filter((s) => re.test(s.text));

// --- 1. Wrong middleware import (stale doc) ---
for (const s of any(/from\s+['"]web-fragments\/middleware['"]/)) {
  add('error',
    `Imports from the non-existent 'web-fragments/middleware' entry point.`,
    `Use 'web-fragments/gateway' (getWebMiddleware) or 'web-fragments/gateway/node' (getNodeMiddleware).`,
    rel(s.f));
}

// --- 2. register vs registerFragment ---
for (const s of sources) {
  // a gateway-ish variable calling .register( but not .registerFragment(
  if (/\.register\s*\(/.test(s.text) && !/\.registerFragment\s*\(/.test(s.text) && /FragmentGateway|web-fragments\/gateway/.test(s.text)) {
    add('error',
      `Calls .register(...) on what looks like a FragmentGateway.`,
      `The method is registerFragment(config), not register.`,
      rel(s.f));
  }
}

// --- 3. Detect project role ---
const usesGateway = any(/web-fragments\/gateway/).length > 0;
const usesElements = any(/from\s+['"]web-fragments['"]/).length > 0 || any(/<web-fragment[\s>]/).length > 0;
const isHost = usesGateway || usesElements;

// --- 4. Host: initializeWebFragments present if elements used ---
if (any(/<web-fragment[\s>]/).length > 0 && any(/initializeWebFragments\s*\(/).length === 0) {
  add('error',
    `Uses <web-fragment> but never calls initializeWebFragments().`,
    `Import { initializeWebFragments } from 'web-fragments' and call it once, early in the host client bootstrap.`);
}

// --- 5. Host: middleware installed if gateway registered ---
if (any(/registerFragment\s*\(/).length > 0 &&
    any(/getWebMiddleware|getNodeMiddleware/).length === 0) {
  add('error',
    `Registers fragments but never installs gateway middleware.`,
    `Add getWebMiddleware(gateway) (Web runtimes) or getNodeMiddleware(gateway) (Express/Connect) to the host server.`);
}

// --- 6. Required FragmentConfig fields present near registerFragment ---
for (const s of any(/registerFragment\s*\(/)) {
  const blockHasId = /fragmentId\s*:/.test(s.text);
  const blockHasEndpoint = /endpoint\s*:/.test(s.text) || /upstream\s*:/.test(s.text);
  const blockHasRoutes = /routePatterns\s*:/.test(s.text);
  if (!blockHasId) add('error', `registerFragment without a fragmentId.`, `fragmentId is required and must match the <web-fragment fragment-id>.`, rel(s.f));
  if (!blockHasEndpoint) add('error', `registerFragment without an endpoint.`, `endpoint (URL string or fetch fn) is required.`, rel(s.f));
  if (!blockHasRoutes) add('error', `registerFragment without routePatterns.`, `routePatterns (path-to-regexp v6) is required: asset prefix + host route(s).`, rel(s.f));
}

// --- 7. Deprecated fields ---
const deprecated = [
  [/\bupstream\s*:/, 'upstream', 'endpoint'],
  [/\bprePiercingClassNames\s*:/, 'prePiercingClassNames', 'piercingClassNames'],
  [/\bprePiercingStyles\s*:/, 'prePiercingStyles', 'piercingStyles'],
];
for (const [re, oldName, newName] of deprecated) {
  for (const s of any(re)) add('warn', `Uses deprecated '${oldName}'.`, `Rename to '${newName}'.`, rel(s.f));
}

// --- 8. Asset path vs routePattern coherence ---
const assetDirRe = /assetsDir\s*:\s*['"]([^'"]+)['"]/;
const assetDirs = [];
for (const s of sources) { const m = s.text.match(assetDirRe); if (m) assetDirs.push(m[1].replace(/^\/+|\/+$/g, '')); }
const routePatternPrefixes = [];
for (const s of sources) {
  for (const m of s.text.matchAll(/['"](\/__wf\/[^'":*]+)/g)) routePatternPrefixes.push(m[1].replace(/^\/+|\/+$/g, ''));
}
if (assetDirs.length && routePatternPrefixes.length) {
  for (const a of assetDirs) {
    const norm = a.replace(/^__wf\//, '__wf/');
    const matched = routePatternPrefixes.some((p) => p.includes(norm) || norm.includes(p.replace(/^__wf\//, '__wf/')));
    if (!matched) add('warn',
      `Vite assetsDir '${a}' does not appear to match any '/__wf/...' routePattern prefix.`,
      `Align the fragment build asset dir with the gateway asset routePattern, or assets will 404.`);
  }
}

// --- 9. Suspicious __wf routePattern without an asset-dir anywhere (host-only project: fine) ---
// (info only; host projects legitimately have no assetsDir)

// --- 10. X-Frame-Options: DENY blocks the gateway's hidden iframe ---
for (const s of any(/x-frame-options['"\s:=,()]+\s*['"]?\s*deny/i)) {
  add('error',
    `Sets X-Frame-Options: DENY — blocks the hidden iframe the gateway uses as the JS context (fragment silently fails).`,
    `Use SAMEORIGIN / remove it on fragment endpoints; allow framing via 'frame-ancestors self <gateway-origin>'. See references/csp-and-iframe.md.`,
    rel(s.f));
}

// --- 11. Unscoped static serving registered BEFORE the fragment middleware ---
// Only flag catch-all static (`.use(express.static(...))` with no path prefix); a path-scoped
// `.use('/assets', express.static(...))` doesn't shadow fragment routes.
for (const s of sources) {
  const mw = s.text.search(/get(Node|Web)Middleware\s*\(/);
  const stat = s.text.search(/\.use\(\s*(express\.static|serveStatic)\s*\(/);
  if (mw !== -1 && stat !== -1 && stat < mw) {
    add('warn',
      `Unscoped static serving appears before the fragment middleware in this file.`,
      `Register get(Node|Web)Middleware BEFORE catch-all static serving, or static answers fragment requests first.`,
      rel(s.f));
  }
}

// --- Report ---
const order = { error: 0, warn: 1, info: 2 };
findings.sort((a, b) => order[a.level] - order[b.level]);
const icon = { error: '✖ ERROR', warn: '▲ WARN ', info: 'ℹ INFO ' };

console.log(`\nWeb Fragments doctor — scanned ${sources.length} files under ${root}`);
console.log(`Project role: ${isHost ? (usesGateway && usesElements ? 'host (elements + gateway)' : usesGateway ? 'host server / gateway' : 'host client') : 'no web-fragments usage detected (fragment app or unrelated)'}\n`);

if (findings.length === 0) {
  console.log('✓ No issues found by the heuristics. Still verify in a browser (wf:<id> context + asset 200s).');
} else {
  for (const f of findings) {
    console.log(`${icon[f.level]}  ${f.msg}${f.file ? `  [${f.file}]` : ''}`);
    console.log(`         ↳ ${f.fix}\n`);
  }
}

const errors = findings.filter((f) => f.level === 'error').length;
const warns = findings.filter((f) => f.level === 'warn').length;
console.log(`Summary: ${errors} error(s), ${warns} warning(s).`);
process.exit(errors > 0 ? 1 : 0);
