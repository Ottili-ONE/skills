#!/usr/bin/env node
// root-allowlist.test.mjs -- SKL-W0-01 TASK-0006
//
// scripts/truth/config.json is the single source of truth for what may live at
// the repository root. Every tracked path whose parent is the root must be a
// directory or a file listed in rootAllowlist. Anything else -- a scratch
// directory, a debug probe script, a stray artefact -- is rejected.
//
// Run against the real repository (expect clean) and against a fixture
// repository seeded with a scratch directory and a debug script at the root
// (expect failures).

import { test } from 'node:test';
import assert from 'node:assert/strict';
import { REPO, makeRepo, cleanup, loadConfig, trackedFiles } from './_fixture.mjs';

function violations(repo) {
  // A tracked path is a violation when its top-level component -- the first
  // path segment, or the file name when there is no segment -- is not in the
  // root allowlist. Directories are not tracked as such, so a scratch
  // directory is caught through the files it contains.
  const cfg = loadConfig(repo);
  const allow = new Set(cfg.rootAllowlist);
  const bad = [];
  for (const rel of trackedFiles(repo)) {
    const top = rel.split('/')[0];
    if (!allow.has(top)) bad.push(top);
  }
  return [...new Set(bad)];
}

test('every tracked root entry is in the root allowlist', () => {
  const bad = violations(REPO);
  assert.deepEqual(bad, []);
});

test('FAILS on a fixture with a scratch directory at the root', () => {
  const repo = makeRepo([
    { path: 'scratch/probe.mjs', content: 'throw new Error("not real")\n' },
  ]);
  try {
    const bad = violations(repo);
    assert.ok(bad.includes('scratch'),
      'expected the scratch/ directory to be rejected');
  } finally { cleanup(repo); }
});

test('FAILS on a fixture with a debug script at the root', () => {
  const repo = makeRepo([
    { path: '_dbg-r308.mjs', content: 'console.log("probe")\n' },
  ]);
  try {
    const bad = violations(repo);
    assert.ok(bad.includes('_dbg-r308.mjs'),
      'expected the debug script to be rejected');
  } finally { cleanup(repo); }
});
