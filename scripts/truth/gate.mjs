#!/usr/bin/env node
// The gate is the ONLY definition of "done". Results are written OUTSIDE the repository (TRUTH_RESULTS_DIR) and are bound to the
// exact content of the owned paths, so safe-commit.mjs can refuse to land anything the gate did not see.
//
//   node scripts/truth/gate.mjs job --job ID --owned "dir/**,file.mjs" [--exclude "glob"] [--ui] [--db] [--tests "paths"] [--e2e "paths"]
//                                    [--stamp-block START-END] [--full] [--skip step,step] [--keep-db]
//   node scripts/truth/gate.mjs trunk [--skip step,step] [--strict]
//   node scripts/truth/gate.mjs show --job ID
//
// Steps of a job gate: ownership, shrink, syntax, sql, language, stubs, secrets, size, i18n, lint, typecheck, registry, migrate,
// tests, e2e. A step that is not applicable is skipped, never silently passed: the result lists every step with its status.
import fs from 'node:fs';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { lintSql, tablesCreated } from './checks/sqllint.mjs';
import { isCode, isText, readFiles, scanI18n, scanLanguageText, scanSecretsText, scanSizeText, scanStubsText } from './checks/scan.mjs';
import { createJobDatabase, dropJobDatabase, grantApp } from './db.mjs';
import { allocatePort } from './port.mjs';
import { isBinary, lineCount, syntaxProblem } from './lib/files.mjs';
import {
  EXIT, KIT_DIR, KIT_VERSION, changedFiles, csv, formatDuration, git, gitOut, listFiles, loadConfig, makeMatcher, mergeBase, nowIso, ownedContentHash, parseArgs, readJson, repoName,
  repoRoot, requireFromRepo, resultsDir, sleep, tail, writeJson,
} from './lib/common.mjs';

const argv = process.argv.slice(2);
const sub = argv[0];
const args = parseArgs(argv.slice(1), { flags: ['ui', 'db', 'full', 'keep-db', 'strict'] });
const root = repoRoot();
const cfg = loadConfig(root);
const dir = resultsDir(root, cfg);
const skip = new Set(csv(args.skip));
const steps = [];
let jobId = args.job ?? (sub === 'trunk' ? `TRUNK-${(cfg.repoCode || repoName(root, cfg)).toUpperCase()}` : null);

