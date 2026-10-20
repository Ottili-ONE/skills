// Shared helpers for the Ottili truth kit. Zero dependencies (Node >= 20).
import { spawnSync } from 'node:child_process';
import crypto from 'node:crypto';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';

export const KIT_DIR = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
export const KIT_VERSION = (() => {
  try {
    return fs.readFileSync(path.join(KIT_DIR, 'KIT_VERSION'), 'utf8').trim();
  } catch {
    return 'unknown';
  }
})();

export const EXIT = Object.freeze({ OK: 0, FAIL: 1, USAGE: 2, NOTHING: 3, OUTSIDE: 4, CONFLICT: 5, BLOCKED: 20 });

export function run(cmd, args = [], opts = {}) {
  const r = spawnSync(cmd, args, { encoding: 'utf8', maxBuffer: 512 * 1024 * 1024, ...opts });
  return {
    code: r.status ?? (r.signal ? 128 : 1),
    stdout: r.stdout ?? '',
    stderr: r.stderr ?? '',
    signal: r.signal ?? null,
    error: r.error ?? null,
  };
}

export function git(root, args, opts = {}) {
  return run('git', ['-C', root, ...args], opts);
}

export function gitOut(root, args) {
  const r = git(root, args);
  if (r.code !== 0) throw new Error(`git ${args.join(' ')} failed (${r.code}): ${r.stderr.trim()}`);
  return r.stdout;
}

export function repoRoot(cwd = process.cwd()) {
  const r = run('git', ['-C', cwd, 'rev-parse', '--show-toplevel']);
  if (r.code !== 0) throw new Error(`not inside a git work tree: ${cwd}`);
  return r.stdout.trim();
}

export const DEFAULT_CONFIG = Object.freeze({
  repo: null,
  repoCode: null,
  kind: 'node-modular', // node-modular | node-monorepo | python
  trunkBranch: 'main',
  remote: 'origin',
  integration: 'push-trunk', // push-trunk | branch-only
  locales: ['de', 'en'],
  maxFileLines: 500,
  maxSqlLines: 800,
  maxTestLines: 800,
  install: null,
  commands: {},
  boot: null, // { command, readyPath, env, timeoutSeconds }
  rootAllowlist: [],
  sharedGlobs: [], // files every job may change (lockfiles, root package.json): implicitly owned, never part of the evidence hash
  sql: { requireRls: true, requireIdempotent: true, globalTableMarker: 'truth:global-table' },
  language: { allowGlobs: [] },
  stubs: { allowGlobs: [] },
  secrets: { allowGlobs: [] },
  size: { allowGlobs: [] },
  i18n: { catalogGlobs: ['**/i18n/*.json', '**/locales/*.json'], callPattern: "\\bt\\(\\s*['\"]([\\w.-]+)['\"]" },
  generatedGlobs: ['**/generated/**', '**/dist/**', '**/node_modules/**', '**/*.lock', '**/pnpm-lock.yaml', '**/package-lock.json'],
});

function deepMerge(a, b) {
  if (Array.isArray(a) || Array.isArray(b) || typeof a !== 'object' || typeof b !== 'object' || !a || !b) return b ?? a;
  const out = { ...a };
  for (const [k, v] of Object.entries(b)) out[k] = k in a ? deepMerge(a[k], v) : v;
  return out;
}

export function loadConfig(root) {
  const file = path.join(root, 'scripts', 'truth', 'config.json');
  const kitGlobs = ['scripts/truth/**', 'docs/truth/**'];
  let user = {};
  if (fs.existsSync(file)) {
    try {
      user = JSON.parse(fs.readFileSync(file, 'utf8'));
    } catch (err) {
      throw new Error(`scripts/truth/config.json is not valid JSON: ${err.message}`);
    }
  }
  const cfg = deepMerge(JSON.parse(JSON.stringify(DEFAULT_CONFIG)), user);
  for (const key of ['language', 'stubs', 'secrets', 'size']) cfg[key].allowGlobs = [...new Set([...kitGlobs, ...(cfg[key].allowGlobs ?? [])])];
  return cfg;
}

export function repoName(root, cfg) {
  if (cfg.repo) return cfg.repo;
  const r = git(root, ['remote', 'get-url', cfg.remote || 'origin']);
  if (r.code === 0 && r.stdout.trim()) return path.basename(r.stdout.trim()).replace(/\.git$/, '');
  return path.basename(root);
}

