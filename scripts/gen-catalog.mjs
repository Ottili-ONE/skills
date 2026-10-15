#!/usr/bin/env node
// gen-catalog.mjs — generate catalog.json from the skills/ folders.
//
// The catalogue is GENERATED, never hand-edited: this script walks every
// skills/<package>/<name>/SKILL.md, reads the YAML frontmatter, and writes one
// entry per skill. Packages are DERIVED from the top-level folders under
// skills/ (a folder that contains skill subfolders is a package); there is no
// hand-maintained package or skill list anywhere in this file.
//
// Usage:  node scripts/gen-catalog.mjs [--check] [--out catalog.json]
//   --check   do not write; exit 1 if the existing catalog.json would change.
//   --out P   write to P (default: <repo>/catalog.json).

import { readFileSync, readdirSync, existsSync, writeFileSync } from 'node:fs';
import { resolve, dirname, basename, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const REPO = resolve(HERE, '..');
const SKILLS_DIR = resolve(REPO, 'skills');
const DEFAULT_OUT = resolve(REPO, 'catalog.json');

const args = process.argv.slice(2);
let check = false;
let outPath = DEFAULT_OUT;
for (let i = 0; i < args.length; i++) {
  if (args[i] === '--check') check = true;
  else if (args[i] === '--out') { outPath = resolve(args[++i]); }
  else if (args[i].startsWith('--out=')) { outPath = resolve(args[i].slice(7)); }
}

// --- minimal YAML-frontmatter parser (frontmatter only, no YAML lib needed) ---
function parseFrontmatter(text) {
  const m = text.match(/^---\s*\n([\s\S]*?)\n---\s*\n/);
  if (!m) return {};
  const fields = {};
  for (const line of m[1].split('\n')) {
    if (!line || line.trim().startsWith('#') || !line.includes(':')) continue;
    const idx = line.indexOf(':');
    let k = line.slice(0, idx).trim();
    let v = line.slice(idx + 1).trim();
    if ((v.startsWith('"') && v.endsWith('"')) || (v.startsWith("'") && v.endsWith("'"))) v = v.slice(1, -1);
    if (k) fields[k] = v;
  }
  return fields;
}

function listSkillDirs(dir) {
  // Returns [packageName, skillName, absDirPath] for every folder containing SKILL.md.
  const out = [];
  if (!existsSync(dir)) return out;
  for (const pkg of readdirSync(dir, { withFileTypes: true })) {
    if (!pkg.isDirectory()) continue;
    if (pkg.name.startsWith('.') || pkg.name === 'node_modules') continue;
    const pkgDir = join(dir, pkg.name);
    for (const skill of readdirSync(pkgDir, { withFileTypes: true })) {
      if (!skill.isDirectory()) continue;
      const skillDir = join(pkgDir, skill.name);
      if (existsSync(join(skillDir, 'SKILL.md'))) {
        out.push([pkg.name, skill.name, skillDir]);
      }
    }
  }
  return out;
}

function walkFiles(dir, files = []) {
  for (const e of readdirSync(dir, { withFileTypes: true })) {
    const p = join(dir, e.name);
    if (e.isDirectory()) walkFiles(p, files);
    else files.push(p);
  }
  return files.sort();
}

function main() {
  const found = listSkillDirs(SKILLS_DIR).sort((a, b) => {
    const pc = a[0].localeCompare(b[0]);
    return pc || a[1].localeCompare(b[1]);
  });

  // Packages are DERIVED from the folders that actually contain skills.
  const packages = {};
  const seenPkg = new Set();
  for (const [pkg] of found) seenPkg.add(pkg);
  for (const pkg of [...seenPkg].sort()) {
    packages[pkg] = {
      label: pkg.charAt(0).toUpperCase() + pkg.slice(1),
      description: `Skills in the ${pkg} package.`,
      path: `skills/${pkg}`,
    };
  }

  const skills = [];
  for (const [pkg, name, dir] of found) {
    const fm = parseFrontmatter(readFileSync(join(dir, 'SKILL.md'), 'utf8'));
    const rel = `skills/${pkg}/${name}`;
    const paths = walkFiles(dir).map((p) => p.replace(REPO + '/', ''));
    skills.push({
      id: fm.name || name,
      name: fm.name || name,
      title: fm.title || (fm.name || name).replace(/-/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase()),
      version: fm.version || '',
      package: pkg,
      path: rel,
      category: fm.category || '',
      license: fm.license || '',
      author: fm.author || '',
      compatibility: Array.isArray(fm.compatibility) ? fm.compatibility
        : (fm.compatibility ? fm.compatibility.split(',').map((s) => s.trim()).filter(Boolean) : []),
      description: fm.description || '',
      paths,
    });
  }

  const catalog = {
    schema_version: '1.0.0',
    repository: 'Ottili-ONE/skills',
    updated_at: new Date().toISOString().slice(0, 10),
    packages,
    skills,
  };

  const json = JSON.stringify(catalog, null, 2) + '\n';
  if (check) {
    if (!existsSync(outPath)) { console.error('catalog missing:', outPath); process.exit(1); }
    const existing = readFileSync(outPath, 'utf8');
    if (existing === json) { console.log(`ok: catalog unchanged (${skills.length} skills, ${Object.keys(packages).length} packages)`); return 0; }
    console.error('catalog would change; run without --check to regenerate');
    process.exit(1);
  }

  writeFileSync(outPath, json, 'utf8');
  console.log(`ok: wrote ${outPath} — ${skills.length} skills, ${Object.keys(packages).length} packages`);
  return 0;
}

process.exit(main());
