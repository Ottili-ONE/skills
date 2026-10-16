#!/usr/bin/env node
// npmrc-scope.test.mjs -- SKL-W0-01 TASK-0006
//
// .npmrc must map the @ottili scope to the private registry and must not
// configure a fallback to the public registry for that scope. The scope line
// is `@ottili:registry=<url>` and the default registry line is a bare
// `registry=<url>`; a bare `registry=` line applies only to unscoped packages,
// so it is allowed. What is not allowed is a second `@ottili:registry=` line
// (which would silently redirect the scope) or a scoped fallback such as
// `@ottili:registry=https://registry.npmjs.org/`.
//
// Run against the real repository (expect clean) and against a fixture
// repository whose .npmrc falls back the scope to the public registry
// (expect failure).

import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { REPO, makeRepo, cleanup } from './_fixture.mjs';

const SCOPE = '@ottili:registry=';

function npmrc(repo) {
  try {
    return readFileSync(resolve(repo, '.npmrc'), 'utf-8');
  } catch {
    return '';
  }
}

function violations(repo) {
  const text = npmrc(repo);
  const bad = [];
  const lines = text.split('\n');
  let scopeLines = 0;
  for (const raw of lines) {
    const line = raw.trim();
    if (!line || line.startsWith('#')) continue;
    if (line.startsWith('@ottili:registry=')) {
      scopeLines++;
      const url = line.slice('@ottili:registry='.length);
      if (/registry\.npmjs\.org/.test(url)) {
        bad.push({ reason: 'scope falls back to the public registry', line });
      }
    }
  }
  if (scopeLines === 0) bad.push({ reason: 'no @ottili scope mapping', line: null });
  if (scopeLines > 1) bad.push({ reason: 'duplicate @ottili scope mapping', line: null });
  return bad;
}

test('.npmrc maps @ottili to the private registry with no public fallback', () => {
  const bad = violations(REPO);
  assert.deepEqual(bad, []);
});

test('FAILS on a fixture whose .npmrc falls back the scope to npmjs.org', () => {
  const repo = makeRepo([
    { path: '.npmrc', content:
      '@ottili:registry=https://registry.npmjs.org/\n' +
      'registry=https://registry.npmjs.org/\n' },
  ]);
  try {
    const bad = violations(repo);
    assert.ok(bad.length > 0, 'expected the public-registry fallback to be reported');
  } finally { cleanup(repo); }
});

test('FAILS on a fixture whose .npmrc has no scope mapping at all', () => {
  const repo = makeRepo([
    { path: '.npmrc', content: 'registry=https://registry.npmjs.org/\n' },
  ]);
  try {
    const bad = violations(repo);
    assert.ok(bad.length > 0, 'expected the missing scope mapping to be reported');
  } finally { cleanup(repo); }
});
