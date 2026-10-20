#!/usr/bin/env node
// Self-test of the truth kit. Builds a throw-away repository with a bare origin in a temp directory and exercises the guards.
// Usage: node scripts/truth/selftest.mjs        (exit 0 = the kit works on this machine)
// With TRUTH_PG_ADMIN_URL set it additionally runs the database checks (db.mjs + gate migrate step).
import { spawnSync } from 'node:child_process';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { lintSql } from './checks/sqllint.mjs';
import { scanI18n, scanLanguageText, scanSecretsText, scanStubsText } from './checks/scan.mjs';
import { globToRegExp, makeMatcher } from './lib/common.mjs';

const KIT = path.dirname(fileURLToPath(import.meta.url));
let failures = 0;
let passes = 0;
function check(name, ok, detail = '') {
  if (ok) passes += 1;
  else failures += 1;
  process.stdout.write(`${ok ? 'ok  ' : 'FAIL'} ${name}${ok ? '' : `  ${detail}`}\n`);
}
const sh = (cmd, args, opts = {}) => spawnSync(cmd, args, { encoding: 'utf8', ...opts });

// ---- pure functions ----
check('glob: directory prefix', makeMatcher(['modules/a/**'])('modules/a/x/y.mjs') && !makeMatcher(['modules/a/**'])('modules/ab/x.mjs'));
check('glob: plain path matches children', makeMatcher(['modules/a'])('modules/a/x.mjs'));
check('glob: braces and star', makeMatcher(['src/*.{mjs,js}'])('src/a.js') && !makeMatcher(['src/*.{mjs,js}'])('src/sub/a.js'));
check('glob: ** in the middle', globToRegExp('a/**/b.mjs').test('a/b.mjs') && globToRegExp('a/**/b.mjs').test('a/x/y/b.mjs'));

const good = `CREATE TABLE IF NOT EXISTS t (id uuid PRIMARY KEY, company_id uuid NOT NULL);
CREATE INDEX IF NOT EXISTS t_company_idx ON t (company_id);
ALTER TABLE t ENABLE ROW LEVEL SECURITY;
ALTER TABLE t FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS tenant_isolation ON t;
CREATE POLICY tenant_isolation ON t USING (company_id = NULLIF(current_setting('app.company_id', true), '')::uuid);`;
check('sql lint: valid migration passes', lintSql(good).filter((f) => f.severity === 'error').length === 0);
const badRules = lintSql("CREATE TABLE x (id int, offset int);\nCREATE POLICY IF NOT EXISTS p ON x USING (true);\nALTER TABLE x ADD CONSTRAINT IF NOT EXISTS c CHECK (id>0);\n# comment\nSELECT datetime('now');").map((f) => f.rule);
for (const rule of ['R001-policy-if-not-exists', 'R001-constraint-if-not-exists', 'R003-bad-comment', 'R006-dialect', 'R008-reserved-identifier', 'R009-create-table', 'R010-no-company-id']) check(`sql lint: detects ${rule}`, badRules.includes(rule));
check('scan: German text flagged', scanLanguageText('a.mjs', '// Rechnung wird nicht gespeichert und ist kaputt', { language: {} }).length > 0);
check('scan: English passes', scanLanguageText('a.mjs', '// Invoice is stored once and never rewritten', { language: {} }).length === 0);
check('scan: i18n catalogue is exempt', scanLanguageText('x/i18n/de.json', '{"a":"Rechnung wird nicht gespeichert"}', { language: {} }).length === 0);
check('scan: TODO flagged', scanStubsText('a.mjs', '// TODO later', { stubs: {} }).some((f) => f.rule === 'stub-marker'));
check('scan: private key flagged', scanSecretsText('a.mjs', '-----BEGIN PRIVATE KEY-----', { secrets: {} }).length === 1);
check('scan: i18n hard-coded text flagged', scanI18n('.', [{ path: 'a/Page.jsx', text: '<h1>Invoice overview</h1>' }], { locales: ['de', 'en'], i18n: {} }).some((f) => f.rule === 'i18n-hardcoded'));

