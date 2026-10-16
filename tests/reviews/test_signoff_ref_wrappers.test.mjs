#!/usr/bin/env node
// test_signoff_ref_wrappers.test.mjs -- SKL-W1-02 TASK-0004
// Regression: every ref-* wrapper carries reviewed_by: UNVERIFIED and the
// validator refuses certified status without docs/reviews/<skill>.md.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync, writeFileSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { execFileSync } from 'node:child_process';

const HERE = dirname(fileURLToPath(import.meta.url));
const REPO = join(HERE, '..', '..');
const SKILLS = join(REPO, 'skills');
const REVIEWS = join(REPO, 'docs', 'reviews');

const WRAPPERS = [
  'ref-datev-extf',
  'ref-gobd-archive',
  'ref-xrechnung-zugferd',
  'ref-ust-edge-cases',
  'ref-bank-reconciliation-camt',
  'ref-webhooks-safe',
];

function audit(args) {
  return execFileSync('python3', [join(REPO, 'scripts', 'validate_reviewed_by.py'), ...args], {
    encoding: 'utf8', cwd: REPO,
  });
}

for (const name of WRAPPERS) {
  test(`wrapper ${name} is marked reviewed_by: UNVERIFIED`, () => {
    const text = readFileSync(join(SKILLS, name, name, 'SKILL.md'), 'utf8');
    assert.match(text, /^reviewed_by: UNVERIFIED$/m,
      `${name} must stay at the UNVERIFIED sentinel`);
  });

  test(`wrapper ${name} has a sign-off placeholder under docs/reviews/`, () => {
    const review = join(REVIEWS, `${name}.md`);
    const text = readFileSync(review, 'utf8');
    assert.match(text, /Status: UNVERIFIED/);
    assert.match(text, /Reviewed by: \*\*UNVERIFIED — pending signature\*\*/);
    assert.match(text, /Date: \*\*pending\*\*/);
  });
}

test('the audit reports all six wrappers as unverified and exits 0', () => {
  const out = audit(['--json']);
  const report = JSON.parse(out);
  assert.ok(report.ok, `audit problems: ${JSON.stringify(report.problems)}`);
  const names = report.unverified.map((e) => e.skill).sort();
  assert.deepEqual(names, [...WRAPPERS].sort());
});

test('property: a wrapper promoted to certified without a filled sign-off block fails the audit', () => {
  const md = join(SKILLS, 'ref-ust-edge-cases', 'ref-ust-edge-cases', 'SKILL.md');
  const review = join(REVIEWS, 'ref-ust-edge-cases.md');
  const mdBackup = readFileSync(md, 'utf8');
  const reviewBackup = readFileSync(review, 'utf8');
  const empty = reviewBackup
    .replace('Reviewed by: **UNVERIFIED — pending signature**', 'Reviewed by: Dr. Anna Meier')
    .replace('Date: **pending**', 'Date: 2026-10-16')
    .replace('Signature: ___________________________________', 'Signature: ___________________________________');
  writeFileSync(md, mdBackup.replace(/^reviewed_by: UNVERIFIED$/m, 'reviewed_by: Dr. Anna Meier'), 'utf8');
  writeFileSync(review, empty, 'utf8');
  try {
    let threw = false;
    try { audit(['--json']); } catch (e) { threw = true; }
    assert.ok(threw, 'audit must fail when a certified wrapper has an empty sign-off block');
  } finally {
    writeFileSync(md, mdBackup, 'utf8');
    writeFileSync(review, reviewBackup, 'utf8');
  }
});
