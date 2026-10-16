#!/usr/bin/env node
// no-database-files.test.mjs -- SKL-W0-01 TASK-0006
//
// No tracked file may be a SQLite/SQLite-WAL/SQLite-SHM artefact or a journal
// file. These are runtime state that must never be committed; a checkout that
// carries them drags local database state into version control.
//
// Patterns: *.db, *.db-wal, *.db-shm, *.sqlite, *.sqlite-wal, *.sqlite-shm,
// *.journal, *.journal-wal, *.journal-shm.
//
// Run against the real repository (expect clean) and against a fixture
// repository seeded with one artefact of each kind (expect failures).

import { test } from 'node:test';
import assert from 'node:assert/strict';
import { REPO, makeRepo, cleanup, trackedFiles } from './_fixture.mjs';

const DB_PATTERNS = [
  /\.db$/, /\.db-wal$/, /\.db-shm$/,
  /\.sqlite$/, /\.sqlite-wal$/, /\.sqlite-shm$/,
  /\.journal$/, /\.journal-wal$/, /\.journal-shm$/,
];

function dbFiles(repo) {
  const out = [];
  for (const rel of trackedFiles(repo)) {
    for (const p of DB_PATTERNS) {
      if (p.test(rel)) { out.push(rel); break; }
    }
  }
  return out;
}

test('no tracked database or journal files', () => {
  const bad = dbFiles(REPO);
  assert.deepEqual(bad, []);
});

test('FAILS on a fixture with a *.db file', () => {
  const repo = makeRepo([{ path: 'state.db', content: 'SQLite format 3\x00' }]);
  try {
    assert.ok(dbFiles(repo).length > 0, 'expected the .db file to be reported');
  } finally { cleanup(repo); }
});

test('FAILS on a fixture with a *.db-wal file', () => {
  const repo = makeRepo([{ path: 'state.db-wal', content: 'wal' }]);
  try {
    assert.ok(dbFiles(repo).length > 0, 'expected the .db-wal file to be reported');
  } finally { cleanup(repo); }
});

test('FAILS on a fixture with a *.db-shm file', () => {
  const repo = makeRepo([{ path: 'state.db-shm', content: 'shm' }]);
  try {
    assert.ok(dbFiles(repo).length > 0, 'expected the .db-shm file to be reported');
  } finally { cleanup(repo); }
});

test('FAILS on a fixture with a *.sqlite file', () => {
  const repo = makeRepo([{ path: 'cache.sqlite', content: 'SQLite format 3\x00' }]);
  try {
    assert.ok(dbFiles(repo).length > 0, 'expected the .sqlite file to be reported');
  } finally { cleanup(repo); }
});

test('FAILS on a fixture with a *.journal file', () => {
  const repo = makeRepo([{ path: 'rollback.journal', content: 'journal' }]);
  try {
    assert.ok(dbFiles(repo).length > 0, 'expected the .journal file to be reported');
  } finally { cleanup(repo); }
});
