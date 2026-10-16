#!/usr/bin/env node
// workspace-protocol.test.mjs -- SKL-W0-01 TASK-0006
//
// Every internal dependency declared in a tracked package.json must use the
// workspace protocol (`workspace:*`, `workspace:^`, `workspace:~`). Internal
// means scoped to @ottili or resolved from a sibling workspace directory --
// never a version range pulled from a registry, and never a relative path.
//
// Run against the real repository (expect clean) and against a fixture
// repository whose package.json pins an internal dependency to a registry
// version (expect failure).

import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { REPO, makeRepo, cleanup, trackedFiles } from './_fixture.mjs';

const WS_RE = /^workspace:/;

function violations(repo) {
  const bad = [];
  for (const rel of trackedFiles(repo)) {
    if (!rel.endsWith('package.json')) continue;
    let pkg;
    try { pkg = JSON.parse(readFileSync(resolve(repo, rel), 'utf-8')); }
    catch { continue; }
    const deps = { ...(pkg.dependencies || {}), ...(pkg.devDependencies || {}) };
    for (const [name, range] of Object.entries(deps)) {
      const internal = name.startsWith('@ottili/') ||
        name.startsWith('@ottili-') ||
        name.startsWith('@');
      if (!internal) continue;
      if (!WS_RE.test(String(range))) {
        bad.push({ file: rel, name, range: String(range) });
      }
    }
  }
  return bad;
}

test('every internal dependency uses the workspace protocol', () => {
  const bad = violations(REPO);
  assert.deepEqual(bad, []);
});

test('FAILS on a fixture with a registry-pinned @ottili dependency', () => {
  const repo = makeRepo([
    { path: 'package.json', content: JSON.stringify({
      name: 'fixture',
      version: '1.0.0',
      dependencies: { '@ottili/platform-client': '^2.0.0' },
    }) },
  ]);
  try {
    const bad = violations(repo);
    assert.ok(bad.length > 0, 'expected the registry-pinned dependency to be reported');
    assert.equal(bad[0].name, '@ottili/platform-client');
  } finally { cleanup(repo); }
});

test('FAILS on a fixture with a relative-path dependency', () => {
  const repo = makeRepo([
    { path: 'package.json', content: JSON.stringify({
      name: 'fixture',
      version: '1.0.0',
      dependencies: { '@ottili/utils': '../utils' },
    }) },
  ]);
  try {
    const bad = violations(repo);
    assert.ok(bad.length > 0, 'expected the relative-path dependency to be reported');
  } finally { cleanup(repo); }
});
