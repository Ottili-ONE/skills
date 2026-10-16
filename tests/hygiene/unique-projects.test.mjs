#!/usr/bin/env node
// unique-projects.test.mjs -- SKL-W0-01 TASK-0006
//
// Every workspace project name is unique. A "workspace project" is either a
// package directory under skills/ (skills/<package>/) or a skill directory
// (skills/<package>/<skill>/) that carries a SKILL.md. Two projects may not
// share a name -- a duplicate name makes the catalogue ambiguous and lets one
// skill silently shadow another at install time.
//
// Run against the real repository (expect clean) and against a fixture
// repository containing a duplicate skill name (expect failure).

import { test } from 'node:test';
import assert from 'node:assert/strict';
import { join } from 'node:path';
import { REPO, makeRepo, cleanup, trackedFiles } from './_fixture.mjs';

function projects(repo) {
  const names = [];
  for (const rel of trackedFiles(repo)) {
    if (!rel.startsWith('skills/')) continue;
    if (rel.endsWith('/SKILL.md')) {
      // skills/<package>/<skill>/SKILL.md -> project name is the skill dir
      const parts = rel.split('/');
      if (parts.length >= 4) names.push({ name: parts[parts.length - 2], rel });
    }
  }
  return names;
}

function duplicates(repo) {
  const seen = new Map();
  for (const p of projects(repo)) {
    if (seen.has(p.name)) { seen.get(p.name).push(p.rel); }
    else seen.set(p.name, [p.rel]);
  }
  return [...seen.entries()].filter(([, v]) => v.length > 1)
    .map(([name, rels]) => ({ name, rels }));
}

test('every workspace project name is unique', () => {
  const bad = duplicates(REPO);
  assert.deepEqual(bad, []);
});

test('FAILS on a fixture with a duplicate skill name', () => {
  const repo = makeRepo([
    { path: 'skills/core/alpha/SKILL.md', content: '# alpha\n' },
    { path: 'skills/core/beta/SKILL.md', content: '# beta\n' },
    { path: 'skills/curated/alpha/SKILL.md', content: '# alpha again\n' },
  ]);
  try {
    const bad = duplicates(repo);
    assert.ok(bad.length > 0, 'expected the duplicate skill name to be reported');
    assert.equal(bad[0].name, 'alpha');
  } finally { cleanup(repo); }
});