// ---- repository scenarios ----
const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'truth-selftest-'));
const env = { ...process.env, TRUTH_RESULTS_DIR: path.join(tmp, 'results'), TRUTH_LOCK_DIR: path.join(tmp, 'locks'), TRUTH_MIN_FREE_MB: '1', GIT_AUTHOR_NAME: 't', GIT_AUTHOR_EMAIL: 't@example.com', GIT_COMMITTER_NAME: 't', GIT_COMMITTER_EMAIL: 't@example.com' };
const origin = path.join(tmp, 'origin.git');
const repo = path.join(tmp, 'repo');
const git = (cwd, ...a) => sh('git', ['-C', cwd, ...a], { env });
sh('git', ['init', '-q', '--bare', '-b', 'main', origin], { env });
fs.mkdirSync(repo);
git(repo, 'init', '-q', '-b', 'main');
git(repo, 'remote', 'add', 'origin', origin);
fs.mkdirSync(path.join(repo, 'scripts'), { recursive: true });
fs.cpSync(KIT, path.join(repo, 'scripts', 'truth'), { recursive: true, filter: (s) => !s.includes('node_modules') });
fs.writeFileSync(path.join(repo, 'scripts/truth/config.json'), JSON.stringify({ repo: 'selftest', repoCode: 'ST', integration: 'auto', sharedGlobs: ['shared.lock'], commands: { test: 'node --test {paths}' } }));
sh(process.execPath, [path.join(repo, 'scripts/truth/manifest.mjs'), '--write'], { env });
fs.mkdirSync(path.join(repo, 'src/a'), { recursive: true });
fs.mkdirSync(path.join(repo, 'src/b'), { recursive: true });
fs.writeFileSync(path.join(repo, 'src/a/big.mjs'), `${Array.from({ length: 120 }, (_, i) => `export const v${i} = ${i};`).join('\n')}\n`);
fs.writeFileSync(path.join(repo, 'src/b/other.mjs'), 'export const other = 1;\n');
fs.writeFileSync(path.join(repo, 'README.md'), '# selftest\n');
fs.writeFileSync(path.join(repo, 'shared.lock'), 'v1\n');
git(repo, 'add', '-A');
git(repo, 'commit', '-q', '-m', 'initial');
git(repo, 'push', '-q', 'origin', 'main');
const wt = path.join(tmp, 'wt');
git(repo, 'worktree', 'add', '-q', '--detach', wt, 'HEAD');
const node = (script, args, cwd = wt) => sh(process.execPath, [path.join(cwd, 'scripts/truth', script), ...args], { cwd, env });
const SC = (extra) => node('safe-commit.mjs', ['--job', 'ST-001', '--message', 'feat(a): change', '--paths', 'src/a/**', ...extra]);

let r = node('preflight.mjs', ['--job', 'ST-001']);
check('preflight passes on a healthy machine', r.status === 0, r.stdout + r.stderr);
r = node('preflight.mjs', ['--job', 'ST-002', '--requires-trunk']);
check('preflight blocks without a trunk gate (exit 20)', r.status === 20, `exit ${r.status}`);
check('preflight --status reports BLOCKED', node('preflight.mjs', ['--job', 'ST-002', '--status']).status === 20);
check('preflight --status ok for unblocked job', node('preflight.mjs', ['--job', 'ST-001', '--status']).status === 0);

fs.appendFileSync(path.join(wt, 'README.md'), 'edited\n');
r = SC(['--no-gate-check']);
check('safe-commit refuses edits outside the owned paths (exit 4)', r.status === 4, `exit ${r.status} ${r.stderr}`);
git(wt, 'restore', '--source=HEAD', '--staged', '--worktree', '--', 'README.md');
fs.rmSync(path.join(wt, 'src/a/big.mjs'));
r = SC(['--no-gate-check']);
check('safe-commit refuses deletions without allowance', r.status === 1 && /DELETE/.test(r.stderr), r.stderr);
git(wt, 'restore', '--', 'src/a/big.mjs');
fs.writeFileSync(path.join(wt, 'src/a/big.mjs'), 'export const v0 = 0;\n');
r = SC(['--no-gate-check']);
check('safe-commit refuses large shrinkage', r.status === 1 && /SHRINK/.test(r.stderr), r.stderr);
r = SC(['--no-gate-check', '--dry-run', '--allow-shrink', 'src/a/big.mjs:generated rows were noise']);
check('safe-commit accepts shrinkage with a reason', r.status === 0, r.stderr);
git(wt, 'restore', '--', 'src/a/big.mjs');
fs.writeFileSync(path.join(wt, 'src/a/broken.mjs'), 'export const = ;\n');
r = SC(['--no-gate-check']);
check('safe-commit refuses syntax errors', r.status === 1 && /SYNTAX/.test(r.stderr), r.stderr);
fs.rmSync(path.join(wt, 'src/a/broken.mjs'));
r = node('safe-commit.mjs', ['--job', 'ST-001', '--message', 'feat: ok', '--paths', '.', '--no-gate-check']);
check('safe-commit refuses broad path specs', r.status === 2, `exit ${r.status}`);

