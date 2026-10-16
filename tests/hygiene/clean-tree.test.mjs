#!/usr/bin/env node
// clean-tree.test.mjs -- SKL-W0-01 TASK-0003 (tree-dirtying tests)
//
// A checkout of this repository must leave `git status --porcelain` empty:
// no untracked files, no modifications, no uncommitted artefacts. Every test
// module therefore runs under this assertion, so a test that writes outside
// the worktree fails the suite instead of silently dirtying the tree.
//
// Usage:
//   node tests/hygiene/clean-tree.test.mjs            # expect clean  (exit 0)
//   node tests/hygiene/clean-tree.test.mjs --dirty    # seed a stray file,
//                                                    # expect dirty   (exit 1)
//
// Run from anywhere; it resolves the repo root from its own location.
import { spawnSync } from 'node:child_process';
import { writeFileSync, rmSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = fileURLToPath(import.meta.url);
const REPO = resolve(dirname(here), '..', '..');
const SEED = resolve(REPO, '.hygiene-seed');

function gitStatus() {
  const r = spawnSync('git', ['-C', REPO, 'status', '--porcelain'],
    { encoding: 'utf-8' });
  if (r.error) throw r.error;
  return r.stdout;
}

function run(label, expectClean) {
  const out = gitStatus();
  const clean = out.trim() === '';
  const ok = clean === expectClean;
  console.log(`${ok ? 'PASS' : 'FAIL'} ${label}: clean=${clean} expectClean=${expectClean}`);
  if (!ok) console.log(out.trim() || '(empty)');
  return ok;
}

const dirty = process.argv.includes('--dirty');
if (dirty) writeFileSync(SEED, 'seeded by clean-tree.test.mjs --dirty\n');

const allOk = run('git status --porcelain is empty', !dirty);

if (dirty) rmSync(SEED, { force: true });

process.exit(allOk ? 0 : 1);