const shq = (s) => `'${String(s).replace(/'/g, `'\\''`)}'`;
const isE2eFile = (p) => /(^|\/)e2e\//.test(p) || /\.spec\.[mc]?[jt]sx?$/.test(p);
const isTestFile = (p) => /\.(test|spec)\.[mc]?[jt]sx?$/.test(p) || /(^|\/)test_[^/]*\.py$/.test(p) || /_test\.py$/.test(p);

async function step(id, fn) {
  if (skip.has(id)) {
    steps.push({ id, status: 'skip', durationMs: 0, details: ['skipped by --skip'] });
    return;
  }
  const t0 = Date.now();
  let r;
  try {
    r = await fn();
  } catch (err) {
    r = { status: 'fail', details: [`step crashed: ${err.stack || err.message}`] };
  }
  const entry = { id, status: r.status, durationMs: Date.now() - t0, details: (r.details ?? []).slice(0, 60), ...(r.log ? { log: r.log } : {}) };
  steps.push(entry);
  const mark = { pass: 'PASS', fail: 'FAIL', skip: 'skip', warn: 'warn', waived: 'WAIV' }[r.status] ?? r.status;
  process.stdout.write(`${mark.padEnd(5)} ${id.padEnd(11)} ${formatDuration(entry.durationMs).padStart(8)}  ${(entry.details[0] ?? '').slice(0, 150)}\n`);
  for (const d of entry.details.slice(1, r.status === 'fail' ? 12 : 3)) process.stdout.write(`${' '.repeat(28)}${d.slice(0, 170)}\n`);
}

function runCommand(label, command, { env = {}, heavy = 'build', timeoutMs = 45 * 60 * 1000 } = {}) {
  const log = path.join(dir, `${jobId}.${label}.log`);
  const heavySh = path.join(KIT_DIR, 'heavy.sh');
  const wrapped = heavy ? `${shq(heavySh)} --class ${heavy} --label ${shq(`${jobId}:${label}`)} -- bash -c ${shq(command)}` : command;
  const t0 = Date.now();
  const r = spawnSync('bash', ['-c', wrapped], { cwd: root, env: { ...process.env, TRUTH_JOB: jobId, TRUTH_RESULTS_DIR: path.dirname(dir), ...env }, encoding: 'utf8', maxBuffer: 1024 * 1024 * 1024, timeout: timeoutMs });
  const out = `${r.stdout ?? ''}${r.stderr ? `\n--- stderr ---\n${r.stderr}` : ''}`;
  fs.writeFileSync(log, `$ ${command}\n${out}\n[exit ${r.status ?? r.signal} after ${Date.now() - t0}ms]\n`);
  return { code: r.status ?? (r.signal ? 124 : 1), tail: tail(out, 30), log, timedOut: r.signal === 'SIGTERM' };
}

function expand(template, vars) {
  return template.replace(/\{(\w+)\}/g, (_, k) => (k in vars ? vars[k] : `{${k}}`));
}

function dbEnv(u, port) {
  const vars = { migratorUrl: u.migrator, appUrl: u.app, adminUrl: u.admin, dbName: u.database, port: String(port ?? ''), namespace: String(jobId).toLowerCase() };
  const env = {
    TRUTH_DATABASE_NAME: u.database,
    TRUTH_DATABASE_ADMIN_URL: u.admin,
    TRUTH_DATABASE_URL: u.migrator,
    TRUTH_DATABASE_APP_URL: u.app,
    TRUTH_NAMESPACE: vars.namespace,
  };
  for (const [k, v] of Object.entries(cfg.env ?? {})) env[k] = expand(String(v), vars);
  return env;
}

function parseGaps() {
  const file = path.join(root, 'docs', 'gaps', `${jobId}.md`);
  const out = { exists: fs.existsSync(file), waive: new Map() };
  if (!out.exists) return out;
  for (const line of fs.readFileSync(file, 'utf8').split('\n')) {
    const m = /^\s*[-*]?\s*WAIVE:\s*([a-z0-9-]+)\s*[-:—]\s*(.{12,})$/i.exec(line);
    if (m) out.waive.set(m[1].toLowerCase(), m[2].trim());
  }
  return out;
}

async function rlsCatalogCheck(u, tables) {
  const pgMod = requireFromRepo(root, 'pg');
  const pg = pgMod.default ?? pgMod;
  const client = new pg.Client({ connectionString: u.admin });
  await client.connect();
  const problems = [];
  try {
    for (const t of tables) {
      const r = await client.query(
        `SELECT c.oid, c.relrowsecurity AS rls, c.relforcerowsecurity AS force,
                EXISTS (SELECT 1 FROM pg_attribute a WHERE a.attrelid = c.oid AND a.attname = 'company_id' AND NOT a.attisdropped) AS has_company,
                (SELECT count(*) FROM pg_policy p WHERE p.polrelid = c.oid) AS policies
           FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
          WHERE c.relkind IN ('r','p') AND c.relname = $1 AND n.nspname NOT IN ('pg_catalog','information_schema')`,
        [t.name],
      );
      if (r.rowCount === 0) {
        problems.push(`table ${t.name} is declared by a migration but does not exist after migrating`);
        continue;
      }
      for (const row of r.rows) {
        if (row.has_company && !(row.rls && row.force && Number(row.policies) > 0)) problems.push(`table ${t.name}: company_id present but rls=${row.rls} force=${row.force} policies=${row.policies}`);
        if (!row.has_company && cfg.sql.requireRls) problems.push(`table ${t.name}: no company_id column (only allowed for explicitly global tables)`);
      }
    }
  } finally {
    await client.end().catch(() => {});
  }
  return problems;
}

async function allTenantTablesCheck(u) {
  const pgMod = requireFromRepo(root, 'pg');
  const pg = pgMod.default ?? pgMod;
  const client = new pg.Client({ connectionString: u.admin });
  await client.connect();
  try {
    const r = await client.query(
      `SELECT n.nspname AS schema, c.relname AS name, c.relrowsecurity AS rls, c.relforcerowsecurity AS force,
              (SELECT count(*) FROM pg_policy p WHERE p.polrelid = c.oid) AS policies
         FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE c.relkind IN ('r','p') AND n.nspname NOT IN ('pg_catalog','information_schema') AND n.nspname NOT LIKE 'pg_toast%'
          AND EXISTS (SELECT 1 FROM pg_attribute a WHERE a.attrelid = c.oid AND a.attname = 'company_id' AND NOT a.attisdropped)`,
    );
    const total = await client.query(`SELECT count(*)::int AS n FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace WHERE c.relkind IN ('r','p') AND n.nspname NOT IN ('pg_catalog','information_schema') AND n.nspname NOT LIKE 'pg_toast%'`);
    const bad = r.rows.filter((row) => !(row.rls && row.force && Number(row.policies) > 0));
    return { tenantTables: r.rowCount, totalTables: total.rows[0].n, bad: bad.map((b) => `${b.schema}.${b.name} (rls=${b.rls} force=${b.force} policies=${b.policies})`) };
  } finally {
    await client.end().catch(() => {});
  }
}

function finish(kind, extra) {
  const failed = steps.filter((s) => s.status === 'fail');
  const overall = failed.length === 0 ? 'pass' : 'fail';
  const result = { kind, job: jobId, repo: repoName(root, cfg), kitVersion: KIT_VERSION, commit: git(root, ['rev-parse', 'HEAD']).stdout.trim(), finishedAt: nowIso(), overall, steps, ...extra };
  writeJson(path.join(dir, `${jobId}.json`), result);
  process.stdout.write(`\n${overall === 'pass' ? 'GATE PASSED' : `GATE FAILED (${failed.map((s) => s.id).join(', ')})`}  ${jobId}  -> ${path.join(dir, `${jobId}.json`)}\n`);
  return result;
}

// ------------------------------------------------------------------ job gate
async function jobGate() {
  if (!args.job) throw new Error('--job <JOB-ID> is required');
  if (!args.owned) throw new Error('--owned "<globs>" is required (the paths this job owns)');
  const pathspec = csv(args.owned);
  const exclude = csv(args.exclude);
  const ownedGlobs = [...pathspec, `docs/gaps/${jobId}.md`, `docs/jobs/${jobId}/**`];
  const sharedGlobs = cfg.sharedGlobs ?? [];
  const owned = makeMatcher(ownedGlobs);
  const excluded = makeMatcher(exclude);
  const sharedMatch = makeMatcher(sharedGlobs);
  const isOwned = (p) => owned(p) && !(exclude.length > 0 && excluded(p));
  const isShared = (p) => sharedGlobs.length > 0 && sharedMatch(p);
  const changed = changedFiles(root, cfg);
  const changedOwned = changed.filter((f) => isOwned(f.path));
  const live = changedOwned.filter((f) => f.status !== 'D' && fs.existsSync(path.join(root, f.path)));
  const scanRels = args.full ? listFiles(root).filter(isOwned) : live.map((f) => f.path);
  const gaps = parseGaps();
  const base = mergeBase(root, cfg);
  process.stdout.write(`gate ${jobId}  owned=${pathspec.join(',')}  changed=${changedOwned.length}  base=${(base ?? 'none').slice(0, 10)}\n`);

  await step('ownership', async () => {
    const outside = changed.filter((f) => !isOwned(f.path) && !isShared(f.path));
    if (outside.length > 0) return { status: 'fail', details: [`${outside.length} changed file(s) outside the owned paths (other jobs own them):`, ...outside.slice(0, 30).map((f) => `${f.status} ${f.path}`), 'revert them (git restore --source=HEAD -- <file>) or describe the needed change in docs/gaps/' + jobId + '.md'] };
    if (changedOwned.length === 0) return { status: 'fail', details: ['no changes inside the owned paths: nothing was built'] };
    return { status: 'pass', details: [`${changedOwned.length} file(s) changed, all inside the owned paths`] };
  });

  await step('shrink', async () => {
    const notes = [];
    for (const f of changedOwned) {
      if (f.status === 'D') {
        notes.push(`deleted ${f.path}: safe-commit needs --allow-delete "${f.path}:<reason>"`);
        continue;
      }
      if (f.status !== 'M' || !base) continue;
      const old = git(root, ['show', `${base}:${f.path}`], { maxBuffer: 64 * 1024 * 1024 });
      if (old.code !== 0 || isBinary(old.stdout)) continue;
      const abs = path.join(root, f.path);
      if (!fs.existsSync(abs)) continue;
      const nOld = lineCount(old.stdout);
      const nNew = lineCount(fs.readFileSync(abs, 'utf8'));
      if (nOld - nNew >= 40 && nNew < nOld * 0.7) notes.push(`shrunk ${f.path}: ${nOld} -> ${nNew} lines: safe-commit needs --allow-shrink "${f.path}:<reason>"`);
    }
    return { status: notes.length ? 'warn' : 'pass', details: notes.length ? notes : ['no deletions or large reductions'] };
  });

  await step('syntax', async () => {
    const problems = [];
    for (const rel of live.map((f) => f.path)) {
      if (!isText(rel)) continue;
      const text = fs.readFileSync(path.join(root, rel), 'utf8');
      const bad = syntaxProblem(root, rel, text);
      if (bad) problems.push(`${rel}: ${bad}`);
    }
    return problems.length ? { status: 'fail', details: problems } : { status: 'pass', details: [`${live.length} changed file(s) parse`] };
  });

  const migrations = live.filter((f) => f.path.endsWith('.sql')).map((f) => f.path);
  await step('sql', async () => {
    if (migrations.length === 0) return { status: 'skip', details: ['no SQL files changed'] };
    const details = [];
    let errors = 0;
    for (const rel of migrations) {
      const text = fs.readFileSync(path.join(root, rel), 'utf8');
      for (const f of lintSql(text, { sql: cfg.sql })) {
        if (f.severity === 'error') errors += 1;
        details.push(`${rel}:${f.line} ${f.severity} ${f.rule}: ${f.message}`);
      }
    }
    if (args['stamp-block']) {
      const m = /^(\d{14})-(\d{14})$/.exec(args['stamp-block']);
      if (!m) {
        errors += 1;
        details.push(`invalid --stamp-block ${args['stamp-block']}`);
      } else {
        const seen = new Map();
        for (const f of changedOwned.filter((x) => x.status === 'A' && x.path.endsWith('.sql'))) {
          const base2 = path.posix.basename(f.path);
          const sm = /^(\d{14})_([a-z0-9_]+)\.sql$/.exec(base2);
          if (!sm) {
            errors += 1;
            details.push(`${f.path}: name must be <14-digit-stamp>_<module>_<slug>.sql (lowercase, underscores)`);
            continue;
          }
          if (sm[1] < m[1] || sm[1] > m[2]) {
            errors += 1;
            details.push(`${f.path}: stamp ${sm[1]} is outside your reserved block ${args['stamp-block']}`);
          }
          if (seen.has(sm[1])) {
            errors += 1;
            details.push(`${f.path}: stamp ${sm[1]} is used twice (${seen.get(sm[1])})`);
          }
          seen.set(sm[1], f.path);
        }
      }
    }
    return { status: errors ? 'fail' : 'pass', details: details.length ? details : [`${migrations.length} migration file(s) pass the static lint`] };
  });

  const scans = [
    ['language', (rel, text) => scanLanguageText(rel, text, cfg)],
    ['stubs', (rel, text) => (isCode(rel) ? scanStubsText(rel, text, cfg) : [])],
    ['secrets', (rel, text) => scanSecretsText(rel, text, cfg)],
    ['size', (rel, text) => scanSizeText(rel, text, cfg)],
  ];
  const files = readFiles(root, scanRels);
  for (const [id, fn] of scans) {
    await step(id, async () => {
      const findings = files.flatMap((f) => fn(f.path, f.text));
      const errors = findings.filter((f) => f.severity === 'error');
      const warns = findings.filter((f) => f.severity !== 'error');
      const lines = [...errors, ...warns].map((f) => `${f.path}:${f.line} ${f.severity} ${f.rule}: ${f.message}`);
      if (errors.length) return { status: 'fail', details: lines };
      return { status: warns.length ? 'warn' : 'pass', details: lines.length ? lines : [`${files.length} file(s) scanned`] };
    });
  }

  await step('i18n', async () => {
    const hasCatalog = files.some((f) => f.path.endsWith('.json') && /(^|\/)(i18n|locales?|messages)\//i.test(f.path));
    if (!args.ui && !hasCatalog) return { status: 'skip', details: ['no UI and no catalogues in this job'] };
    const ownedCatalogs = readFiles(root, listFiles(root).filter((p) => isOwned(p) && p.endsWith('.json') && /(^|\/)(i18n|locales?|messages)\//i.test(p)));
    const merged = new Map();
    for (const f of [...ownedCatalogs, ...files]) merged.set(f.path, f);
    const allCatalogs = readFiles(root, listFiles(root, { untracked: true }).filter(makeMatcher(cfg.i18n.catalogGlobs)));
    const findings = scanI18n(root, [...merged.values()], { ...cfg, _allCatalogs: allCatalogs });
    const lines = findings.map((f) => `${f.path}:${f.line} ${f.severity} ${f.rule}: ${f.message}`);
    return findings.some((f) => f.severity === 'error') ? { status: 'fail', details: lines } : { status: 'pass', details: lines.length ? lines : ['catalogues are complete in all locales and the UI has no hard-coded text'] };
  });

  const ownedDirs = pathspec.map((p) => p.replace(/\/\*\*.*$/, '').replace(/\/$/, '')).filter((p) => fs.existsSync(path.join(root, p)));
  for (const [id, key, when] of [['lint', 'lint', true], ['typecheck', 'typecheck', live.some((f) => /\.(ts|tsx|mts)$/.test(f.path)) || args.typecheck], ['registry', 'registryCheck', true]]) {
    await step(id, async () => {
      const cmd = cfg.commands?.[key];
      if (!cmd) return { status: 'skip', details: [`no commands.${key} in scripts/truth/config.json`] };
      if (!when) return { status: 'skip', details: ['not applicable (no TypeScript changed)'] };
      const r = runCommand(id, expand(cmd, { paths: ownedDirs.map(shq).join(' '), job: jobId, root }));
      return r.code === 0 ? { status: 'pass', details: [`${cmd}`], log: r.log } : { status: 'fail', details: [`${cmd} exited ${r.code}`, ...r.tail.split('\n').slice(-14)], log: r.log };
    });
  }

  let dbUrls = null;
  let tablesDeclared = [];
  const wantDb = args.db || migrations.length > 0;
  await step('migrate', async () => {
    if (!wantDb) return { status: 'skip', details: ['job has no migrations and --db was not given'] };
    const cmd = cfg.commands?.migrate;
    if (!cmd) return { status: 'fail', details: ['commands.migrate is not configured in scripts/truth/config.json: the W0 job of this repository must define the migration command'] };
    dbUrls = await createJobDatabase({ root, cfg, job: jobId, fresh: true });
    const env = dbEnv(dbUrls);
    for (const round of [1, 2]) {
      const r = runCommand(`migrate-${round}`, cmd, { env, heavy: 'db' });
      if (r.code !== 0) return { status: 'fail', details: [`run ${round}: ${cmd} exited ${r.code}`, ...r.tail.split('\n').slice(-16)], log: r.log };
    }
    await grantApp({ root, cfg, job: jobId });
    tablesDeclared = migrations.flatMap((rel) => tablesCreated(fs.readFileSync(path.join(root, rel), 'utf8')));
    const problems = await rlsCatalogCheck(dbUrls, tablesDeclared);
    if (problems.length) return { status: 'fail', details: problems };
    return { status: 'pass', details: [`migrations applied twice on a fresh database ${dbUrls.database}; ${tablesDeclared.length} owned table(s) verified with forced RLS`] };
  });

  await step('tests', async () => {
    const cmd = cfg.commands?.test;
    if (!cmd) return { status: 'fail', details: ['commands.test is not configured in scripts/truth/config.json'] };
    const testFiles = live.filter((f) => isTestFile(f.path) && !isE2eFile(f.path));
    if (testFiles.length === 0) return { status: 'fail', details: ['no test file (*.test.mjs / *.test.ts / test_*.py ...) was added or changed inside the owned paths: a job without tests is not done'] };
    const paths = csv(args.tests).length ? csv(args.tests) : [...new Set(testFiles.map((f) => f.path))];
    if (wantDb && !dbUrls) dbUrls = await createJobDatabase({ root, cfg, job: jobId, fresh: false });
    const port = await allocatePort(jobId);
    const env = dbUrls ? dbEnv(dbUrls, port) : { TRUTH_NAMESPACE: String(jobId).toLowerCase(), PORT: String(port) };
    const r = runCommand('tests', expand(cmd, { paths: paths.map(shq).join(' '), job: jobId, root }), { env, heavy: wantDb ? 'db' : 'build' });
    const skipped = /(?:#\s*skipped\s+([1-9]\d*))|(?:\b([1-9]\d*)\s+skipped\b)/i.exec(`${r.tail}`);
    if (r.code !== 0) return { status: 'fail', details: [`${cmd} exited ${r.code}`, ...r.tail.split('\n').slice(-20)], log: r.log };
    if (skipped) return { status: 'fail', details: ['the run reports skipped tests: skipped tests prove nothing, make them run or delete them'], log: r.log };
    return { status: 'pass', details: [`${paths.length} test path(s) passed`], log: r.log };
  });

  await step('e2e', async () => {
    if (!args.ui) return { status: 'skip', details: ['job has no UI'] };
    const waived = gaps.waive.get('e2e');
    const cmd = cfg.commands?.e2e;
    if (!cmd) return waived ? { status: 'waived', details: [`waived in docs/gaps/${jobId}.md: ${waived}`] } : { status: 'fail', details: ['commands.e2e is not configured: the W0 job of this repository must define the Playwright command'] };
    const paths = csv(args.e2e).length ? csv(args.e2e) : [...new Set(live.filter((f) => isE2eFile(f.path) && /\.[mc]?[jt]sx?$/.test(f.path)).map((f) => f.path))];
    if (paths.length === 0) return waived ? { status: 'waived', details: [`waived: ${waived}`] } : { status: 'fail', details: ['a job with UI needs Playwright specs (*.spec.mjs / *.spec.ts under an e2e/ directory) inside its owned paths'] };
    if (wantDb && !dbUrls) dbUrls = await createJobDatabase({ root, cfg, job: jobId, fresh: false });
    const port = await allocatePort(jobId);
    const env = dbUrls ? dbEnv(dbUrls, port) : { PORT: String(port), TRUTH_NAMESPACE: String(jobId).toLowerCase() };
    const r = runCommand('e2e', expand(cmd, { paths: paths.map(shq).join(' '), job: jobId, root }), { env: { ...env, TRUTH_PORT: String(port) }, heavy: 'browser' });
    if (r.code === 0) return { status: 'pass', details: [`browser acceptance passed (${paths.join(', ')})`], log: r.log };
    return waived ? { status: 'waived', details: [`e2e failed but is waived in docs/gaps/${jobId}.md: ${waived}`, ...r.tail.split('\n').slice(-6)], log: r.log } : { status: 'fail', details: [`${cmd} exited ${r.code}`, ...r.tail.split('\n').slice(-20)], log: r.log };
  });

  if (dbUrls && !args['keep-db'] && steps.every((s) => s.status !== 'fail')) await dropJobDatabase({ root, cfg, job: jobId }).catch(() => {});
  const result = finish('job', {
    ownedGlobs: pathspec,
    excludeGlobs: exclude,
    ownedHash: ownedContentHash(root, ownedGlobs, [...exclude, ...sharedGlobs]),
    base,
    changed: changedOwned.map((f) => `${f.status} ${f.path}`),
    waived: [...gaps.waive.entries()].map(([k, v]) => `${k}: ${v}`),
  });
  return result.overall === 'pass' ? EXIT.OK : EXIT.FAIL;
}

// ------------------------------------------------------------------ trunk gate
async function trunkGate() {
  process.stdout.write(`trunk gate ${jobId}  kit ${KIT_VERSION}\n`);
  const commandStep = (id, cmd, opts = {}) =>
    step(id, async () => {
      if (!cmd) return { status: 'skip', details: [`not configured in scripts/truth/config.json (${id})`] };
      const r = runCommand(id, cmd, opts);
      return r.code === 0 ? { status: 'pass', details: [cmd], log: r.log } : { status: 'fail', details: [`${cmd} exited ${r.code}`, ...r.tail.split('\n').slice(-18)], log: r.log };
    });
  await commandStep('install', cfg.install);
  await commandStep('build', cfg.commands?.build);
  await commandStep('typecheck', cfg.commands?.typecheck);
  await commandStep('lint', cfg.commands?.lint ? expand(cfg.commands.lint, { paths: '.', job: jobId, root }) : null);
  await commandStep('registry', cfg.commands?.registryCheck);

  let u = null;
  await step('migrate', async () => {
    const cmd = cfg.commands?.migrate;
    if (!cmd) return { status: 'skip', details: ['no commands.migrate configured'] };
    u = await createJobDatabase({ root, cfg, job: jobId, fresh: true });
    const env = dbEnv(u);
    for (const round of [1, 2]) {
      const r = runCommand(`migrate-${round}`, cmd, { env, heavy: 'db' });
      if (r.code !== 0) return { status: 'fail', details: [`run ${round}: ${cmd} exited ${r.code}`, ...r.tail.split('\n').slice(-18)], log: r.log };
    }
    await grantApp({ root, cfg, job: jobId });
    const info = await allTenantTablesCheck(u);
    if (info.bad.length && cfg.sql.requireRls) return { status: 'fail', details: [`${info.bad.length}/${info.tenantTables} tenant tables without forced RLS + policy:`, ...info.bad.slice(0, 20)] };
    return { status: 'pass', details: [`fresh database migrated twice; ${info.totalTables} tables, ${info.tenantTables} tenant tables all with forced RLS`] };
  });

  await step('boot', async () => {
    const boot = cfg.boot;
    if (!boot?.command) return { status: 'skip', details: ['no boot command configured'] };
    if (!u) return { status: 'fail', details: ['boot needs the migrated database from the migrate step'] };
    const port = await allocatePort(jobId);
    const env = { ...process.env, ...dbEnv(u, port), PORT: String(port), ...(boot.env ?? {}) };
    for (const [k, v] of Object.entries(boot.env ?? {})) env[k] = expand(String(v), { port: String(port), appUrl: u.app, migratorUrl: u.migrator });
    const logFile = path.join(dir, `${jobId}.boot.log`);
    const out = fs.openSync(logFile, 'w');
    const { spawn } = await import('node:child_process');
    const child = spawn('bash', ['-c', boot.command], { cwd: root, env, stdio: ['ignore', out, out], detached: true });
    let exited = null;
    child.on('exit', (code) => {
      exited = code ?? 'signal';
    });
    const url = `http://127.0.0.1:${port}${boot.readyPath ?? '/readyz'}`;
    const deadline = Date.now() + (boot.timeoutSeconds ?? 90) * 1000;
    let status = null;
    while (Date.now() < deadline && exited === null) {
      try {
        const res = await fetch(url, { signal: AbortSignal.timeout(3000) });
        status = res.status;
        if (res.status === 200) break;
      } catch {
        status = null;
      }
      await sleep(1000);
    }
    try {
      process.kill(-child.pid, 'SIGTERM');
    } catch {
      // already gone
    }
    await sleep(500);
    fs.closeSync(out);
    if (status === 200) return { status: 'pass', details: [`${boot.command} answered 200 on ${boot.readyPath ?? '/readyz'}`], log: logFile };
    return { status: 'fail', details: [exited !== null ? `server exited with ${exited} before it became ready` : `${url} answered ${status ?? 'nothing'} within ${boot.timeoutSeconds ?? 90}s`, ...tail(fs.readFileSync(logFile, 'utf8'), 14).split('\n')], log: logFile };
  });

  await commandStep('smoke', cfg.commands?.smokeTests, { heavy: 'db', env: u ? dbEnv(u) : {} });

  await step('hygiene', async () => {
    const allow = cfg.rootAllowlist ?? [];
    if (allow.length === 0) return { status: 'skip', details: ['no rootAllowlist configured'] };
    const matcher = makeMatcher(allow);
    const top = [...new Set(listFiles(root, { untracked: false }).map((f) => f.split('/')[0]))];
    const junk = top.filter((t) => !matcher(t));
    return junk.length ? { status: 'fail', details: [`${junk.length} entries at the repository root are not in rootAllowlist:`, ...junk.slice(0, 30)] } : { status: 'pass', details: [`${top.length} root entries, all allowed`] };
  });

  await step('scan-full', async () => {
    const rels = listFiles(root, { untracked: false }).filter((f) => isText(f) && !makeMatcher(cfg.generatedGlobs)(f));
    const fl = readFiles(root, rels.slice(0, 60000));
    const counts = { language: 0, stubs: 0, size: 0 };
    for (const f of fl) {
      counts.language += scanLanguageText(f.path, f.text, cfg).filter((x) => x.severity === 'error').length;
      if (isCode(f.path)) counts.stubs += scanStubsText(f.path, f.text, cfg).filter((x) => x.severity === 'error').length;
      counts.size += scanSizeText(f.path, f.text, cfg).filter((x) => x.severity === 'error').length;
    }
    const line = `repository-wide findings (informational, burned down by the feature jobs): language=${counts.language} stubs=${counts.stubs} oversized-files=${counts.size}`;
    return { status: args.strict && (counts.language || counts.stubs || counts.size) ? 'fail' : 'warn', details: [line] };
  });

  if (u && steps.every((s) => s.status !== 'fail')) await dropJobDatabase({ root, cfg, job: jobId }).catch(() => {});
  const result = finish('trunk', {});
  if (result.overall === 'pass') {
    const statusFile = path.join(root, 'docs', 'truth', 'TRUNK_STATUS.json');
    fs.mkdirSync(path.dirname(statusFile), { recursive: true });
    writeJson(statusFile, {
      overall: 'pass',
      commit: result.commit,
      generatedAt: result.finishedAt,
      kitVersion: KIT_VERSION,
      repo: result.repo,
      steps: steps.map((s) => ({ id: s.id, status: s.status })),
    });
    // bind the result to the status file so that safe-commit.mjs can land exactly this file
    const bound = ['docs/truth/TRUNK_STATUS.json'];
    const resFile = path.join(dir, `${jobId}.json`);
    writeJson(resFile, { ...(readJson(resFile) ?? result), ownedGlobs: bound, excludeGlobs: [], ownedHash: ownedContentHash(root, [...bound, `docs/gaps/${jobId}.md`, `docs/jobs/${jobId}/**`], []) });
    process.stdout.write(`wrote ${path.relative(root, statusFile)}: land it with  node scripts/truth/safe-commit.mjs --job ${jobId} --paths docs/truth/TRUNK_STATUS.json --message "chore(truth): trunk gate passed" --integrate\n`);
  }
  return result.overall === 'pass' ? EXIT.OK : EXIT.FAIL;
}

async function show() {
  const r = readJson(path.join(dir, `${args.job}.json`));
  if (!r) {
    process.stdout.write('no result\n');
    return EXIT.FAIL;
  }
  process.stdout.write(`${r.job}: ${r.overall} at ${r.finishedAt} (commit ${String(r.commit).slice(0, 10)})\n`);
  for (const s of r.steps) process.stdout.write(`  ${s.status.padEnd(6)} ${s.id}\n`);
  return r.overall === 'pass' ? EXIT.OK : EXIT.FAIL;
}

try {
  const code = sub === 'job' ? await jobGate() : sub === 'trunk' ? await trunkGate() : sub === 'show' ? await show() : (() => {
    process.stderr.write(`${fs.readFileSync(new URL(import.meta.url), 'utf8').split('\n').slice(0, 14).join('\n')}\n`);
    return EXIT.USAGE;
  })();
  process.exit(code);
} catch (err) {
  process.stderr.write(`gate: ${err.stack || err.message}\n`);
  process.exit(EXIT.FAIL);
}
