#!/usr/bin/env node
// test_preamble_reproducible.test.mjs -- SKL-W1-02 TASK-0002
// Verifies the orchestrator preamble is generated, short, reproducible and wired to
// the four canonical engineering skills' gate commands.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync, writeFileSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { execFileSync } from 'node:child_process';

const HERE = dirname(fileURLToPath(import.meta.url));
const REPO = join(HERE, '..', '..');
const PREAMBLE = join(REPO, 'skills', 'orchestrator-preamble', 'orchestrator-preamble', 'references', 'preamble.md');
const GEN = join(REPO, 'scripts', 'gen-preamble.mjs');

function runGen() {
  return execFileSync('node', [GEN], { cwd: REPO, encoding: 'utf8' });
}

test('preamble.md exists and is <= 60 lines', () => {
  const lines = readFileSync(PREAMBLE, 'utf8').split('\n');
  assert.ok(lines.length <= 60, `preamble is ${lines.length} lines, expected <= 60`);
  assert.ok(lines[0].startsWith('# Orchestrator Preamble'));
});

test('generator is reproducible: two runs produce byte-identical output', () => {
  runGen();
  const first = readFileSync(PREAMBLE, 'utf8');
  runGen();
  const second = readFileSync(PREAMBLE, 'utf8');
  assert.equal(second, first);
});

test('generator --check exits 0 against the committed file', () => {
  const out = execFileSync('node', [GEN, '--check'], { cwd: REPO, encoding: 'utf8' });
  assert.ok(out.includes('up to date'), out);
});

test('preamble contains all four canonical gate commands', () => {
  const body = readFileSync(PREAMBLE, 'utf8');
  for (const cmd of ['check_rls_migration.py', 'check_outbox.py', 'check_problem_catalogue.py', 'check_status_evidence.py']) {
    assert.ok(body.includes(cmd), `preamble missing gate command: ${cmd}`);
  }
});

test('generator refuses when a canonical gate command drifts from its skill', () => {
  const skill = join(REPO, 'skills', 'engineering', 'honest-status', 'SKILL.md');
  const backup = readFileSync(skill, 'utf8');
  try {
    writeFileSync(skill, backup.replace('check_status_evidence.py', 'check_status_evidence DRIFTED.py'), 'utf8');
    assert.throws(() => runGen());
  } finally {
    writeFileSync(skill, backup, 'utf8');
  }
});