export function resultsRoot() {
  return process.env.TRUTH_RESULTS_DIR || path.join(os.homedir(), '.ottili-truth', 'results');
}

export function resultsDir(root, cfg) {
  const dir = path.join(resultsRoot(), repoName(root, cfg));
  fs.mkdirSync(dir, { recursive: true });
  return dir;
}

export function lockDir() {
  const dir = process.env.TRUTH_LOCK_DIR || path.join(os.tmpdir(), 'ottili-truth-locks');
  fs.mkdirSync(dir, { recursive: true, mode: 0o1777 });
  return dir;
}

export function writeJson(file, obj) {
  fs.mkdirSync(path.dirname(file), { recursive: true });
  const tmp = `${file}.${process.pid}.tmp`;
  fs.writeFileSync(tmp, `${JSON.stringify(obj, null, 2)}\n`);
  fs.renameSync(tmp, file);
}

export function readJson(file, fallback = null) {
  try {
    return JSON.parse(fs.readFileSync(file, 'utf8'));
  } catch {
    return fallback;
  }
}

export function sha256(data) {
  return crypto.createHash('sha256').update(data).digest('hex');
}

export function nowIso() {
  return new Date().toISOString();
}

export function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

export function parseArgs(argv, spec = {}) {
  // spec: { flags: ['ui','db'], multi: ['allow-shrink'] }
  const flags = new Set(spec.flags ?? []);
  const multi = new Set(spec.multi ?? []);
  const out = { _: [] };
  for (let i = 0; i < argv.length; i += 1) {
    const a = argv[i];
    if (a === '--') {
      out._.push(...argv.slice(i + 1));
      break;
    }
    if (a.startsWith('--')) {
      const eq = a.indexOf('=');
      const key = eq === -1 ? a.slice(2) : a.slice(2, eq);
      if (flags.has(key)) {
        out[key] = true;
        continue;
      }
      let value;
      if (eq !== -1) value = a.slice(eq + 1);
      else {
        value = argv[i + 1];
        i += 1;
      }
      if (value === undefined) throw new Error(`missing value for --${key}`);
      if (multi.has(key)) (out[key] ??= []).push(value);
      else out[key] = value;
    } else out._.push(a);
  }
  return out;
}

export function csv(value) {
  if (!value) return [];
  return String(value)
    .split(',')
    .map((s) => s.trim())
    .filter(Boolean);
}

// ---------- glob matching (posix paths relative to the repo root) ----------

function expandBraces(pattern) {
  const m = /\{([^{}]*)\}/.exec(pattern);
  if (!m) return [pattern];
  const out = [];
  for (const alt of m[1].split(',')) out.push(...expandBraces(pattern.slice(0, m.index) + alt + pattern.slice(m.index + m[0].length)));
  return out;
}

function globToRegExpSingle(glob) {
  let re = '';
  for (let i = 0; i < glob.length; i += 1) {
    const c = glob[i];
    if (c === '*') {
      if (glob[i + 1] === '*') {
        i += 1;
        if (glob[i + 1] === '/') {
          i += 1;
          re += '(?:.*/)?';
        } else re += '.*';
      } else re += '[^/]*';
    } else if (c === '?') re += '[^/]';
    else if ('\\^$+.()|[]{}'.includes(c)) re += `\\${c}`;
    else re += c;
  }
  return re;
}

