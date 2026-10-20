#!/usr/bin/env node
// Fail-closed preflight. A job that cannot run honestly must stop BEFORE touching anything.
//
//   node scripts/truth/preflight.mjs --job ID [--needs db,registry,browser,keycloak,platform,valkey,minio,mail,wordpress]
//        [--requires-trunk] [--after JOB[@repo],JOB...] [--owned "globs"] [--stamp-block START-END]
//   node scripts/truth/preflight.mjs --job ID --status      exit 20 when the job has been marked BLOCKED (do nothing then)
//   node scripts/truth/preflight.mjs --job ID --block "why" mark the job BLOCKED by hand (a prerequisite outside the job is missing)
//   node scripts/truth/preflight.mjs --job ID --clear       remove the BLOCKED marker (a human fixed the cause)
//
// --after lists predecessor jobs that must have LANDED on trunk (record <results>/<repo>/<JOB>.commit.json written by safe-commit with a
// non-branch integration; for jobs of this repository the commit with the trailer "Job: <JOB>" must also be part of this worktree).
//
// A failed preflight writes <TRUTH_RESULTS_DIR>/<repo>/<job>.blocked.json and exits 20.
import fs from 'node:fs';
import http from 'node:http';
import https from 'node:https';
import net from 'node:net';
import os from 'node:os';
import path from 'node:path';
import { KIT_VERSION, EXIT, csv, git, listFiles, loadConfig, makeMatcher, nowIso, parseArgs, readJson, repoName, repoRoot, requireFromRepo, resultsDir, resultsRoot, run, sha256, writeJson } from './lib/common.mjs';

const args = parseArgs(process.argv.slice(2), { flags: ['status', 'clear', 'requires-trunk'] });
const job = args.job;
if (!job) {
  process.stderr.write('preflight: --job <JOB-ID> is required\n');
  process.exit(EXIT.USAGE);
}
const root = repoRoot();
const cfg = loadConfig(root);
const dir = resultsDir(root, cfg);
const marker = path.join(dir, `${job}.blocked.json`);

if (args.clear) {
  fs.rmSync(marker, { force: true });
  process.stdout.write('cleared\n');
  process.exit(0);
}
if (args.block) {
  const report = { job, repo: repoName(root, cfg), at: nowIso(), kitVersion: KIT_VERSION, manual: true, checks: [], failed: [{ id: 'manual', ok: false, level: 'error', detail: String(args.block), hint: String(args.block) }] };
  writeJson(marker, report);
  process.stdout.write(`BLOCKED: ${job} marked as blocked: ${args.block}\nEvery later task of this job stops at once. A human clears it with --clear after fixing the cause.\n`);
  process.exit(EXIT.BLOCKED);
}
if (args.status) {
  const m = readJson(marker);
  if (m) {
    process.stdout.write(`BLOCKED: ${job} was stopped by its preflight at ${m.at}. Do not modify anything. Failing checks: ${m.failed.map((f) => f.id).join(', ')}. Details: ${marker}\n`);
    process.exit(EXIT.BLOCKED);
  }
  process.stdout.write('ok\n');
  process.exit(0);
}

const checks = [];
const add = (id, ok, detail, hint = '', level = 'error') => checks.push({ id, ok, level: ok ? 'info' : level, detail, hint });

function httpGet(url, timeoutMs = 4000) {
  return new Promise((resolve) => {
    let u;
    try {
      u = new URL(url);
    } catch {
      resolve({ ok: false, error: 'invalid URL' });
      return;
    }
    const lib = u.protocol === 'https:' ? https : http;
    const req = lib.get(u, { timeout: timeoutMs }, (res) => {
      res.resume();
      resolve({ ok: res.statusCode < 500, status: res.statusCode });
    });
    req.on('timeout', () => {
      req.destroy();
      resolve({ ok: false, error: 'timeout' });
    });
    req.on('error', (err) => resolve({ ok: false, error: err.code || err.message }));
  });
}

function tcpPing(hostPort, payload, timeoutMs = 3000) {
  return new Promise((resolve) => {
    const u = new URL(hostPort.includes('://') ? hostPort : `tcp://${hostPort}`);
    const sock = net.connect({ host: u.hostname, port: Number(u.port || 6379), timeout: timeoutMs });
    let buf = '';
    sock.on('connect', () => sock.write(payload));
    sock.on('data', (d) => {
      buf += d.toString();
      sock.destroy();
      resolve({ ok: /PONG/i.test(buf), reply: buf.trim().slice(0, 40) });
    });
    sock.on('timeout', () => {
      sock.destroy();
      resolve({ ok: false, error: 'timeout' });
    });
    sock.on('error', (err) => resolve({ ok: false, error: err.code || err.message }));
  });
}