fs.mkdirSync(path.join(wt, 'src/a/tests'), { recursive: true });
fs.writeFileSync(path.join(wt, 'src/a/feature.mjs'), 'export const feature = () => 42;\n');
fs.writeFileSync(path.join(wt, 'src/a/tests/feature.test.mjs'), "import test from 'node:test';\nimport assert from 'node:assert/strict';\nimport { feature } from '../feature.mjs';\ntest('feature', () => assert.equal(feature(), 42));\n");
r = SC([]);
check('safe-commit demands a gate result', r.status === 1 && /no gate result/.test(r.stderr), r.stderr);
r = node('gate.mjs', ['job', '--job', 'ST-001', '--owned', 'src/a/**', '--tests', 'src/a/tests/feature.test.mjs']);
check('gate passes for a clean job', r.status === 0, r.stdout + r.stderr);
fs.appendFileSync(path.join(wt, 'src/a/feature.mjs'), 'export const late = 1;\n');
r = SC([]);
check('safe-commit refuses content changed after the gate', r.status === 1 && /changed after/.test(r.stderr), r.stderr);
r = node('gate.mjs', ['job', '--job', 'ST-001', '--owned', 'src/a/**', '--tests', 'src/a/tests/feature.test.mjs']);
check('gate passes again', r.status === 0, r.stdout);
r = SC(['--integrate']);
check('safe-commit commits and integrates', r.status === 0, r.stderr + r.stdout);
const remoteLog = git(origin, 'log', '--format=%s', 'main').stdout;
check('integration landed on origin/main', /feat\(a\): change/.test(remoteLog), remoteLog);
const landedRecord = JSON.parse(fs.readFileSync(path.join(tmp, 'results', 'selftest', 'ST-001.commit.json'), 'utf8'));
check('commit record holds the sha that landed on trunk', landedRecord.commit === git(origin, 'rev-parse', 'main').stdout.trim(), `${landedRecord.commit}`);
r = node('preflight.mjs', ['--job', 'ST-010', '--after', 'ST-001']);
check('preflight --after accepts a landed predecessor', r.status === 0, r.stdout + r.stderr);
r = node('preflight.mjs', ['--job', 'ST-011', '--after', 'ST-777']);
check('preflight --after blocks when the predecessor has not landed (exit 20)', r.status === 20 && /after:ST-777/.test(r.stdout), r.stdout + r.stderr);
r = node('preflight.mjs', ['--job', 'ST-012', '--block', 'prerequisite outside the job is missing']);
check('preflight --block marks the job blocked', r.status === 20 && node('preflight.mjs', ['--job', 'ST-012', '--status']).status === 20);
node('preflight.mjs', ['--job', 'ST-012', '--clear']);
check('preflight --clear removes the marker', node('preflight.mjs', ['--job', 'ST-012', '--status']).status === 0);
fs.appendFileSync(path.join(wt, 'scripts/truth/gate.mjs'), '\n// tampered\n');
r = node('preflight.mjs', ['--job', 'ST-013']);
check('preflight blocks when a kit file was modified (kit-integrity)', r.status === 20 && /kit-integrity/.test(r.stdout), r.stdout + r.stderr);
git(wt, 'restore', '--source=HEAD', '--worktree', '--', 'scripts/truth/gate.mjs');
check('preflight passes again after restoring the kit', node('preflight.mjs', ['--job', 'ST-014']).status === 0);

// a commit that was made without safe-commit must not smuggle foreign files into the integration
fs.writeFileSync(path.join(wt, 'src/b/smuggled.mjs'), 'export const smuggled = 1;\n');
git(wt, 'add', '--', 'src/b/smuggled.mjs');
git(wt, 'commit', '-q', '-m', 'sneaky direct commit');
fs.writeFileSync(path.join(wt, 'src/a/second.mjs'), 'export const second = 2;\n');
r = node('gate.mjs', ['job', '--job', 'ST-020', '--owned', 'src/a/**']);
check('gate flags the directly committed foreign file (ownership)', r.status === 1 && /ownership/.test(r.stdout) && /smuggled/.test(r.stdout), r.stdout);
r = node('safe-commit.mjs', ['--job', 'ST-020', '--message', 'feat(a): second', '--paths', 'src/a/**', '--integrate', '--no-gate-check']);
check('safe-commit refuses to integrate history that touches foreign paths (exit 4)', r.status === 4 && /outside the owned paths/.test(r.stderr), `exit ${r.status} ${r.stderr}`);
git(wt, 'reset', '-q', '--hard', 'origin/main');
git(wt, 'clean', '-q', '-fd');