export function globToRegExp(glob) {
  const g = glob.replace(/^\.\//, '').replace(/\/+$/, '');
  const alts = expandBraces(g).map((one) => {
    const hasMeta = /[*?]/.test(one);
    const body = globToRegExpSingle(one);
    // a plain path (no wildcard) also matches everything below it
    return hasMeta ? `^${body}$` : `^${body}(?:/.*)?$`;
  });
  return new RegExp(alts.join('|'));
}

export function makeMatcher(globs) {
  const list = (globs ?? []).filter(Boolean).map(globToRegExp);
  return (rel) => list.some((re) => re.test(rel));
}

// ---------- file listing ----------

export function listFiles(root, { tracked = true, untracked = true } = {}) {
  const files = new Set();
  if (tracked) for (const f of gitOut(root, ['ls-files', '-z']).split('\0')) if (f) files.add(f);
  if (untracked) for (const f of gitOut(root, ['ls-files', '-z', '--others', '--exclude-standard']).split('\0')) if (f) files.add(f);
  return [...files].filter((f) => fs.existsSync(path.join(root, f))).sort();
}

export function trunkRef(root, cfg) {
  const remote = `${cfg.remote}/${cfg.trunkBranch}`;
  if (git(root, ['rev-parse', '--verify', '--quiet', `refs/remotes/${remote}`]).code === 0) return remote;
  if (git(root, ['rev-parse', '--verify', '--quiet', `refs/heads/${cfg.trunkBranch}`]).code === 0) return cfg.trunkBranch;
  return 'HEAD';
}

export function mergeBase(root, cfg) {
  const ref = trunkRef(root, cfg);
  const r = git(root, ['merge-base', 'HEAD', ref]);
  return r.code === 0 ? r.stdout.trim() : null;
}

/** Files changed relative to the merge base (committed + working tree + untracked). Returns [{status, path}] */
export function changedFiles(root, cfg) {
  const base = mergeBase(root, cfg);
  const out = new Map();
  if (base) {
    const diff = gitOut(root, ['diff', '--name-status', '-z', '--no-renames', base]).split('\0');
    for (let i = 0; i + 1 < diff.length; i += 2) if (diff[i]) out.set(diff[i + 1], diff[i][0]);
  } else {
    const diff = gitOut(root, ['diff', '--name-status', '-z', '--no-renames', 'HEAD']).split('\0');
    for (let i = 0; i + 1 < diff.length; i += 2) if (diff[i]) out.set(diff[i + 1], diff[i][0]);
  }
  for (const f of gitOut(root, ['ls-files', '-z', '--others', '--exclude-standard']).split('\0')) if (f) out.set(f, 'A');
  return [...out.entries()].map(([p, status]) => ({ status, path: p })).sort((a, b) => a.path.localeCompare(b.path));
}

export function ownedTreeHash(root, ownedGlobs) {
  // Content hash of every tracked file at HEAD that matches the owned globs (evidence binding for the gate result).
  const match = makeMatcher(ownedGlobs);
  const listing = gitOut(root, ['ls-tree', '-r', '-z', 'HEAD']).split('\0').filter(Boolean);
  const lines = [];
  for (const entry of listing) {
    const tab = entry.indexOf('\t');
    const meta = entry.slice(0, tab).split(' ');
    const file = entry.slice(tab + 1);
    if (match(file)) lines.push(`${meta[2]} ${file}`);
  }
  return sha256(lines.sort().join('\n'));
}

/** Hash of the working-tree content of every file (tracked or untracked) that matches the owned globs: binds gate evidence to content. */
export function ownedContentHash(root, ownedGlobs, excludeGlobs = []) {
  const match = makeMatcher(ownedGlobs);
  const excluded = makeMatcher(excludeGlobs);
  const lines = [];
  for (const rel of listFiles(root)) {
    if (!match(rel) || (excludeGlobs.length > 0 && excluded(rel))) continue;
    let st;
    try {
      st = fs.statSync(path.join(root, rel));
    } catch {
      continue;
    }
    if (!st.isFile()) continue;
    lines.push(`${sha256(fs.readFileSync(path.join(root, rel)))} ${rel}`);
  }
  return sha256(lines.sort().join('\n'));
}

export function requireFromRepo(root, name) {
  const candidates = [path.join(root, 'package.json'), path.join(KIT_DIR, 'package.json')];
  if (process.env.TRUTH_NODE_MODULES_DIR) candidates.push(path.join(process.env.TRUTH_NODE_MODULES_DIR, 'noop.js'));
  for (const c of candidates) {
    try {
      return createRequire(c)(name);
    } catch {
      // try next
    }
  }
  return null;
}

export function formatDuration(ms) {
  if (ms < 1000) return `${ms}ms`;
  const s = Math.round(ms / 100) / 10;
  return s < 120 ? `${s}s` : `${Math.round(s / 6) / 10}min`;
}

export function tail(text, lines = 40) {
  const arr = String(text).split('\n');
  return arr.slice(-lines).join('\n');
}

export function log(...a) {
  process.stderr.write(`${a.join(' ')}\n`);
}