function diskFreeGb(p) {
  const r = run('df', ['-Pk', p]);
  if (r.code !== 0) return null;
  const cols = r.stdout.trim().split('\n').pop().split(/\s+/);
  return Number(cols[3]) / 1024 / 1024;
}

function memAvailMb() {
  try {
    const m = /^MemAvailable:\s+(\d+) kB/m.exec(fs.readFileSync('/proc/meminfo', 'utf8'));
    return m ? Math.floor(Number(m[1]) / 1024) : null;
  } catch {
    return null;
  }
}

// ---- always ----
const nodeMajor = Number(process.versions.node.split('.')[0]);
add('node', nodeMajor >= 20, `node ${process.versions.node}`, 'install Node 20 or newer on the worker');
add('kit', fs.existsSync(path.join(root, 'scripts/truth/config.json')) && fs.existsSync(path.join(root, 'scripts/truth/KIT_VERSION')), `truth kit ${KIT_VERSION} in scripts/truth`, 'the truth kit is not committed on trunk of this repository: the operator must run install-all.sh and commit it before any job starts (LAUNCH.md step 2)');
{
  const manifestFile = path.join(root, 'scripts/truth/MANIFEST.sha256');
  if (!fs.existsSync(manifestFile)) add('kit-integrity', false, 'scripts/truth/MANIFEST.sha256 is missing', 'reinstall the kit with install-all.sh (LAUNCH.md step 2)');
  else {
    const bad = [];
    for (const line of fs.readFileSync(manifestFile, 'utf8').split('\n')) {
      const m = /^([0-9a-f]{64})  (.+)$/.exec(line.trim());
      if (!m) continue;
      let actual = null;
      try {
        actual = sha256(fs.readFileSync(path.join(root, m[2])));
      } catch {
        // missing file
      }
      if (actual !== m[1]) bad.push(m[2]);
    }
    add('kit-integrity', bad.length === 0, bad.length ? `modified or missing kit files: ${bad.slice(0, 6).join(', ')}` : 'kit files match MANIFEST.sha256', 'scripts/truth belongs to the operator and is never edited by jobs: restore it with  git restore --source=HEAD -- scripts/truth  or reinstall it (LAUNCH.md step 2)');
  }
}
const wt = git(root, ['rev-parse', '--is-inside-work-tree']);
add('git', wt.code === 0, 'inside a git work tree', 'run the job inside a git worktree of the repository');
const head = git(root, ['rev-parse', 'HEAD']);
add('git-head', head.code === 0, `HEAD ${head.stdout.trim().slice(0, 10)}`, 'repository has no commits');
const free = diskFreeGb(root);
add('disk', free === null || free >= 4, `${free === null ? 'unknown' : free.toFixed(1)} GB free at the work tree`, 'free at least 4 GB on the worker (see LAUNCH.md: reap old worktrees and databases)');
const mem = memAvailMb();
add('memory', mem === null || mem >= 1024, `${mem ?? 'unknown'} MB available`, 'the machine is out of memory: reduce the number of running jobs (see LAUNCH.md ramp-up)', 'warn');
try {
  fs.accessSync(dir, fs.constants.W_OK);
  add('results-dir', true, dir);
} catch {
  add('results-dir', false, dir, 'set TRUTH_RESULTS_DIR to a writable directory outside the repository');
}

// ---- trunk gate ----
if (args['requires-trunk']) {
  const statusFile = path.join(root, 'docs/truth/TRUNK_STATUS.json');
  const st = readJson(statusFile);
  if (!st) add('trunk-status', false, 'docs/truth/TRUNK_STATUS.json is missing', 'the W0 trunk repair jobs of this repository must finish and pass `node scripts/truth/gate.mjs trunk` first (see LAUNCH.md wave order)');
  else {
    const ancestor = st.commit ? git(root, ['merge-base', '--is-ancestor', st.commit, 'HEAD']).code === 0 : false;
    add('trunk-status', st.overall === 'pass' && ancestor, `trunk gate ${st.overall} at ${String(st.commit).slice(0, 10)}${ancestor ? '' : ' (not an ancestor of HEAD)'}`, 'trunk is not green in this worktree: wait for W0 to finish, then start this job from a fresh worktree of trunk');
    add('kit-version', st.kitVersion === KIT_VERSION, `kit ${KIT_VERSION} (trunk gate ran with ${st.kitVersion})`, 'kit version differs from the one that validated trunk', 'warn');
  }
}