// shared files (lockfiles): every job may change them, they are committed along, and they never invalidate the gate evidence
fs.mkdirSync(path.join(wt, 'src/a/tests'), { recursive: true });
fs.writeFileSync(path.join(wt, 'src/a/shared.mjs'), 'export const shared = 1;\n');
fs.writeFileSync(path.join(wt, 'src/a/tests/shared.test.mjs'), "import test from 'node:test';\nimport assert from 'node:assert/strict';\nimport { shared } from '../shared.mjs';\ntest('shared', () => assert.equal(shared, 1));\n");
fs.appendFileSync(path.join(wt, 'shared.lock'), 'dep-a\n');
r = node('gate.mjs', ['job', '--job', 'ST-030', '--owned', 'src/a/**']);
check('gate accepts a changed shared file without owning it', r.status === 0, r.stdout);
fs.appendFileSync(path.join(wt, 'shared.lock'), 'dep-b\n');
r = node('safe-commit.mjs', ['--job', 'ST-030', '--message', 'feat(a): shared', '--paths', 'src/a/**', '--integrate']);
check('shared file changes after the gate do not invalidate the evidence', r.status === 0, r.stdout + r.stderr);
check('the shared file was committed with the job', /shared\.lock/.test(git(wt, 'show', '--name-only', '--format=', 'HEAD').stdout), git(wt, 'show', '--name-only', '--format=', 'HEAD').stdout);

fs.writeFileSync(path.join(wt, 'src/a/german.mjs'), '// Rechnung wird nicht gespeichert und ist kaputt\nexport const x = 1;\n');
r = node('gate.mjs', ['job', '--job', 'ST-003', '--owned', 'src/a/**']);
check('gate fails on German text', r.status === 1 && /language/.test(r.stdout), r.stdout);
fs.rmSync(path.join(wt, 'src/a/german.mjs'));
fs.writeFileSync(path.join(wt, 'src/b/foreign.mjs'), 'export const foreign = 1;\n');
r = node('gate.mjs', ['job', '--job', 'ST-004', '--owned', 'src/a/**']);
check('gate fails on files outside the owned paths', r.status === 1 && /ownership/.test(r.stdout), r.stdout);
fs.rmSync(path.join(wt, 'src/b/foreign.mjs'));

r = node('gate.mjs', ['trunk', '--job', 'ST-T1']);
check('trunk gate passes on the fixture and binds its status file', r.status === 0 && fs.existsSync(path.join(wt, 'docs/truth/TRUNK_STATUS.json')), r.stdout + r.stderr);
r = node('safe-commit.mjs', ['--job', 'ST-T1', '--message', 'chore(truth): trunk gate passed', '--paths', 'docs/truth/TRUNK_STATUS.json', '--integrate']);
check('trunk status lands through safe-commit', r.status === 0 && /TRUNK_STATUS/.test(git(origin, 'ls-tree', '-r', '--name-only', 'main').stdout), r.stdout + r.stderr);
r = node('preflight.mjs', ['--job', 'ST-T2', '--requires-trunk']);
check('preflight --requires-trunk passes once the status landed', r.status === 0, r.stdout + r.stderr);
r = sh(path.join(KIT, 'heavy.sh'), ['--class', 'build', '--', 'bash', '-c', 'echo out; echo err >&2; exit 7'], { env });
check('heavy.sh passes exit code and stderr through', r.status === 7 && /err/.test(r.stderr) && /out/.test(r.stdout), `${r.status} ${r.stderr}`);
r = node('port.mjs', ['--job', 'ST-001', '--count', '2']);
const ports = r.stdout.trim().split('\n').map(Number);
check('port.mjs hands out two distinct free ports', ports.length === 2 && ports[0] !== ports[1] && ports.every((p) => p > 1024), r.stdout + r.stderr);

// ---- database (optional) ----
if (process.env.TRUTH_PG_ADMIN_URL) {
  fs.writeFileSync(path.join(repo, 'scripts/truth/config.json'), JSON.stringify({ repo: 'selftest', repoCode: 'ST', commands: { migrate: 'true' } }));
  fs.cpSync(path.join(repo, 'scripts/truth/config.json'), path.join(wt, 'scripts/truth/config.json'));
  r = node('db.mjs', ['create', '--job', 'ST-099', '--fresh']);
  check('db.mjs creates an isolated database with a non-superuser app role', r.status === 0 && /truth_app/.test(r.stdout), r.stderr);
  r = node('db.mjs', ['exec', '--job', 'ST-099', '--role', 'app', '--sql', 'SELECT rolsuper, rolbypassrls FROM pg_roles WHERE rolname = current_user']);
  check('app role is neither superuser nor BYPASSRLS', /"rolsuper": false/.test(r.stdout) && /"rolbypassrls": false/.test(r.stdout), r.stdout + r.stderr);
  node('db.mjs', ['drop', '--job', 'ST-099']);
}

fs.rmSync(tmp, { recursive: true, force: true });
process.stdout.write(`\n${failures === 0 ? 'SELFTEST PASSED' : 'SELFTEST FAILED'}: ${passes} ok, ${failures} failed\n`);
process.exit(failures === 0 ? 0 : 1);
