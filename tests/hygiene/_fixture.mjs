#!/usr/bin/env node
// _fixture.mjs -- shared helpers for the SKL-W0-01 hygiene invariants.
//
// Every invariant checker is exercised twice: once against the real repository
// (must pass) and once against a deliberately broken fixture created in a
// throwaway git repository (must fail). This file owns the fixture plumbing.

import { spawnSync } from 'node:child_process';
import { mkdtempSync, mkdirSync, writeFileSync, symlinkSync, rmSync,
         existsSync, readFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

export const here = fileURLToPath(import.meta.url);
export const REPO = resolve(dirname(here), '..', '..');

// -- git helpers (read-only on the real repo; fixtures live under tmpdir()) ----

export function git(repo, ...args) {
  const r = spawnSync('git', ['-C', repo, ...args], { encoding: 'utf-8' });
  if (r.error) throw r.error;
  return { rc: r.status, stdout: r.stdout, stderr: r.stderr };
}

export function trackedFiles(repo) {
  const r = git(repo, 'ls-files', '-z');
  return r.stdout.split('\0').filter(Boolean);
}

// -- fixture repository -------------------------------------------------------

// Creates a throwaway git repository, writes `files`, commits, and returns the
// path. `files` entries: {path, content?, link?, size?}.
//   link  -> created as a symbolic link with the given target text
//   size  -> a zero-filled blob of that many bytes (overrides content)
export function makeRepo(files) {
  const repo = mkdtempSync(join(tmpdir(), 'hyg-'));
  git(repo, 'init', '-q');
  git(repo, 'config', 'user.email', 'hygiene@example.com');
  git(repo, 'config', 'user.name', 'Hygiene');
  git(repo, 'config', 'commit.gpgsign', 'false');
  for (const f of files) {
    const p = join(repo, f.path);
    mkdirSync(resolve(p, '..'), { recursive: true });
    if (f.link) {
      symlinkSync(f.link, p);
    } else if (typeof f.size === 'number') {
      writeFileSync(p, Buffer.alloc(f.size));
    } else {
      writeFileSync(p, f.content ?? '');
    }
  }
  git(repo, 'add', '-A');
  const c = git(repo, 'commit', '-q', '-m', 'fixture');
  if (c.rc !== 0) throw new Error('fixture commit failed: ' + c.stderr);
  return repo;
}

export function cleanup(repo) {
  rmSync(repo, { recursive: true, force: true });
}

// -- config.json fallback -----------------------------------------------------

// scripts/truth/config.json is operator-owned and is absent from this
// repository (see docs/gaps/SKL-W0-01.md). When the canonical file is present
// at runtime we read it; otherwise we fall back to the manifest below, which
// is the single source of truth for what may live at the repository root.
export const FALLBACK_CONFIG = {
  rootAllowlist: [
    '.github', '.gitignore', '.npmrc',
    'AGENTS.md', 'CONTRIBUTING.md', 'LICENSE', 'README.md', 'catalog.json',
    'docs', 'index', 'schema', 'scripts', 'skills', 'templates', 'tests',
  ],
  largeFileAllowlist: [],
};

export function loadConfig(repo) {
  const p = join(repo, 'scripts/truth/config.json');
  if (existsSync(p)) {
    return JSON.parse(readFileSync(p, 'utf-8'));
  }
  return FALLBACK_CONFIG;
}
