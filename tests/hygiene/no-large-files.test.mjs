#!/usr/bin/env node
// no-large-files.test.mjs -- SKL-W0-01 TASK-0006
//
// No tracked file may exceed 5 MiB unless it is allow-listed in
// scripts/truth/config.json (largeFileAllowlist) with a reason. Large blobs
// in version control bloat clones and defeat the point of a source tree.
//
// Run against the real repository (expect clean) and against a fixture
// repository seeded with a 6 MiB blob (expect failure).

import { test } from 'node:test';
import assert from 'node:assert/strict';
import { statSync } from 'node:fs';
import { resolve } from 'node:path';
import { REPO, makeRepo, cleanup, loadConfig, trackedFiles } from './_fixture.mjs';

const MAX_BYTES = 5 * 1024 * 1024;

function largeFiles(repo) {
  const cfg = loadConfig(repo);
  const allow = new Set(cfg.largeFileAllowlist ?? []);
  const bad = [];
  for (const rel of trackedFiles(repo)) {
    let size;
    try { size = statSync(resolve(repo, rel)).size; }
    catch { continue; }
    if (size > MAX_BYTES && !allow.has(rel)) bad.push({ rel, size });
  }
  return bad;
}

test('no tracked file above 5 MiB without an allow-list reason', () => {
  const bad = largeFiles(REPO);
  assert.deepEqual(bad, []);
});

test('FAILS on a fixture with a 6 MiB blob', () => {
  const repo = makeRepo([{ path: 'blob.bin', size: 6 * 1024 * 1024 }]);
  try {
    const bad = largeFiles(repo);
    assert.ok(bad.length > 0, 'expected the 6 MiB blob to be reported');
    assert.ok(bad[0].size > MAX_BYTES);
  } finally { cleanup(repo); }
});
