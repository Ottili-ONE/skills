#!/usr/bin/env node
// Integrity manifest of the truth kit itself.
//   node scripts/truth/manifest.mjs --write     regenerate scripts/truth/MANIFEST.sha256 (operator only, after updating the kit)
//   node scripts/truth/manifest.mjs --check     verify every kit file against the manifest (exit 1 on any difference)
// config.json and node_modules are not part of the manifest: the operator and the first repair job tune config.json.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { sha256 } from './lib/common.mjs';

const KIT = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(KIT, '..', '..');
const SKIP = new Set(['config.json', 'MANIFEST.sha256', 'node_modules', 'package-lock.json']);

function list(dir, out = []) {
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    if (SKIP.has(e.name)) continue;
    const full = path.join(dir, e.name);
    if (e.isDirectory()) list(full, out);
    else if (e.isFile()) out.push(full);
  }
  return out;
}

const lines = list(KIT)
  .map((f) => `${sha256(fs.readFileSync(f))}  ${path.relative(ROOT, f).split(path.sep).join('/')}`)
  .sort((a, b) => a.slice(66).localeCompare(b.slice(66)));
const manifest = path.join(KIT, 'MANIFEST.sha256');

if (process.argv.includes('--write')) {
  fs.writeFileSync(manifest, `${lines.join('\n')}\n`);
  process.stdout.write(`wrote ${path.relative(ROOT, manifest)} (${lines.length} files)\n`);
} else {
  const expected = fs.existsSync(manifest) ? fs.readFileSync(manifest, 'utf8').split('\n').filter(Boolean) : [];
  const missing = expected.filter((l) => !lines.includes(l));
  const extra = lines.filter((l) => !expected.includes(l));
  if (expected.length === 0 || missing.length || extra.length) {
    process.stderr.write(`kit differs from MANIFEST.sha256 (${missing.length} changed or missing, ${extra.length} new or changed)\n`);
    process.exit(1);
  }
  process.stdout.write(`kit matches MANIFEST.sha256 (${lines.length} files)\n`);
}
