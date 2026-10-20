#!/usr/bin/env node
// gen-catalog.mjs — generate catalog.json from the skills/ folders.
//
// The catalogue is GENERATED, never hand-edited: this script walks every
// skills/<package>/<name>/SKILL.md, reads the YAML frontmatter, and writes one
// entry per skill. Packages are DERIVED from the top-level folders under
// skills/ (a folder that contains skill subfolders is a package); there is no
// hand-maintained package or skill list anywhere in this file.
//
// SOURCE OF TRUTH for the `package` field of an entry: the name of the folder
// that CONTAINS the skill folder — i.e. for skills/<package>/<skill-name>/SKILL.md
// the package is `<package>`. It is taken from the folder layout on disk, never
// from the SKILL.md frontmatter and never from a list maintained by hand.
//
// DETERMINISM: the output is a pure function of the skills/ tree. There is no
// wall-clock stamp anywhere in the file, so a clean clone regenerates
// catalog.json byte-for-byte and `--check` gives the same answer on every day.
//
// Usage:  node scripts/gen-catalog.mjs [--check] [--out catalog.json]
//   --check   do not write; exit 1 if the existing catalog.json would change.
//   --out P   write to P (default: <repo>/catalog.json).
//   --help    Show this help.

import { readFileSync, readdirSync, existsSync, writeFileSync } from 'node:fs';
import { resolve, dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const REPO = resolve(HERE, '..');
const SKILLS_DIR = resolve(REPO, 'skills');
const DEFAULT_OUT = resolve(REPO, 'catalog.json');

// Cache/build artefacts and empty placeholder files that must never appear in
// a generated catalogue. `.gitkeep` exists only to keep empty directories in
// git; it carries no skill content and pollutes the `paths` list.
const IGNORE_DIRS = new Set(['.pytest_cache', '__pycache__', 'node_modules', '.git']);
const IGNORE_FILES = new Set(['.DS_Store', '.gitkeep']);

const args = process.argv.slice(2);
let check = false;
let outPath = DEFAULT_OUT;
const USAGE = 'Usage: gen-catalog.mjs [--check] [--out <file>]';
for (let i = 0; i < args.length; i++) {
  if (args[i] === '--check') check = true;
  else if (args[i] === '--help' || args[i] === '-h') {
    console.log(USAGE);
    process.exit(0);
  }
  else if (args[i] === '--out') {
    const value = args[i + 1];
    if (value === undefined || value === '' || value.startsWith('--')) {
      console.error(`error: --out needs a file path\n${USAGE}`);
      process.exit(2);
    }
    outPath = resolve(value);
    i++;
  }
  else if (args[i].startsWith('--out=')) {
    const value = args[i].slice(6);
    if (value === '') {
      console.error(`error: --out needs a file path\n${USAGE}`);
      process.exit(2);
    }
    outPath = resolve(value);
  }
  else {
    // An unknown option must never be ignored: a typo like "--chek" would
    // otherwise silently WRITE the catalogue instead of checking it.
    console.error(`error: unknown option ${args[i]}\n${USAGE}`);
    process.exit(2);
  }
}

// --- minimal block-style YAML frontmatter parser (frontmatter only) ---
// Handles scalar values (quoted or bare), multi-line list values and nested
// maps such as `compatibility:` / `metadata:`. No YAML library is needed.
function unquote(v) {
  v = v.trim();
  if ((v.startsWith('"') && v.endsWith('"')) || (v.startsWith("'") && v.endsWith("'"))) {
    return v.slice(1, -1);
  }
  return v;
}

function parseFrontmatter(text) {
  const m = text.match(/^---\s*\n([\s\S]*?)\n---\s*\n/);
  if (!m) return {};
  const fields = {};
  const lines = m[1].split('\n');
  let i = 0;
  while (i < lines.length) {
    const line = lines[i];
    if (!line || line.trim().startsWith('#') || !line.includes(':')) { i++; continue; }
    const idx = line.indexOf(':');
    const key = line.slice(0, idx).trim();
    let rest = line.slice(idx + 1).trim();
    if (!key) { i++; continue; }

    if (rest === '' || rest === '|' || rest === '>' || rest === '-') {
      // Block scalar or list: collect following indented lines.
      const block = [];
      i++;
      while (i < lines.length && (lines[i] === '' || /^\s+/.test(lines[i]))) {
        block.push(lines[i]);
        i++;
      }
      const items = block
        .map((l) => l.replace(/^\s+-\s*/, '').trim())
        .filter((l) => l.length > 0);
      if (items.length) {
        fields[key] = items.map(unquote);
      } else {
        fields[key] = block.join('\n').trim();
      }
    } else if (rest.startsWith('-')) {
      // Inline list on the same line (rare in these files).
      const items = rest.split(',').map((s) => unquote(s.replace(/^-\s*/, ''))).filter(Boolean);
      fields[key] = items;
      i++;
    } else {
      fields[key] = unquote(rest);
      i++;
    }
  }
  return fields;
}

function listSkillDirs(dir) {
  // Returns [packageName, skillName, absDirPath] for every folder containing SKILL.md.
  const out = [];
  if (!existsSync(dir)) return out;
  for (const pkg of readdirSync(dir, { withFileTypes: true })) {
    if (!pkg.isDirectory() || IGNORE_DIRS.has(pkg.name)) continue;
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
    if (IGNORE_DIRS.has(e.name) || IGNORE_FILES.has(e.name)) continue;
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
    // The folder name IS the skill name. A frontmatter name that disagrees with
    // the folder would make the catalogue ambiguous (path, id and install
    // target would no longer be derivable), so it is a hard error here instead
    // of a silently inconsistent entry.
    if (fm.name && fm.name !== name) {
      console.error(
        `error: ${dir}/SKILL.md declares name '${fm.name}' but the folder is named '${name}'`
      );
      process.exit(1);
    }
    const rel = `skills/${pkg}/${name}`;
    const paths = walkFiles(dir).map((p) => p.replace(REPO + '/', ''));
    const compat = fm.compatibility;
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
      compatibility: Array.isArray(compat) ? compat : (compat ? [compat] : []),
      description: fm.description || '',
      paths,
    });
  }

  const catalog = {
    schema_version: '1.0.0',
    repository: 'Ottili-ONE/skills',
    packages,
    skills,
  };

  const json = JSON.stringify(catalog, null, 2) + '\n';
  if (check) {
    if (!existsSync(outPath)) {
      console.error('catalog missing:', outPath, '— run: node scripts/gen-catalog.mjs');
      process.exit(1);
    }
    const existing = readFileSync(outPath, 'utf8');
    if (existing === json) {
      console.log(`ok: catalog unchanged (${skills.length} skills, ${Object.keys(packages).length} packages)`);
      return 0;
    }
    // Report WHAT drifted, not only that something did: a reviewer has to be
    // able to tell "a skill was added" from "someone hand-edited the file".
    const before = JSON.parse(existing);
    const beforeById = new Map((before.skills || []).map((s) => [s.id, s]));
    const afterById = new Map(skills.map((s) => [s.id, s]));
    const added = [...afterById.keys()].filter((id) => !beforeById.has(id));
    const removed = [...beforeById.keys()].filter((id) => !afterById.has(id));
    const changed = [...afterById.keys()].filter(
      (id) => beforeById.has(id) && JSON.stringify(beforeById.get(id)) !== JSON.stringify(afterById.get(id))
    );
    console.error('catalog is out of date — it is GENERATED, never hand-edited.');
    console.error('  run: node scripts/gen-catalog.mjs');
    if (added.length) console.error(`  added:   ${added.join(', ')}`);
    if (removed.length) console.error(`  removed: ${removed.join(', ')}`);
    if (changed.length) console.error(`  changed: ${changed.join(', ')}`);
    process.exit(1);
  }

  writeFileSync(outPath, json, 'utf8');
  console.log(`ok: wrote ${outPath} — ${skills.length} skills, ${Object.keys(packages).length} packages`);
  return 0;
}

process.exit(main());
