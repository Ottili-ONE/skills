#!/usr/bin/env node
// test_ust_legal_corrections.test.mjs -- SKL-W1-02 TASK-0002
// Pins the two corrected legal rules into the ref-ust-edge-cases wrapper and its
// sign-off placeholder. These assertions fail against the uncorrected canonical
// skill text (which says "services only" and "§4a UStG").
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const REPO = join(HERE, '..', '..');
const SKILL = join(REPO, 'skills', 'ref-ust-edge-cases', 'ref-ust-edge-cases', 'SKILL.md');
const REVIEW = join(REPO, 'docs', 'reviews', 'ref-ust-edge-cases.md');

test('ref-ust-edge-cases is marked reviewed_by: UNVERIFIED', () => {
  const text = readFileSync(SKILL, 'utf8');
  assert.match(text, /^reviewed_by: UNVERIFIED$/m);
  assert.match(text, /Status: UNVERIFIED/);
});

test('§13b is stated as the full goods+services scope, not "services only"', () => {
  const text = readFileSync(SKILL, 'utf8');
  assert.ok(!/services only/i.test(text), 'wrapper must not say "services only"');
  assert.match(text, /goods AND services/);
  assert.match(text, /§13b Abs\. 1 Nr\. 1-11/);
  assert.match(text, /Werklieferungen/);
});

test('§13b is NOT narrowed to services; goods may fall inside the reverse-charge list', () => {
  const text = readFileSync(SKILL, 'utf8');
  assert.match(text, /a goods supply.*may fall inside the §13b reverse-charge list/);
  assert.ok(!/services only/i.test(text));
});

test('igL is cited as §4 Nr. 1b / §6a, never §4a', () => {
  const text = readFileSync(SKILL, 'utf8');
  assert.match(text, /§4 Nr\. 1b/);
  assert.match(text, /§6a/);
  assert.match(text, /§4a UStG is "Steuervergütung"/);
  assert.ok(!/igL.*=.*§4a(?!.*Nr)/.test(text), 'igL must not be equated with §4a');
});

test('the review placeholder mirrors both corrections', () => {
  const text = readFileSync(REVIEW, 'utf8');
  assert.match(text, /§13b reverse charge is NOT "services only"/);
  assert.match(text, /igL) is NOT §4a UStG/);
  assert.match(text, /§4 Nr\. 1b/);
  assert.match(text, /§6a/);
  assert.match(text, /Reviewed by: \*\*UNVERIFIED — pending signature\*\*/);
  assert.match(text, /Date: \*\*pending\*\*/);
});