// ---- predecessor jobs ----
for (const spec of csv(args.after)) {
  const [id, otherRepo] = spec.split('@');
  const rec = readJson(path.join(resultsRoot(), otherRepo || repoName(root, cfg), `${id}.commit.json`));
  const landed = Boolean(rec && rec.integration && rec.integration.mode !== 'branch-only');
  let reachable = true;
  if (landed && !otherRepo) {
    const found = git(root, ['log', 'HEAD', '-n', '1', '--format=%H', '-E', `--grep=^Job: ${id}$`]);
    reachable = found.code === 0 && found.stdout.trim().length > 0;
  }
  add(`after:${id}`, landed && reachable, landed ? (reachable ? `${id} landed on trunk` : `${id} landed, but is not part of this worktree`) : `${id} has not landed on trunk yet`, landed ? 'this worktree was created before the predecessor landed: start this job again from a fresh worktree of trunk' : `wait until ${id} has finished and landed (see LAUNCH.md launch order), then start this job again`);
}

// ---- stamp block ----
if (args['stamp-block'] && args.owned) {
  const m = /^(\d{14})-(\d{14})$/.exec(args['stamp-block']);
  if (!m) add('stamp-block', false, `invalid --stamp-block ${args['stamp-block']}`, 'expected START-END with 14-digit stamps');
  else {
    const owned = makeMatcher(csv(args.owned));
    const clashes = [];
    for (const f of listFiles(root)) {
      const sm = /(?:^|\/)(\d{14})_[^/]*\.sql$/.exec(f);
      if (sm && sm[1] >= m[1] && sm[1] <= m[2] && !owned(f)) clashes.push(f);
    }
    add('stamp-block', clashes.length === 0, clashes.length ? `migration files of other owners inside your block: ${clashes.slice(0, 5).join(', ')}` : `stamp block ${args['stamp-block']} is free`, 'another job already wrote migrations into your reserved block: report this in docs/gaps and stop');
  }
}

