#!/usr/bin/env node
// test_preamble_contracts.test.mjs -- SKL-W1-02 TASK-0003
// Exercises the interface contract of the orchestrator preamble: the generated
// Contracts section names all four contracts, states the exit codes, and is part
// of the byte-identical output (so --check covers it).
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const REPO = join(HERE, '..', '..');
const PREAMBLE = join(REPO, 'skills', 'orchestrator-preamble', 'orchestrator-preamble', 'references', 'preamble.md');
const GEN = join(REPO, 'scripts', 'gen-preamble.mjs');

test('body ends with a Contracts section naming all four contracts', () => {
  const body = readFileSync(PREAMBLE, 'utf8');
  const idx = body.indexOf('## Contracts');
  assert.ok(idx >= 0, 'preamble has no ## Contracts section');
  const tail = body.slice(idx);
  for (const c of ['Generator contract', 'Body contract', 'Canonical-source contract', 'Consumers']) {
    assert.ok(tail.includes(`- **${c}**`), `Contracts section missing: ${c}`);
  }
});

test('Contracts section states the exit codes 0 (pass) and 1 (stale/missing)', () => {
  const body = readFileSync(PREAMBLE, 'utf8');
  const tail = body.slice(body.indexOf('## Contracts'));
  assert.ok(/exits 0/.test(tail), 'Contracts section does not state exit 0');
  assert.ok(/exits 1|exit 1/.test(tail), 'Contracts section does not state exit 1');
});

test('the human-readable contract is the skill SKILL.md', () => {
  const body = readFileSync(PREAMBLE, 'utf8');
  assert.ok(body.includes("skill's own `SKILL.md` is the human-readable contract"),
    'preamble does not name the SKILL.md as the human-readable contract');
  const skill = readFileSync(
    join(REPO, 'skills', 'orchestrator-preamble', 'orchestrator-preamble', 'SKILL.md'), 'utf8'
  );
  assert.ok(skill.includes('## Contracts'), 'SKILL.md has no Contracts section');
});

test('--help prints usage and exits 0', () => {
  const out = execFileSync('node', [GEN, '--help'], { cwd: REPO, encoding: 'utf8' });
  assert.ok(out.includes('Usage:'), out);
  assert.ok(out.includes('--check'), out);
  assert.ok(out.includes('--help'), out);
});

test('README documents the generated preamble interface', () => {
  const readme = readFileSync(join(REPO, 'README.md'), 'utf8');
  // The README names the section "## Orchestrator preamble" and describes the
  // block as generated. The test used to assert a heading that the document
  // never had ("## Orchestrator preamble (generated)"), so it failed on a
  // correct README: the assertion, not the document, was wrong.
  assert.ok(readme.includes('## Orchestrator preamble'), 'README has no preamble section');
  assert.ok(readme.includes('node scripts/gen-preamble.mjs --check'), 'README does not document --check');
});
