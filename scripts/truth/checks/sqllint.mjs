// Static SQL lint for PostgreSQL migrations. The authoritative check is applying the migration to a real
// PostgreSQL twice (gate.mjs migrate); this lint catches the invented-SQL patterns found in the Ottili repos
// early and produces precise messages. Zero dependencies.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const RESERVED = new Set(
  `all analyse analyze and any array as asc asymmetric both case cast check collate column constraint create current_catalog
   current_date current_role current_time current_timestamp current_user default deferrable desc distinct do else end except false
   fetch for foreign from grant group having in initially intersect into lateral leading limit localtime localtimestamp not null
   offset on only or order placing primary references returning select session_user some symmetric system_user table then to
   trailing true union unique user using variadic when where window with`.split(/\s+/),
);

/** Blank out comments and string literals (keeping newlines and length) and split into top-level statements. */
export function analyse(text) {
  const n = text.length;
  const out = new Array(n);
  const statements = [];
  const dollarStack = [];
  const badCommentIdx = [];
  let stmtStart = 0;
  let i = 0;
  const blank = (from, to) => {
    for (let k = from; k < to; k += 1) out[k] = text[k] === '\n' ? '\n' : ' ';
  };
  while (i < n) {
    if ((i === 0 || text[i - 1] === '\n') && dollarStack.length === 0) {
      let j = i;
      while (j < n && (text[j] === ' ' || text[j] === '\t')) j += 1;
      const lead2 = text.slice(j, j + 2);
      if (lead2 === '//' || (text[j] === '#' && !/^#(variable_conflict|print_strict_params|plpgsql)/.test(text.slice(j, j + 40)))) {
        let e = j;
        while (e < n && text[e] !== '\n') e += 1;
        badCommentIdx.push({ idx: j, mark: lead2 === '//' ? '//' : '#' });
        blank(i, e);
        i = e;
        continue;
      }
    }
    const c = text[i];
    const next = text[i + 1];
    if (c === '-' && next === '-') {
      let j = i;
      while (j < n && text[j] !== '\n') j += 1;
      blank(i, j);
      i = j;
      continue;
    }
    if (c === '/' && next === '*') {
      let depth = 1;
      let j = i + 2;
      while (j < n && depth > 0) {
        if (text[j] === '/' && text[j + 1] === '*') {
          depth += 1;
          j += 2;
        } else if (text[j] === '*' && text[j + 1] === '/') {
          depth -= 1;
          j += 2;
        } else j += 1;
      }
      blank(i, j);
      i = j;
      continue;
    }
    if (c === "'") {
      let j = i + 1;
      while (j < n) {
        if (text[j] === "'" && text[j + 1] === "'") j += 2;
        else if (text[j] === "'") break;
        else j += 1;
      }
      out[i] = "'";
      blank(i + 1, j);
      if (j < n) out[j] = "'";
      i = j + 1;
      continue;
    }
    if (c === '"') {
      let j = i + 1;
      while (j < n && text[j] !== '"') j += 1;
      for (let k = i; k <= Math.min(j, n - 1); k += 1) out[k] = text[k];
      i = j + 1;
      continue;
    }
    if (c === '$') {
      const m = /^\$([A-Za-z_][A-Za-z0-9_]*)?\$/.exec(text.slice(i, i + 80));
      if (m) {
        const tag = m[1] ?? '';
        const top = dollarStack[dollarStack.length - 1];
        if (top === tag) dollarStack.pop();
        else dollarStack.push(tag);
        for (let k = 0; k < m[0].length; k += 1) out[i + k] = text[i + k];
        i += m[0].length;
        continue;
      }
    }
    out[i] = c;
    if (c === ';' && dollarStack.length === 0) {
      statements.push({ start: stmtStart, end: i + 1 });
      stmtStart = i + 1;
    }
    i += 1;
  }
  if (stmtStart < n) statements.push({ start: stmtStart, end: n });
  const stripped = out.join('');
  const lineStarts = [0];
  for (let k = 0; k < n; k += 1) if (text[k] === '\n') lineStarts.push(k + 1);
  const lineOf = (idx) => {
    let lo = 0;
    let hi = lineStarts.length - 1;
    while (lo < hi) {
      const mid = (lo + hi + 1) >> 1;
      if (lineStarts[mid] <= idx) lo = mid;
      else hi = mid - 1;
    }
    return lo + 1;
  };
  const stmts = statements
    .map((s) => ({ ...s, code: stripped.slice(s.start, s.end), line: lineOf(s.start) }))
    .filter((s) => s.code.trim() !== '' && s.code.trim() !== ';');
  for (const s of stmts) {
    const lead = s.code.search(/\S/);
    s.line = lineOf(s.start + Math.max(0, lead));
    s.flat = s.code.replace(/\s+/g, ' ').trim();
  }
  return { stripped, statements: stmts, lineOf, badComments: badCommentIdx.map((b) => ({ line: lineOf(b.idx), mark: b.mark })) };
}

function splitTopLevel(body) {
  const items = [];
  let depth = 0;
  let cur = '';
  for (const ch of body) {
    if (ch === '(') depth += 1;
    if (ch === ')') depth -= 1;
    if (ch === ',' && depth === 0) {
      items.push(cur);
      cur = '';
    } else cur += ch;
  }
  if (cur.trim()) items.push(cur);
  return items;
}

function bareName(raw) {
  return raw
    .replace(/"/g, '')
    .split('.')
    .pop()
    .toLowerCase();
}

function createTableInfo(stmt) {
  const m = /^CREATE\s+(?:(?:GLOBAL\s+|LOCAL\s+)?(?:TEMP|TEMPORARY)\s+|UNLOGGED\s+)?TABLE\s+(IF\s+NOT\s+EXISTS\s+)?([\w."]+)\s*\(/i.exec(stmt.flat);
  if (!m) return null;
  const openIdx = stmt.code.indexOf('(', stmt.code.toUpperCase().indexOf('TABLE'));
  let depth = 0;
  let end = -1;
  for (let k = openIdx; k < stmt.code.length; k += 1) {
    if (stmt.code[k] === '(') depth += 1;
    if (stmt.code[k] === ')') {
      depth -= 1;
      if (depth === 0) {
        end = k;
        break;
      }
    }
  }
  if (end === -1) return { name: bareName(m[2]), ifNotExists: Boolean(m[1]), columns: [], items: [], broken: true };
  const items = splitTopLevel(stmt.code.slice(openIdx + 1, end)).map((s) => s.replace(/\s+/g, ' ').trim());
  const columns = [];
  for (const item of items) {
    if (/^(CONSTRAINT|PRIMARY|FOREIGN|UNIQUE|CHECK|EXCLUDE|LIKE)\b/i.test(item)) continue;
    const cm = /^("[^"]+"|[A-Za-z_][\w$]*)\s*(.*)$/.exec(item);
    if (cm) columns.push({ raw: cm[1], quoted: cm[1].startsWith('"'), name: cm[1].replace(/"/g, '').toLowerCase(), rest: cm[2], item });
  }
  return { name: bareName(m[2]), ifNotExists: Boolean(m[1]), columns, items };
}

/**
 * @param {string} text
 * @param {{file?: string, sql?: {requireRls?: boolean, requireIdempotent?: boolean, globalTableMarker?: string}}} opts
 * @returns {{severity:'error'|'warn', rule:string, line:number, message:string}[]}
 */
export function lintSql(text, opts = {}) {
  const sqlCfg = { requireRls: true, requireIdempotent: true, globalTableMarker: 'truth:global-table', ...(opts.sql ?? {}) };
  const findings = [];
  const add = (severity, rule, line, message) => findings.push({ severity, rule, line, message });
  const { stripped, statements, badComments } = analyse(text);

  // R003 / R004 / R005: non-SQL comment styles, backticks, escaped dollars
  for (const b of badComments) add('error', 'R003-bad-comment', b.line, `line starts with "${b.mark}": SQL comments must use "--" or /* */`);
  stripped.split('\n').forEach((ln, idx) => {
    if (ln.includes('`')) add('error', 'R004-backtick', idx + 1, 'backtick found: PostgreSQL quotes identifiers with double quotes');
  });
  text.split('\n').forEach((ln, idx) => {
    if (/\\\$/.test(ln)) add('error', 'R005-escaped-dollar', idx + 1, 'backslash before "$": dollar quoting must be written as $$ ... $$ without escapes');
  });

  const policyDrops = new Set();
  const triggerDrops = new Set();
  const constraintDrops = new Set();
  const tables = []; // {name, line, hasCompanyId, rls, force, policy, indexOnCompany}
  const byName = new Map();
  const noteTable = (name) => byName.get(name);

  for (const stmt of statements) {
    const s = stmt.flat;
    const head = s.slice(0, 40).toUpperCase();
    const isDo = /^DO\b/i.test(s);

    // R001: constructs PostgreSQL does not have
    if (/\bCREATE\s+POLICY\s+IF\s+NOT\s+EXISTS\b/i.test(s)) add('error', 'R001-policy-if-not-exists', stmt.line, 'CREATE POLICY IF NOT EXISTS does not exist: use DROP POLICY IF EXISTS <name> ON <table>; CREATE POLICY ...');
    if (/\bADD\s+CONSTRAINT\s+IF\s+NOT\s+EXISTS\b/i.test(s)) add('error', 'R001-constraint-if-not-exists', stmt.line, 'ADD CONSTRAINT IF NOT EXISTS does not exist: guard with DROP CONSTRAINT IF EXISTS or a DO block that checks pg_constraint');
    const ine = /\bCREATE\s+(?:OR\s+REPLACE\s+)?(TRIGGER|TYPE|DOMAIN|VIEW|FUNCTION|PROCEDURE|ROLE|DATABASE|POLICY)\s+IF\s+NOT\s+EXISTS\b/i.exec(s);
    if (ine) add('error', 'R001-if-not-exists-unsupported', stmt.line, `CREATE ${ine[1].toUpperCase()} IF NOT EXISTS is not valid PostgreSQL`);
    if (/\bUNIQUE\s*\([^)]*\)\s*WHERE\b/i.test(s) && !/^CREATE\s+(UNIQUE\s+)?INDEX\b/i.test(s)) add('error', 'R002-unique-where', stmt.line, 'a partial unique rule is not a table constraint: use CREATE UNIQUE INDEX ... WHERE ...');

    // R006: dialect leaks
    const dialect = [
      [/\bAUTOINCREMENT\b/i, 'AUTOINCREMENT (SQLite)'],
      [/\bAUTO_INCREMENT\b/i, 'AUTO_INCREMENT (MySQL)'],
      [/\bPRAGMA\b/i, 'PRAGMA (SQLite)'],
      [/\bdatetime\s*\(/i, "datetime(...) (SQLite): use now() or CURRENT_TIMESTAMP with timestamptz"],
      [/\bstrftime\s*\(/i, 'strftime(...) (SQLite)'],
      [/\bINSERT\s+OR\s+(REPLACE|IGNORE)\b/i, 'INSERT OR REPLACE/IGNORE (SQLite): use ON CONFLICT'],
      [/\bWITHOUT\s+ROWID\b/i, 'WITHOUT ROWID (SQLite)'],
      [/\bENGINE\s*=/i, 'ENGINE= (MySQL)'],
      [/\bON\s+DUPLICATE\s+KEY\b/i, 'ON DUPLICATE KEY (MySQL): use ON CONFLICT'],
      [/\bIFNULL\s*\(/i, 'IFNULL (use COALESCE)'],
      [/\b(TINYINT|MEDIUMINT|UNSIGNED)\b/i, 'MySQL integer type'],
      [/(?<![\w.])DATETIME(?![\w(])/i, 'DATETIME type: use timestamptz'],
      [/\bBLOB\b/i, 'BLOB type: use bytea'],
    ];
    for (const [re, msg] of dialect) if (re.test(s)) add('error', 'R006-dialect', stmt.line, `non-PostgreSQL construct: ${msg}`);

    // R009 idempotency / R010 RLS bookkeeping
    const dropPolicy = /^DROP\s+POLICY\s+IF\s+EXISTS\s+("?[\w$]+"?)\s+ON\s+([\w."]+)/i.exec(s);
    if (dropPolicy) policyDrops.add(`${dropPolicy[1].replace(/"/g, '').toLowerCase()}@${bareName(dropPolicy[2])}`);
    const dropTrigger = /^DROP\s+TRIGGER\s+IF\s+EXISTS\s+("?[\w$]+"?)\s+ON\s+([\w."]+)/i.exec(s);
    if (dropTrigger) triggerDrops.add(`${dropTrigger[1].replace(/"/g, '').toLowerCase()}@${bareName(dropTrigger[2])}`);
    const dropConstraint = /\bALTER\s+TABLE\s+(?:IF\s+EXISTS\s+)?(?:ONLY\s+)?([\w."]+)\s+DROP\s+CONSTRAINT\s+IF\s+EXISTS\s+("?[\w$]+"?)/i.exec(s);
    if (dropConstraint) constraintDrops.add(`${dropConstraint[2].replace(/"/g, '').toLowerCase()}@${bareName(dropConstraint[1])}`);

    if (sqlCfg.requireIdempotent && !isDo) {
      if (/^CREATE\s+(?:(?:GLOBAL\s+|LOCAL\s+)?(?:TEMP|TEMPORARY)\s+|UNLOGGED\s+)?TABLE\s+(?!IF\s+NOT\s+EXISTS)/i.test(s)) add('error', 'R009-create-table', stmt.line, 'CREATE TABLE must be CREATE TABLE IF NOT EXISTS');
      if (/^CREATE\s+(UNIQUE\s+)?INDEX\s+(?!IF\s+NOT\s+EXISTS)(?!CONCURRENTLY\s+IF\s+NOT\s+EXISTS)/i.test(s) && !/^CREATE\s+(UNIQUE\s+)?INDEX\s+CONCURRENTLY\s+IF\s+NOT\s+EXISTS/i.test(s)) add('error', 'R009-create-index', stmt.line, 'CREATE INDEX must be CREATE INDEX IF NOT EXISTS');
      if (/^CREATE\s+(SEQUENCE|SCHEMA)\s+(?!IF\s+NOT\s+EXISTS)/i.test(s)) add('error', 'R009-create-object', stmt.line, 'CREATE SEQUENCE/SCHEMA must use IF NOT EXISTS');
      if (/^CREATE\s+(FUNCTION|PROCEDURE|VIEW)\b/i.test(s)) add('error', 'R009-create-or-replace', stmt.line, 'use CREATE OR REPLACE FUNCTION/PROCEDURE/VIEW');
      if (/^CREATE\s+TYPE\b/i.test(s)) add('error', 'R009-create-type', stmt.line, 'wrap CREATE TYPE in a DO block that checks pg_type (or use a lookup table / CHECK constraint)');
      if (/^CREATE\s+TRIGGER\b/i.test(s)) {
        const m = /^CREATE\s+TRIGGER\s+("?[\w$]+"?)\s+.*?\bON\s+([\w."]+)/i.exec(s);
        if (!m || !triggerDrops.has(`${m[1].replace(/"/g, '').toLowerCase()}@${bareName(m[2])}`))
          add('error', 'R009-create-trigger', stmt.line, 'precede CREATE TRIGGER with DROP TRIGGER IF EXISTS <name> ON <table> (or use CREATE OR REPLACE TRIGGER)');
      }
      if (/^CREATE\s+POLICY\b/i.test(s)) {
        const m = /^CREATE\s+POLICY\s+("?[\w$]+"?)\s+ON\s+([\w."]+)/i.exec(s);
        if (!m || !policyDrops.has(`${m[1].replace(/"/g, '').toLowerCase()}@${bareName(m[2])}`))
          add('error', 'R009-create-policy', stmt.line, 'precede CREATE POLICY with DROP POLICY IF EXISTS <name> ON <table>; in the same file');
      }
      if (/\bALTER\s+TABLE\b/i.test(s) && /\bADD\s+CONSTRAINT\b/i.test(s)) {
        const names = [...s.matchAll(/\bADD\s+CONSTRAINT\s+(?!IF\s+NOT\s+EXISTS)("?[\w$]+"?)/gi)].map((m) => m[1].replace(/"/g, '').toLowerCase());
        const tm = /\bALTER\s+TABLE\s+(?:IF\s+EXISTS\s+)?(?:ONLY\s+)?([\w."]+)/i.exec(s);
        const tbl = tm ? bareName(tm[1]) : '';
        for (const nm of names) if (!constraintDrops.has(`${nm}@${tbl}`)) add('error', 'R009-add-constraint', stmt.line, `ADD CONSTRAINT ${nm} is not repeatable: drop it first with DROP CONSTRAINT IF EXISTS ${nm} in the same file or guard it in a DO block`);
      }
      if (/\bALTER\s+TABLE\b/i.test(s)) {
        for (const m of s.matchAll(/\bADD\s+COLUMN\s+(?!IF\s+NOT\s+EXISTS)/gi)) add('error', 'R009-add-column', stmt.line, `ADD COLUMN must be ADD COLUMN IF NOT EXISTS (at offset ${m.index})`);
      }
      if (/^DROP\s+(TABLE|INDEX|VIEW|SCHEMA|TYPE|FUNCTION)\s+(?!IF\s+EXISTS)/i.test(s)) add('error', 'R009-drop', stmt.line, 'DROP must use IF EXISTS');
    }
    if (/^DROP\s+(TABLE|SCHEMA)\b/i.test(s) || /\bDROP\s+COLUMN\b/i.test(s)) {
      if (!/truth:allow-destructive/.test(text)) add('warn', 'R015-destructive', stmt.line, 'destructive DDL in a migration: migrations are append-only; add "-- truth:allow-destructive <reason>" if this is a deliberate pre-release re-baseline');
    }

    // CREATE TABLE structure
    const info = createTableInfo(stmt);
    if (info) {
      if (info.broken) add('error', 'R016-unbalanced', stmt.line, `CREATE TABLE ${info.name}: unbalanced parentheses`);
      const record = { name: info.name, line: stmt.line, hasCompanyId: false, rls: false, force: false, policy: false, companyIndex: false };
      tables.push(record);
      byName.set(info.name, record);
      for (const col of info.columns) {
        if (col.name === 'company_id') record.hasCompanyId = true;
        if (!col.quoted && RESERVED.has(col.name)) add('error', 'R008-reserved-identifier', stmt.line, `column "${col.name}" is a reserved word in PostgreSQL: rename it (e.g. page_offset, row_limit) or quote it`);
        if (/^(text|varchar|character\s+varying|char)\b/i.test(col.rest) && /\bDEFAULT\s+(CURRENT_TIMESTAMP|now\s*\(\))/i.test(col.rest)) add('error', 'R007-text-timestamp', stmt.line, `column ${col.name}: text column with a timestamp default; use timestamptz`);
        if (/^timestamp(?!\s*tz)(?!\s+with\s+time\s+zone)\b/i.test(col.rest) && !/^timestamptz/i.test(col.rest)) add('warn', 'R011-timestamp-without-tz', stmt.line, `column ${col.name}: use timestamptz instead of timestamp`);
      }
      for (const item of info.items) if (/^(PRIMARY\s+KEY|UNIQUE)\s*\(\s*company_id\b/i.test(item) || /\bCONSTRAINT\s+\S+\s+(PRIMARY\s+KEY|UNIQUE)\s*\(\s*company_id\b/i.test(item)) record.companyIndex = true;
      if (info.columns.some((c) => c.name === 'company_id' && /PRIMARY\s+KEY/i.test(c.rest))) record.companyIndex = true;
    }
    const rls = /^ALTER\s+TABLE\s+(?:IF\s+EXISTS\s+)?(?:ONLY\s+)?([\w."]+)\s+(ENABLE|FORCE)\s+ROW\s+LEVEL\s+SECURITY/i.exec(s);
    if (rls) {
      const t = noteTable(bareName(rls[1]));
      if (t) {
        if (rls[2].toUpperCase() === 'ENABLE') t.rls = true;
        else t.force = true;
      }
    }
    const pol = /^CREATE\s+POLICY\s+"?[\w$]+"?\s+ON\s+([\w."]+)/i.exec(s);
    if (pol) {
      const t = noteTable(bareName(pol[1]));
      if (t) t.policy = true;
    }
    const idx = /^CREATE\s+(?:UNIQUE\s+)?INDEX\s+(?:CONCURRENTLY\s+)?(?:IF\s+NOT\s+EXISTS\s+)?[\w."]+\s+ON\s+(?:ONLY\s+)?([\w."]+)(?:\s+USING\s+\w+)?\s*\(\s*"?company_id"?/i.exec(s);
    if (idx) {
      const t = noteTable(bareName(idx[1]));
      if (t) t.companyIndex = true;
    }
  }

  const markerSeen = text.includes(sqlCfg.globalTableMarker);
  for (const t of tables) {
    if (sqlCfg.requireRls) {
      if (t.hasCompanyId) {
        if (!t.rls) add('error', 'R010-rls-enable', t.line, `table ${t.name}: add ALTER TABLE ${t.name} ENABLE ROW LEVEL SECURITY`);
        if (!t.force) add('error', 'R010-rls-force', t.line, `table ${t.name}: add ALTER TABLE ${t.name} FORCE ROW LEVEL SECURITY (the owner role must not bypass tenant isolation)`);
        if (!t.policy) add('error', 'R010-rls-policy', t.line, `table ${t.name}: add a tenant policy USING (company_id = current_setting('app.company_id')::uuid)`);
      } else if (!markerSeen) {
        add('error', 'R010-no-company-id', t.line, `table ${t.name} has no company_id column: add company_id uuid NOT NULL or mark the file with "-- ${sqlCfg.globalTableMarker} <reason>" for a deliberately global table`);
      }
    }
    if (t.hasCompanyId && !t.companyIndex) add('warn', 'R012-company-index', t.line, `table ${t.name}: no index/constraint starting with company_id found in this file`);
  }
  if (!/\S/.test(stripped)) add('error', 'R017-empty', 1, 'migration file contains no SQL statements');
  return findings.sort((a, b) => a.line - b.line);
}

export function tablesCreated(text) {
  const { statements } = analyse(text);
  return statements
    .map((st) => createTableInfo(st))
    .filter(Boolean)
    .map((info) => ({ name: info.name, hasCompanyId: info.columns.some((c) => c.name === 'company_id') }));
}

export function lintFile(file, opts = {}) {
  return lintSql(fs.readFileSync(file, 'utf8'), { ...opts, file });
}

const isMain = process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url);
if (isMain) {
  const files = process.argv.slice(2);
  let errors = 0;
  for (const f of files) {
    for (const fd of lintFile(f)) {
      if (fd.severity === 'error') errors += 1;
      process.stdout.write(`${f}:${fd.line}: ${fd.severity} ${fd.rule}: ${fd.message}\n`);
    }
  }
  process.exit(errors ? 1 : 0);
}
