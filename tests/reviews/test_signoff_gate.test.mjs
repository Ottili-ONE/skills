#!/usr/bin/env node
// test_signoff_gate.test.mjs -- SKL-W1-02 TASK-0002
// Exercises scripts/validate_reviewed_by.py: the UNVERIFIED sentinel, the
// filled-signoff certifier and the fail-closed cases.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync, writeFileSync, renameSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { execFileSync } from 'node:child_process';

const HERE = dirname(fileURLToPath(import.meta.url));
const REPO = join(HERE, '..', '..');
const VALIDATOR = join(REPO, 'scripts', 'validate_reviewed_by.py');
const REVIEWS = join(REPO, 'docs', 'reviews');

function audit(args) {
  return execFileSync('python3', [VALIDATOR, ...args], { cwd: REPO, encoding: 'utf8' });
}

function frontmatter(name) {
  const md = join(REPO, 'skills', name, name, 'SKILL.md');
  const text = readFileSync(md, 'utf8');
  const m = text.match(/^---\s*\n([\s\S]*?)\n---\s*\n/);
  assert.ok(m, `no frontmatter in ${md}`);
  const out = {};
  for (const line of m[1].split('\n')) {
    const i = line.indexOf(':');
    if (i < 0) continue;
    out[line.slice(0, i).trim()] = line.slice(i + 1).trim().replace(/^["']|["']$/g, '');
  }
  return out;
}

const NAMES = [
  'ref-datev-extf', 'ref-gobd-archive', 'ref-xrechnung-zugferd',
  'ref-ust-edge-cases', 'ref-bank-reconciliation-camt', 'ref-webhooks-safe',
];

test('all six ref-* wrappers carry reviewed_by: UNVERIFIED', () => {
  for (const n of NAMES) {
    assert.equal(frontmatter(n).reviewed_by, 'UNVERIFIED', n);
  }
});

test('audit reports the six wrappers as unverified and exits 0', () => {
  const report = JSON.parse(audit(['--json']));
  const unverified = report.unverified.map((e) => e.skill);
  for (const n of NAMES) {
    assert.ok(unverified.includes(n), `${n} not reported unverified`);
  }
  assert.equal(report.problems.length, 0, JSON.stringify(report.problems));
});

test('UNVERIFIED skills never block: non-strict audit exits 0', () => {
  assert.doesNotThrow(() => audit([]));
});

test('a filled sign-off block certifies the skill (audit exits 0, entry ok)', () => {
  const file = join(REVIEWS, 'ref-ust-edge-cases.md');
  const backup = readFileSync(file, 'utf8');
  const filled = backup
    .replace('| Reviewed by | **UNVERIFIED — pending signature** |', '| Reviewed by | Dr. Anna Meier |')
    .replace('| Date | **pending** |', '| Date | 2026-10-16 |')
    .replace('Date: _______________', 'Date: 2026-10-16')
    .replace('Reviewed by: ___________________________________', 'Reviewed by: Dr. Anna Meier')
    .replace('Signature: ___________________________________', 'Signature: Dr. Anna Meier')
    .replace('Findings: ___________________________________', 'Findings: §13b scope and igL citation confirmed correct');
  const md = join(REPO, 'skills', 'ref-ust-edge-cases', 'ref-ust-edge-cases', 'SKILL.md');
  const mdBackup = readFileSync(md, 'utf8');
  writeFileSync(md, mdBackup.replace(/^reviewed_by: UNVERIFIED$/m, 'reviewed_by: Dr. Anna Meier'), 'utf8');
  writeFileSync(file, filled, 'utf8');
  try {
    assert.doesNotThrow(() => audit(['--json']));
    const report = JSON.parse(audit(['--json']));
    const cert = report.certified.find((e) => e.skill === 'ref-ust-edge-cases');
    assert.ok(cert, 'ref-ust-edge-cases not certified');
    assert.equal(cert.ok, true);
  } finally {
    writeFileSync(file, backup, 'utf8');
    writeFileSync(md, mdBackup, 'utf8');
  }
});

test('a certified skill with an empty sign-off block is a problem (audit exits non-zero)', () => {
  const file = join(REVIEWS, 'ref-ust-edge-cases.md');
  const backup = readFileSync(file, 'utf8');
  const empty = backup
    .replace('| Reviewed by | **UNVERIFIED — pending signature** |', '| Reviewed by | Dr. Anna Meier |')
    .replace('Reviewed by: ___________________________________', 'Reviewed by: ___________________________________')
    .replace('Date: _______________', 'Date: _______________')
    .replace('Signature: ___________________________________', 'Signature: ___________________________________');
  const md = join(REPO, 'skills', 'ref-ust-edge-cases', 'ref-ust-edge-cases', 'SKILL.md');
  const mdBackup = readFileSync(md, 'utf8');
  writeFileSync(md, mdBackup.replace(/^reviewed_by: UNVERIFIED$/m, 'reviewed_by: Dr. Anna Meier'), 'utf8');
  writeFileSync(file, empty, 'utf8');
  try {
    let threw = false;
    try { audit(['--json']); } catch (e) { threw = true; }
    assert.ok(threw, 'audit should fail when a certified skill has an empty sign-off block');
  } finally {
    writeFileSync(file, backup, 'utf8');
    writeFileSync(md, mdBackup, 'utf8');
  }
});

test('a certified skill whose review file is missing is a problem (audit exits non-zero)', () => {
  const md = join(REPO, 'skills', 'ref-ust-edge-cases', 'ref-ust-edge-cases', 'SKILL.md');
  const review = join(REVIEWS, 'ref-ust-edge-cases.md');
  const mdBackup = readFileSync(md, 'utf8');
  const reviewBackup = readFileSync(review, 'utf8');
  const stash = review + '.missing-stash';
  writeFileSync(md, mdBackup.replace(/^reviewed_by: UNVERIFIED$/m, 'reviewed_by: Dr. Anna Meier'), 'utf8');
  renameSync(review, stash);
  try {
    let threw = false;
    try { audit(['--json']); } catch (e) { threw = true; }
    assert.ok(threw, 'audit should fail when a certified skill has no sign-off file');
  } finally {
    renameSync(stash, review);
    writeFileSync(md, mdBackup, 'utf8');
  }
});
