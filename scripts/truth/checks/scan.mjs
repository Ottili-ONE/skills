// Source scans used by gate.mjs: language, stubs, secrets, size, i18n. Zero dependencies.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { makeMatcher } from '../lib/common.mjs';

const TEXT_EXT = new Set(['.mjs', '.js', '.cjs', '.ts', '.tsx', '.jsx', '.json', '.sql', '.md', '.py', '.sh', '.yml', '.yaml', '.css', '.html', '.txt', '.toml']);
const CODE_EXT = new Set(['.mjs', '.js', '.cjs', '.ts', '.tsx', '.jsx', '.py', '.sh']);
const UI_EXT = new Set(['.jsx', '.tsx', '.html']);

export const isText = (p) => TEXT_EXT.has(path.extname(p).toLowerCase());
export const isCode = (p) => CODE_EXT.has(path.extname(p).toLowerCase());
const isTestPath = (p) => /(^|\/)(tests?|__tests__|e2e|fixtures?|__fixtures__)(\/|$)|\.(test|spec)\.[a-z]+$/i.test(p);
const isCatalog = (p) => /(^|\/)(i18n|locales?|messages)\//i.test(p) || /(^|\/)(de|en)\.json$/i.test(p) || /\.(de|en)\.json$/i.test(p);

// ---------- language ----------
const STRONG = new Set(
  `und oder nicht wird werden wurde wurden für über mit von nach zum zur dass auch bitte wenn dann noch nur sind eine einen einer einem
   keine kein dem des ist haben kann können muss müssen soll sollen wir aus durch gegen ohne zwischen bereits jedoch sowie damit weil
   alle jede jeder jedes neue neuen vor beim aber hier diese dieser dieses diesen wieder immer keinen sich`.split(/\s+/),
);
const DOMAIN = new Set(
  `rechnung rechnungen rechnungs kunde kunden lieferant lieferanten angebot angebote auftrag auftraege auftrage bestellung bestellungen
   lieferschein mahnung mahnungen buchung buchungen stammdaten zahlung zahlungen betrag betraege benutzer passwort einstellungen
   bericht berichte aufgabe aufgaben ansicht verwaltung druckfunktion speichern abbrechen loeschen bearbeiten suchen uebersicht
   unternehmen firma mandant mandanten mitarbeiter kostenstelle kostenstellen konto konten beleg belege steuer umsatzsteuer
   mehrwertsteuer lager bestand artikel preis preise menge einheit vorlage vorlagen ordner datei dateien fehler warnung hinweis
   erfolg senden empfaenger absender betreff nachricht nachrichten freigabe genehmigung antrag antraege urlaub lohn gehalt
   buchhaltung jahresabschluss bilanz kassenbuch rechnungsdatenservice lieferung versand zahlungsziel skonto gutschrift
   abrechnung ausgang eingang erledigt offen gesperrt gueltig ungueltig pflicht pflichtfeld anrede vorname nachname strasse
   plz ort land telefon kundennummer rechnungsnummer`.split(/\s+/),
);

function tokensOfIdentifier(s) {
  return s
    .replace(/([a-z0-9])([A-Z])/g, '$1 $2')
    .split(/[^A-Za-z0-9äöüÄÖÜß]+/)
    .map((t) => t.toLowerCase())
    .filter(Boolean);
}

