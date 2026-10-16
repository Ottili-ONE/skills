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
  // The phrase "services only" may only appear as the *quotation of the error* being
  // corrected (e.g. `reverse charge (§13b) applies to services only`), never as a
  // statement of the rule itself.
  const errorQuotations = text.match(/applies to services only/g) || [];
  assert.ok(errorQuotations.length <= 1, `unexpected "services only" occurrences: ${errorQuotations.length}`);
  assert.match(text, /goods AND services/);
  // The Abs. 1 list reference is split across two lines in the SKILL.md quote, so
  // match the pieces separately rather than one anchored regex.
  assert.match(text, /§13b Abs\. 1/);
  assert.match(text, /Nr\. 1-11/);
  assert.match(text, /Werklieferungen/);
});

test('§13b is NOT narrowed to services; goods may fall inside the reverse-charge list', () => {
  const text = readFileSync(SKILL, 'utf8');
  // Substring checks (the wrapper prose is multi-line, so anchored regexes are brittle).
  assert.ok(text.includes('a goods supply'), 'wrapper must discuss a goods supply');
  assert.ok(text.includes('may fall inside the §13b reverse-charge list'),
    'wrapper must state goods may fall inside the reverse-charge list');
  assert.ok(text.includes('is NOT "services only"'), 'wrapper must say the rule is NOT services only');
  assert.ok(text.includes('the full §13b Abs. 1 list must be consulted per transaction'),
    'wrapper must require consulting the full Abs. 1 list per transaction');
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
  assert.match(text, /igL\) is NOT §4a UStG/);
  assert.match(text, /§4 Nr\. 1b/);
  assert.match(text, /§6a/);
  assert.match(text, /Reviewed by \| \*\*UNVERIFIED — pending signature\*\*/);
  assert.match(text, /Date \| \*\*pending\*\*/);
});
