#!/usr/bin/env node
// no-bad-symlinks.test.mjs -- SKL-W0-01 TASK-0006
//
// A tracked symlink must never be:
//   (a) absolute  -- it would escape the checkout and pin a host path
//   (b) a self-loop -- the symlink points at its own path
//   (c) dangling  -- the target does not exist
//
// Run against the real repository (expect clean) and against a fixture
// repository containing one bad symlink of each kind (expect failures).

import { test } from 'node:test';
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { existsSync, lstatSync, readlinkSync } from 'node:fs';
import { resolve } from 'node:path';
import { REPO, makeRepo, cleanup } from './_fixture.mjs';

function badSymlinks(repo) {
  const bad = [];
  const r = spawnSync('git', ['-C', repo, 'ls-files', '-z'],
    { encoding: 'utf-8' });
  if (r.error) throw r.error;
  for (const rel of r.stdout.split('\0').filter(Boolean)) {
    const abs = resolve(repo, rel);
    let st;
    try { st = lstatSync(abs); } catch { continue; }
    if (!st.isSymbolicLink()) continue;
    const target = readlinkSync(abs);
    if (target.startsWith('/')) {
      bad.push({ rel, kind: 'absolute', target });
      continue;
    }
    if (resolve(abs, '..', target) === abs) {
      bad.push({ rel, kind: 'self-loop', target });
      continue;
    }
    if (!existsSync(resolve(abs, '..', target))) {
      bad.push({ rel, kind: 'dangling', target });
    }
  }
  return bad;
}

test('no tracked symlink with an absolute target', () => {
  const bad = badSymlinks(REPO).filter(b => b.kind === 'absolute');
  assert.deepEqual(bad, []);
});

test('no tracked symlink that is a self-loop', () => {
  const bad = badSymlinks(REPO).filter(b => b.kind === 'self-loop');
  assert.deepEqual(bad, []);
});

test('no tracked symlink with a dangling target', () => {
  const bad = badSymlinks(REPO).filter(b => b.kind === 'dangling');
  assert.deepEqual(bad, []);
});

// -- broken fixtures (must FAIL) ---------------------------------------------

test('FAILS on a fixture with an absolute symlink', () => {
  const repo = makeRepo([
    { path: 'abs-link', link: '/etc/hostname' },
    { path: 'real.txt', content: 'ok' },
  ]);
  try {
    const bad = badSymlinks(repo).filter(b => b.kind === 'absolute');
    assert.ok(bad.length > 0, 'expected the absolute symlink to be reported');
  } finally {
    cleanup(repo);
  }
});

test('FAILS on a fixture with a self-loop symlink', () => {
  const repo = makeRepo([
    { path: 'loop-link', link: 'loop-link' },
  ]);
  try {
    const bad = badSymlinks(repo).filter(b => b.kind === 'self-loop');
    assert.ok(bad.length > 0, 'expected the self-loop symlink to be reported');
  } finally {
    cleanup(repo);
  }
});

test('FAILS on a fixture with a dangling symlink', () => {
  const repo = makeRepo([
    { path: 'dead-link', link: 'does-not-exist' },
  ]);
  try {
    const bad = badSymlinks(repo).filter(b => b.kind === 'dangling');
    assert.ok(bad.length > 0, 'expected the dangling symlink to be reported');
  } finally {
    cleanup(repo);
  }
});