export function scanLanguageText(rel, text, cfg = {}) {
  const findings = [];
  const allow = makeMatcher(cfg.language?.allowGlobs);
  if (allow(rel) || isCatalog(rel)) return findings;
  const head = text.split('\n', 5).join('\n');
  if (head.includes('truth:allow-german-file')) return findings;
  for (const tok of tokensOfIdentifier(rel)) {
    if (DOMAIN.has(tok)) findings.push({ severity: 'error', rule: 'language-filename', path: rel, line: 0, message: `German word "${tok}" in the file path: use English names` });
  }
  const lines = text.split('\n');
  lines.forEach((line, idx) => {
    if (line.includes('truth:allow-german')) return;
    if (/[äöüÄÖÜß]/.test(line)) {
      findings.push({ severity: 'error', rule: 'language-umlaut', path: rel, line: idx + 1, message: `non-English character in "${line.trim().slice(0, 90)}": code, comments, identifiers and docs must be English (user-facing German lives in i18n catalogues)` });
      return;
    }
    const words = line.split(/[^A-Za-z]+/).filter(Boolean);
    const strong = new Set(words.filter((w) => STRONG.has(w)));
    const domain = new Set();
    for (const w of words) for (const t of tokensOfIdentifier(w)) if (DOMAIN.has(t)) domain.add(t);
    if (strong.size >= 2) findings.push({ severity: 'error', rule: 'language-words', path: rel, line: idx + 1, message: `German text detected (${[...strong].slice(0, 4).join(', ')}): "${line.trim().slice(0, 90)}"` });
    else if (domain.size >= 1 && !/^\s*(import|export\s+\*)\b.*['"]@ottili\//.test(line)) findings.push({ severity: 'error', rule: 'language-identifier', path: rel, line: idx + 1, message: `German domain word (${[...domain].slice(0, 3).join(', ')}) in "${line.trim().slice(0, 90)}": use the English term` });
  });
  return dedupePerFile(findings, 25);
}

function dedupePerFile(findings, cap) {
  if (findings.length <= cap) return findings;
  const head = findings.slice(0, cap);
  head.push({ ...findings[cap], line: findings[cap].line, message: `... ${findings.length - cap} more findings of this kind in the file (first ${cap} shown)` });
  return head;
}

// ---------- stubs ----------
export function scanStubsText(rel, text, cfg = {}) {
  const findings = [];
  const allow = makeMatcher(cfg.stubs?.allowGlobs);
  if (allow(rel)) return findings;
  const test = isTestPath(rel);
  const lines = text.split('\n');
  const add = (severity, rule, line, message) => findings.push({ severity, rule, path: rel, line, message });
  lines.forEach((line, idx) => {
    const n = idx + 1;
    if (line.includes('truth:allow-stub')) return;
    if (/\b(TODO|FIXME|HACK|XXX)\b/.test(line)) add('error', 'stub-marker', n, 'TODO/FIXME/HACK/XXX: finish it or record the gap in docs/gaps/<JOB-ID>.md');
    if (/\bSTUB[-_\w]*\b/.test(line)) add('error', 'stub-marker', n, 'STUB marker: replace the stub with a working implementation');
    if (/not[ _-]?implemented|unimplemented/i.test(line) && !/^\s*(\/\/|\*|#)/.test(line)) add('error', 'stub-not-implemented', n, 'not-implemented path: implement it or remove the unreachable surface');
    if (/lorem ipsum/i.test(line)) add('error', 'stub-lorem', n, 'lorem ipsum text');
    if (!test) {
      if (/\b(status|statusCode|reply\.code|res\.status|writeHead)\b[^;\n]*\b501\b/.test(line) || /\b501\b[^;\n]*\bNot Implemented\b/i.test(line)) add('error', 'stub-501', n, 'HTTP 501 response: a declared route must work');
      if (/\b(fake|dummy|simulat(?:e|ed|ion)|hard-?coded)\b/i.test(line) && !/^\s*(\/\/|\*)\s*(see|note)/i.test(line)) add('warn', 'stub-fake', n, 'fake/dummy/simulated/hard-coded wording in production code: verify this is not a facade');
      if (/catch\s*(\([^)]*\))?\s*\{\s*\}/.test(line)) add('warn', 'swallowed-error', n, 'empty catch block swallows errors');
      if (/\bconsole\.(log|debug)\(/.test(line) && !/scripts\//.test(rel)) add('warn', 'console-log', n, 'console.log in service code: use the structured logger');
    } else {
      if (/\b(it|test|describe)\.(skip|todo)\b|\bxit\(|\bxdescribe\(|\bt\.skip\(|\{\s*skip\s*:\s*(true|['"`])/.test(line)) add('error', 'test-skipped', n, 'skipped/todo test: delete it or make it pass');
      if (/:memory:|better-sqlite3|node:sqlite|sqlite3|pg-mem|mockPool|jest\.mock\(['"]pg['"]\)|vi\.mock\(['"]pg['"]\)/.test(line)) add('error', 'test-fake-db', n, 'tests must run against real PostgreSQL (scripts/truth/db.mjs), not SQLite/in-memory/mocked pg');
    }
  });
  return dedupePerFile(findings, 25);
}

// ---------- secrets ----------
const SECRET_PATTERNS = [
  [/-----BEGIN (?:RSA |EC |OPENSSH |DSA |ENCRYPTED )?PRIVATE KEY-----/, 'private key'],
  [/\bAKIA[0-9A-Z]{16}\b/, 'AWS access key id'],
  [/\bghp_[A-Za-z0-9]{30,}\b/, 'GitHub token'],
  [/\bxox[baprs]-[A-Za-z0-9-]{10,}/, 'Slack token'],
  [/\bsk_live_[A-Za-z0-9]{10,}/, 'Stripe live key'],
  [/\bAIza[0-9A-Za-z_-]{35}\b/, 'Google API key'],
  [/\beyJ[A-Za-z0-9_-]{15,}\.[A-Za-z0-9_-]{15,}\.[A-Za-z0-9_-]{10,}\b/, 'JWT'],
  [/\b(?:password|passwd|secret|api[_-]?key|token)\s*[:=]\s*['"][^'"\s]{10,}['"]/i, 'hard-coded credential'],
];

export function scanSecretsText(rel, text, cfg = {}) {
  const findings = [];
  if (makeMatcher(cfg.secrets?.allowGlobs)(rel)) return findings;
  text.split('\n').forEach((line, idx) => {
    if (line.includes('truth:allow-secret')) return;
    for (const [re, label] of SECRET_PATTERNS) {
      if (re.test(line)) {
        if (label === 'hard-coded credential' && /(example|changeme|placeholder|process\.env|\$\{|<[^>]+>|xxxx|\*{4})/i.test(line)) continue;
        findings.push({ severity: 'error', rule: 'secret', path: rel, line: idx + 1, message: `possible ${label} committed (value redacted): use the secrets manager / generate test keys at test time` });
      }
    }
  });
  return findings;
}

// ---------- size ----------
export function scanSizeText(rel, text, cfg = {}) {
  const findings = [];
  const ext = path.extname(rel).toLowerCase();
  if (makeMatcher([...(cfg.generatedGlobs ?? []), ...(cfg.size?.allowGlobs ?? [])])(rel)) return findings;
  if (ext === '.json' || ext === '.md' || ext === '.txt' || ext === '.yml' || ext === '.yaml' || isCatalog(rel)) return findings;
  const lines = text.split('\n').length;
  const limit = ext === '.sql' ? cfg.maxSqlLines : isTestPath(rel) ? cfg.maxTestLines : cfg.maxFileLines;
  if (lines > limit) findings.push({ severity: 'error', rule: 'file-size', path: rel, line: 0, message: `${lines} lines (limit ${limit}): split the file by responsibility` });
  else if (lines > Math.floor(limit * 0.85)) findings.push({ severity: 'warn', rule: 'file-size', path: rel, line: 0, message: `${lines} lines is close to the ${limit} line limit` });
  return findings;
}

// ---------- i18n ----------
function flatten(obj, prefix = '', out = {}) {
  for (const [k, v] of Object.entries(obj ?? {})) {
    const key = prefix ? `${prefix}.${k}` : k;
    if (v && typeof v === 'object' && !Array.isArray(v)) flatten(v, key, out);
    else out[key] = v;
  }
  return out;
}

export function scanI18n(root, files, cfg) {
  const findings = [];
  const add = (severity, rule, rel, line, message) => findings.push({ severity, rule, path: rel, line, message });
  const catalogs = files.filter((f) => f.path.endsWith('.json') && isCatalog(f.path));
  const groups = new Map();
  for (const f of catalogs) {
    const dir = path.posix.dirname(f.path);
    const base = path.posix.basename(f.path);
    let locale = null;
    let stem = '';
    const m1 = /^([a-z]{2})(?:[-_][A-Za-z]{2})?\.json$/.exec(base);
    const m2 = /^(.+)\.([a-z]{2})(?:[-_][A-Za-z]{2})?\.json$/.exec(base);
    if (m1) {
      locale = m1[1];
      stem = '';
    } else if (m2) {
      locale = m2[2];
      stem = m2[1];
    } else continue;
    const key = `${dir}::${stem}`;
    if (!groups.has(key)) groups.set(key, {});
    groups.get(key)[locale] = f;
  }
  const locales = cfg.locales ?? ['de', 'en'];
  for (const [key, group] of groups) {
    const present = locales.filter((l) => group[l]);
    if (present.length === 0) continue;
    if (present.length !== locales.length) {
      const anyFile = Object.values(group)[0];
      add('error', 'i18n-missing-locale', anyFile.path, 0, `catalogue ${key.replace('::', '/')} lacks locale(s): ${locales.filter((l) => !group[l]).join(', ')}`);
      continue;
    }
    const flat = {};
    for (const l of locales) {
      try {
        flat[l] = flatten(JSON.parse(group[l].text));
      } catch (err) {
        add('error', 'i18n-invalid-json', group[l].path, 0, `invalid JSON: ${err.message}`);
      }
    }
    if (locales.some((l) => !flat[l])) continue;
    const base = flat[locales[0]];
    for (const l of locales.slice(1)) {
      for (const k of Object.keys(base)) if (!(k in flat[l])) add('error', 'i18n-parity', group[l].path, 0, `key "${k}" exists in ${locales[0]} but is missing in ${l}`);
      for (const k of Object.keys(flat[l])) if (!(k in base)) add('error', 'i18n-parity', group[locales[0]].path, 0, `key "${k}" exists in ${l} but is missing in ${locales[0]}`);
    }
    for (const l of locales)
      for (const [k, v] of Object.entries(flat[l])) if (typeof v === 'string' && v.trim() === '') add('error', 'i18n-empty', group[l].path, 0, `empty translation for "${k}" (${l})`);
    const en = flat.en ?? {};
    for (const [k, v] of Object.entries(en)) if (typeof v === 'string' && /[äöüß]/i.test(v)) add('error', 'i18n-wrong-language', group.en.path, 0, `English catalogue value for "${k}" contains German characters`);
  }
  // hard-coded literals in UI sources
  const attr = /\b(title|label|placeholder|aria-label|alt|tooltip|description|helperText|errorText|emptyText|heading|caption)=("([^"{}]*[A-Za-z]{3}[^"{}]*)"|'([^'{}]*[A-Za-z]{3}[^'{}]*)')/;
  const sameLineText = /<[A-Za-z][^<>]*>([^<>{}\n]*[A-Za-z]{3}[^<>{}\n]*)<\//;
  const toast = /\b(toast|notify|alert|showError|showMessage|showSuccess)\(\s*['"`][A-Za-z]/;
  for (const f of files) {
    if (!UI_EXT.has(path.extname(f.path).toLowerCase()) || isTestPath(f.path)) continue;
    f.text.split('\n').forEach((line, idx) => {
      if (line.includes('truth:allow-literal')) return;
      const a = attr.exec(line);
      if (a) {
        const v = a[3] ?? a[4];
        if (!/^[\w.-]+$/.test(v) || /\s/.test(v)) add('error', 'i18n-hardcoded', f.path, idx + 1, `hard-coded UI text in attribute ${a[1]}="${v.slice(0, 40)}": use the i18n catalogue`);
      }
      const t = sameLineText.exec(line);
      if (t && !/^\s*(\/\/|\*)/.test(line) && /[A-Za-z]{3}/.test(t[1]) && !/^[\s\d.,:;|/-]+$/.test(t[1])) add('error', 'i18n-hardcoded', f.path, idx + 1, `hard-coded UI text "${t[1].trim().slice(0, 40)}": use the i18n catalogue`);
      if (toast.test(line)) add('error', 'i18n-hardcoded', f.path, idx + 1, 'hard-coded message text passed to a notifier: use a catalogue key');
    });
  }
  // keys used but not defined anywhere (best effort)
  const all = new Set();
  const allCatalogs = (cfg._allCatalogs ?? []);
  for (const c of allCatalogs) {
    try {
      for (const k of Object.keys(flatten(JSON.parse(c.text)))) all.add(k);
    } catch {
      // reported elsewhere
    }
  }
  if (all.size > 0) {
    const call = new RegExp(cfg.i18n?.callPattern ?? "\\bt\\(\\s*['\"]([\\w.-]+)['\"]", 'g');
    for (const f of files) {
      if (!isCode(f.path) && !UI_EXT.has(path.extname(f.path).toLowerCase())) continue;
      if (isTestPath(f.path) || isCatalog(f.path)) continue;
      for (const m of f.text.matchAll(call)) {
        const k = m[1];
        if (!all.has(k) && !k.endsWith('.')) add('error', 'i18n-missing-key', f.path, f.text.slice(0, m.index).split('\n').length, `translation key "${k}" is not defined in any catalogue`);
      }
    }
  }
  return findings;
}

// ---------- CLI ----------
export function readFiles(root, rels) {
  const out = [];
  for (const rel of rels) {
    if (!isText(rel)) continue;
    const abs = path.join(root, rel);
    try {
      const st = fs.statSync(abs);
      if (!st.isFile() || st.size > 4 * 1024 * 1024) continue;
      out.push({ path: rel, text: fs.readFileSync(abs, 'utf8') });
    } catch {
      // file vanished
    }
  }
  return out;
}

export function runScan(kind, root, rels, cfg) {
  const files = readFiles(root, rels);
  const findings = [];
  for (const f of files) {
    if (kind === 'language') findings.push(...scanLanguageText(f.path, f.text, cfg));
    else if (kind === 'stubs' && isCode(f.path)) findings.push(...scanStubsText(f.path, f.text, cfg));
    else if (kind === 'secrets') findings.push(...scanSecretsText(f.path, f.text, cfg));
    else if (kind === 'size') findings.push(...scanSizeText(f.path, f.text, cfg));
  }
  if (kind === 'i18n') findings.push(...scanI18n(root, files, cfg));
  return findings;
}

const isMain = process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url);
if (isMain) {
  const { loadConfig, repoRoot, listFiles, parseArgs, csv } = await import('../lib/common.mjs');
  const args = parseArgs(process.argv.slice(2));
  const kind = args._[0];
  const root = repoRoot();
  const cfg = loadConfig(root);
  const rels = args.paths ? csv(args.paths).flatMap((p) => listFiles(root).filter(makeMatcher([p]))) : listFiles(root);
  const findings = runScan(kind, root, rels, cfg);
  for (const f of findings) process.stdout.write(`${f.path}:${f.line}: ${f.severity} ${f.rule}: ${f.message}\n`);
  process.exit(findings.some((f) => f.severity === 'error') ? 1 : 0);
}