// ---- infrastructure ----
const needs = csv(args.needs);
const env = process.env;
if (needs.includes('registry')) {
  let registry = env.TRUTH_REGISTRY_URL || null;
  for (const f of ['.npmrc', path.join(os.homedir(), '.npmrc')]) {
    if (registry) break;
    try {
      const m = /^@ottili:registry=(.+)$/m.exec(fs.readFileSync(path.isAbsolute(f) ? f : path.join(root, f), 'utf8'));
      if (m) registry = m[1].trim();
    } catch {
      // no npmrc
    }
  }
  if (!registry) add('registry', false, 'no @ottili registry configured (.npmrc "@ottili:registry=" or TRUTH_REGISTRY_URL)', 'configure the private registry (Verdaccio) for the @ottili scope; see LAUNCH.md prerequisites');
  else {
    const r = await httpGet(`${registry.replace(/\/$/, '')}/-/ping`);
    add('registry', r.ok, `${registry} -> ${r.status ?? r.error}`, 'the private @ottili registry is not reachable: start Verdaccio and publish the 13 @ottili/* packages (tag platform-m1-freeze-3) - see LAUNCH.md');
  }
}
if (needs.includes('db')) {
  const adminUrl = env.TRUTH_PG_ADMIN_URL;
  if (!adminUrl) add('db', false, 'TRUTH_PG_ADMIN_URL is not set', 'export the superuser URL of the shared development PostgreSQL 17 (see LAUNCH.md)');
  else {
    const pg = requireFromRepo(root, 'pg');
    if (!pg) add('db', false, 'the "pg" package cannot be resolved', 'run: npm install --prefix scripts/truth --no-audit --no-fund');
    else {
      const P = pg.default ?? pg;
      const client = new P.Client({ connectionString: adminUrl, connectionTimeoutMillis: 4000 });
      try {
        await client.connect();
        const v = await client.query('SHOW server_version');
        add('db', true, `PostgreSQL ${v.rows[0].server_version}`);
      } catch (err) {
        add('db', false, `cannot connect: ${err.message}`, 'start the shared development PostgreSQL and check TRUTH_PG_ADMIN_URL');
      } finally {
        await client.end().catch(() => {});
      }
    }
  }
}
if (needs.includes('browser')) {
  const base = env.PLAYWRIGHT_BROWSERS_PATH || path.join(os.homedir(), '.cache', 'ms-playwright');
  let found = false;
  try {
    found = fs.readdirSync(base).some((d) => /^chromium/.test(d));
  } catch {
    // missing
  }
  add('browser', found, `Chromium in ${base}`, 'install Playwright Chromium on the worker and export PLAYWRIGHT_BROWSERS_PATH (see LAUNCH.md)');
}
if (needs.includes('keycloak')) {
  const base = env.TRUTH_KEYCLOAK_URL || 'http://127.0.0.1:50080';
  const realm = env.TRUTH_KEYCLOAK_REALM || 'ottili-dev';
  const r = await httpGet(`${base}/realms/${realm}/.well-known/openid-configuration`);
  add('keycloak', r.ok && r.status === 200, `${base} realm ${realm} -> ${r.status ?? r.error}`, 'start Keycloak 26 with the ottili-dev realm (see LAUNCH.md)');
}
if (needs.includes('platform')) {
  const base = (env.TRUTH_PLATFORM_URL || 'http://127.0.0.1:50101').replace(/\/$/, '');
  let r = await httpGet(`${base}/readyz`);
  if (!(r.ok && r.status === 200)) r = await httpGet(`${base}/v2/health`);
  add('platform', r.ok && r.status === 200, `${base} -> ${r.status ?? r.error}`, 'start the shared Platform development host from Platform trunk and export TRUTH_PLATFORM_URL (see LAUNCH.md)');
}
if (needs.includes('valkey')) {
  const r = await tcpPing(env.TRUTH_VALKEY_URL || 'redis://127.0.0.1:6379', '*1\r\n$4\r\nPING\r\n');
  add('valkey', r.ok, `${env.TRUTH_VALKEY_URL || 'redis://127.0.0.1:6379'} -> ${r.reply ?? r.error}`, 'start Valkey 8 (see LAUNCH.md)');
}
if (needs.includes('minio')) {
  const base = env.TRUTH_MINIO_URL || 'http://127.0.0.1:9000';
  const r = await httpGet(`${base}/minio/health/live`);
  add('minio', r.ok && r.status === 200, `${base} -> ${r.status ?? r.error}`, 'start MinIO (see LAUNCH.md)');
}
if (needs.includes('mail')) {
  const base = env.TRUTH_MAILPIT_URL || 'http://127.0.0.1:8025';
  const r = await httpGet(`${base}/api/v1/info`);
  add('mail', r.ok && r.status === 200, `${base} -> ${r.status ?? r.error}`, 'start Mailpit (see LAUNCH.md)');
}
if (needs.includes('wordpress')) {
  const base = env.TRUTH_WP_URL || 'http://127.0.0.1:8080';
  const r = await httpGet(`${base}/wp-json/`);
  add('wordpress', r.ok && r.status === 200, `${base} -> ${r.status ?? r.error}`, 'start WordPress 6 + MariaDB 11 (see LAUNCH.md)');
}

const failed = checks.filter((c) => !c.ok && c.level === 'error');
const report = { job, repo: repoName(root, cfg), at: nowIso(), kitVersion: KIT_VERSION, head: head.stdout.trim(), checks, failed };
writeJson(path.join(dir, `${job}.preflight.json`), report);
for (const c of checks) process.stdout.write(`${c.ok ? 'ok  ' : c.level === 'warn' ? 'warn' : 'FAIL'} ${c.id.padEnd(14)} ${c.detail}\n`);
if (failed.length > 0) {
  writeJson(marker, report);
  process.stdout.write(`\nBLOCKED: ${job} cannot run honestly.\n${failed.map((f) => `  - ${f.id}: ${f.hint}`).join('\n')}\nDo NOT modify the repository, do NOT improvise a workaround and do NOT fake the missing prerequisite. End your reply with "BLOCKED: <failing check ids>" so the operator sees it. Marker: ${marker}\n`);
  process.exit(EXIT.BLOCKED);
}
fs.rmSync(marker, { force: true });
process.stdout.write('\npreflight passed\n');
