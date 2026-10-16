#!/usr/bin/env node
// test_gen_preamble.test.mjs -- SKL-W1-02 TASK-0004 (pytest suite)
// Unit + property + golden-file tests for scripts/gen-preamble.mjs.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync, writeFileSync, renameSync, existsSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { execFileSync } from 'node:child_process';

const HERE = dirname(fileURLToPath(import.meta.url));
const REPO = join(HERE, '..', '..');
const GEN = join(REPO, 'scripts', 'gen-preamble.mjs');
const OUT = join(REPO, 'skills', 'orchestrator-preamble', 'orchestrator-preamble', 'references', 'preamble.md');
const GOLDEN = join(HERE, 'golden', 'preamble.md');

function run(args) {
  return execFileSync('node', [GEN, ...args], { encoding: 'utf8', cwd: REPO });
}

test('gen-preamble.mjs --help prints usage and exits 0', () => {
  const out = run(['--help']);
  assert.match(out, /Usage: node scripts\/gen-preamble.mjs/);
  assert.match(out, /--check/);
  assert.match(out, /Exit codes:/);
});

test('gen-preamble.mjs --check passes on the committed body (exit 0)', () => {
  const out = run(['--check']);
  assert.match(out, /preamble.md is up to date/);
});

test('golden-file: committed preamble.md matches tests/golden/preamble.md byte-for-byte', () => {
  const committed = readFileSync(OUT, 'utf8');
  const golden = readFileSync(GOLDEN, 'utf8');
  assert.equal(committed, golden, 'committed preamble.md diverges from the golden copy');
});

test('the committed preamble.md is <= 60 lines', () => {
  const lines = readFileSync(OUT, 'utf8').split('\n');
  assert.ok(lines.length <= 60, `preamble.md is ${lines.length} lines (> 60)`);
});

test('the preamble lists the four rules with their exact check commands', () => {
  const text = readFileSync(OUT, 'utf8');
  assert.match(text, /^# Orchestrator Preamble \(generated\)$/m);
  for (const gate of [
    'python3 scripts/check_rls_migration.py <migration.sql>',
    'python3 scripts/check_outbox.py <sql-file>',
    'python3 scripts/check_problem_catalogue.py --catalogue <cat> --openapi <spec> --schema-dir <dir>',
    'python3 scripts/check_status_evidence.py STATUS.md --root .',
  ]) {
    assert.ok(text.includes(gate), `gate command missing: ${gate}`);
  }
});

test('property: the generator is deterministic (same input -> same bytes)', () => {
  const a = run([]);
  const b = run([]);
  assert.equal(a, b);
});

test('regression: --check fails (exit 1) when the body is stale', () => {
  const backup = readFileSync(OUT, 'utf8');
  writeFileSync(OUT, backup + '\n// stale marker\n', 'utf8');
  let threw = false;
  try {
    run(['--check']);
  } catch (e) {
    threw = true;
    assert.match(e.stderr || e.stdout || '', /stale/);
  }
  assert.ok(threw, '--check must exit non-zero on a stale body');
  writeFileSync(OUT, backup, 'utf8');
});

test('regression: --check fails (exit 1) when the body is missing', () => {
  const backup = readFileSync(OUT, 'utf8');
  renameSync(OUT, OUT + '.missing-stash');
  let threw = false;
  try {
    run(['--check']);
  } catch (e) {
    threw = true;
    assert.match(e.stderr || e.stdout || '', /missing/);
  }
  assert.ok(threw, '--check must exit non-zero on a missing body');
  renameSync(OUT + '.missing-stash', OUT);
  writeFileSync(OUT, backup, 'utf8');
});
