#!/usr/bin/env node
// Guarded commit + integration. This is the ONLY way jobs commit and land code.
//
//   node scripts/truth/safe-commit.mjs --job ID --message "feat(scope): summary" --paths "dir/**,file.mjs" [--exclude "glob"]
//        [--body-file path] [--trailer "Key: value"] [--allow-shrink "path:reason"] [--allow-delete "path:reason"]
//        [--integrate] [--dry-run] [--no-gate-check]
//
// What it refuses (exit codes in lib/common.mjs EXIT):
//   * an empty / "." / absolute / ".." path specification, or paths inside .git or node_modules
//   * staged or modified TRACKED files outside the owned paths (exit 4) - nothing is ever swept up with "add -A"
//   * deleting tracked files, or shrinking a file by >= 40 lines AND below 70 % of its size, without an explicit allowance
//   * syntax errors (node --check, JSON, SQL lint, Python, shell), committed secrets, non-English commit messages
//   * integrating without a passing gate result bound to the exact content being committed
// Integration modes (scripts/truth/config.json "integration"): push-trunk | local-trunk | branch-only | auto (default).
import fs from 'node:fs';
import path from 'node:path';
import { lintSql } from './checks/sqllint.mjs';
import { isBinary, lineCount, readHead, syntaxProblem } from './lib/files.mjs';
import { scanLanguageText, scanSecretsText } from './checks/scan.mjs';
import {
  EXIT, git, gitOut, loadConfig, makeMatcher, nowIso, ownedContentHash, parseArgs, readJson, repoRoot, repoName, resultsDir, sleep, writeJson, csv, mergeBase,
} from './lib/common.mjs';

const args = parseArgs(process.argv.slice(2), { flags: ['integrate', 'dry-run', 'no-gate-check'], multi: ['allow-shrink', 'allow-delete', 'trailer', 'path'] });

function die(code, message) {
  process.stderr.write(`safe-commit: ${message}\n`);
  process.exit(code);
}

export function validatePathspec(list) {
  if (list.length === 0) throw new Error('--paths is required (explicit owned paths; never "." or a repository-wide glob)');
  const out = [];
  for (const raw of list) {
    const p = raw.trim().replace(/^\.\//, '');
    if (!p || p === '.' || p === '*' || p === '**' || p === '**/*') throw new Error(`refusing broad path specification "${raw}"`);
    if (p.startsWith('/') || p.startsWith(':') || p.split('/').includes('..')) throw new Error(`refusing path "${raw}": must be a relative path inside the repository`);
    if (/(^|\/)(\.git|node_modules)(\/|$)/.test(p)) throw new Error(`refusing path "${raw}"`);
    out.push(p);
  }
  return out;
}

function parseAllowances(list) {
  return (list ?? []).map((entry) => {
    const i = entry.indexOf(':');
    const p = i === -1 ? entry : entry.slice(0, i);
    const reason = i === -1 ? '' : entry.slice(i + 1).trim();
    if (reason.length < 8) die(EXIT.USAGE, `allowance "${entry}" needs a reason of at least 8 characters ("path:why this is intended")`);
    return { path: p, reason, match: makeMatcher([p]) };
  });
}

function parseStatus(out) {
  const parts = out.split('\0');
  const entries = [];
  for (let i = 0; i < parts.length; i += 1) {
    const rec = parts[i];
    if (!rec) continue;
    entries.push({ x: rec[0], y: rec[1], path: rec.slice(3) });
  }
  return entries;
}

function trunkWorktree(root, branch) {
  const out = git(root, ['worktree', 'list', '--porcelain']).stdout.split('\n\n');
  for (const block of out) {
    const wt = /^worktree (.+)$/m.exec(block);
    const br = /^branch refs\/heads\/(.+)$/m.exec(block);
    if (wt && br && br[1] === branch) return wt[1];
  }
  return null;
}

function resolveMode(root, cfg) {
  if (cfg.integration && cfg.integration !== 'auto') return cfg.integration;
  const remotes = git(root, ['remote']).stdout.split('\n').filter(Boolean);
  if (remotes.includes(cfg.remote)) {
    const r = git(root, ['ls-remote', '--exit-code', cfg.remote, `refs/heads/${cfg.trunkBranch}`], { timeout: 30000 });
    if (r.code === 0) return 'push-trunk';
  }
  if (trunkWorktree(root, cfg.trunkBranch)) return 'local-trunk';
  return 'branch-only';
}

async function withDirLock(dir, fn, { waitMs = 600000, staleMs = 900000 } = {}) {
  const deadline = Date.now() + waitMs;
  for (;;) {
    try {
      fs.mkdirSync(dir);
      break;
    } catch (err) {
      if (err.code !== 'EEXIST') throw err;
      try {
        if (Date.now() - fs.statSync(dir).mtimeMs > staleMs) fs.rmSync(dir, { recursive: true, force: true });
      } catch {
        // raced with the owner
      }
      if (Date.now() > deadline) throw new Error(`could not acquire ${dir} within ${waitMs / 1000}s`);
      await sleep(500 + Math.random() * 1500);
    }
  }
  try {
    return await fn();
  } finally {
    fs.rmSync(dir, { recursive: true, force: true });
  }
}

function conflictFiles(root) {
  return git(root, ['diff', '--name-only', '--diff-filter=U']).stdout.split('\n').filter(Boolean);
}

async function rebaseOnto(root, ref) {
  const contains = git(root, ['merge-base', '--is-ancestor', ref, 'HEAD']);
  if (contains.code === 0) return { ok: true, files: [] };
  const r = git(root, ['rebase', ref]);
  if (r.code === 0) return { ok: true, files: [] };
  const files = conflictFiles(root);
  git(root, ['rebase', '--abort']);
  return { ok: false, files, message: r.stderr.trim().split('\n').slice(-3).join(' | ') };
}


/** Every commit of this job (everything between trunk and HEAD) must stay inside the owned paths - also commits made without this script. */
function assertOnlyOwnedHistory(root, baseRef, ownedGlobs, excludeGlobs) {
  if (!baseRef) return;
  const names = gitOut(root, ['diff', '--name-only', '-z', baseRef, 'HEAD']).split('\0').filter(Boolean);
  const owned = makeMatcher(ownedGlobs);
  const excluded = makeMatcher(excludeGlobs);
  const outside = names.filter((n) => !owned(n) || (excludeGlobs.length > 0 && excluded(n)));
  if (outside.length > 0) {
    die(EXIT.OUTSIDE, `the commits of this job touch ${outside.length} file(s) outside the owned paths: ${outside.slice(0, 15).join(', ')}. Other jobs own them. Restore them from trunk (git restore --source=${baseRef} -- <file>, then commit that restoration through safe-commit.mjs) or describe the needed change in docs/gaps/<JOB>.md.`);
  }
}

async function integrate({ root, cfg, job, ownedGlobs, excludeGlobs, hashExclude, hashGlobs, evidenceHash }) {
  const mode = resolveMode(root, cfg);
  const trunk = cfg.trunkBranch;
  const stale = () => {
    if (!evidenceHash) return false;
    return ownedContentHash(root, hashGlobs, hashExclude) !== evidenceHash;
  };
  if (mode === 'push-trunk') {
    for (let attempt = 1; attempt <= 10; attempt += 1) {
      const f = git(root, ['fetch', cfg.remote, trunk], { timeout: 120000 });
      if (f.code !== 0) {
        if (attempt === 10) die(7, `cannot fetch ${cfg.remote}/${trunk}: ${f.stderr.trim()}`);
        await sleep(2000 * attempt);
        continue;
      }
      const rb = await rebaseOnto(root, `${cfg.remote}/${trunk}`);
      if (!rb.ok) die(EXIT.CONFLICT, `rebase onto ${cfg.remote}/${trunk} conflicts in: ${rb.files.join(', ') || '(unknown)'}. These files changed on trunk while you worked. Re-read trunk's version, re-apply your intent on top of it, keep both sides' behaviour, re-run the gate and retry. Never discard the other side.`);
      if (stale()) die(EXIT.FAIL, 'files in your owned paths changed during the rebase: re-run the gate before integrating');
      assertOnlyOwnedHistory(root, `${cfg.remote}/${trunk}`, ownedGlobs, excludeGlobs);
      const p = git(root, ['push', cfg.remote, `HEAD:refs/heads/${trunk}`], { timeout: 180000 });
      if (p.code === 0) return { mode, trunkSha: gitOut(root, ['rev-parse', 'HEAD']).trim() };
      if (attempt === 10) die(7, `push to ${cfg.remote}/${trunk} failed after ${attempt} attempts: ${p.stderr.trim().split('\n').slice(-2).join(' | ')}`);
      await sleep(1000 * attempt + Math.random() * 3000);
    }
  }
  if (mode === 'local-trunk') {
    const wt = trunkWorktree(root, trunk);
    if (!wt) die(7, `no worktree has branch ${trunk} checked out; set integration to branch-only in scripts/truth/config.json`);
    const common = gitOut(root, ['rev-parse', '--git-common-dir']).trim();
    const lock = path.resolve(root, common, 'truth-integrate.lock');
    return withDirLock(lock, async () => {
      const rb = await rebaseOnto(root, trunk);
      if (!rb.ok) die(EXIT.CONFLICT, `rebase onto ${trunk} conflicts in: ${rb.files.join(', ') || '(unknown)'}. Re-apply your intent on top of trunk's version, keep both sides' behaviour, re-run the gate and retry.`);
      if (stale()) die(EXIT.FAIL, 'files in your owned paths changed during the rebase: re-run the gate before integrating');
      assertOnlyOwnedHistory(root, trunk, ownedGlobs, excludeGlobs);
      const sha = gitOut(root, ['rev-parse', 'HEAD']).trim();
      for (let attempt = 1; attempt <= 20; attempt += 1) {
        const dirty = git(wt, ['status', '--porcelain', '--untracked-files=no']).stdout.trim();
        if (!dirty) {
          const m = git(wt, ['merge', '--ff-only', sha]);
          if (m.code === 0) return { mode, trunkSha: sha, trunkWorktree: wt };
          die(7, `fast-forward of ${trunk} failed: ${m.stderr.trim().split('\n').slice(-2).join(' | ')}`);
        }
        await sleep(3000 + Math.random() * 3000);
      }
      return die(8, `the trunk worktree ${wt} has uncommitted changes (another job is writing there); retry later or switch integration to branch-only`);
    });
  }
  // branch-only
  assertOnlyOwnedHistory(root, mergeBase(root, cfg), ownedGlobs, excludeGlobs);
  const branch = `truth/${job}`;
  const sha = gitOut(root, ['rev-parse', 'HEAD']).trim();
  git(root, ['update-ref', `refs/heads/${branch}`, sha]);
  const remotes = git(root, ['remote']).stdout.split('\n').filter(Boolean);
  let pushed = false;
  if (remotes.includes(cfg.remote)) pushed = git(root, ['push', '--force-with-lease', cfg.remote, `refs/heads/${branch}:refs/heads/${branch}`], { timeout: 180000 }).code === 0;
  return { mode: 'branch-only', branch, pushed, trunkSha: sha };
}

async function main() {
  const root = repoRoot();
  const cfg = loadConfig(root);
  const job = args.job;
  if (!job || !/^[A-Z0-9][A-Z0-9-]{2,40}$/.test(job)) die(EXIT.USAGE, '--job <JOB-ID> is required (e.g. HQ-031)');
  if (!args.message) die(EXIT.USAGE, '--message "<type>(<scope>): <summary>" is required');
  const subject = args.message.trim();
  if (subject.length > 100) die(EXIT.USAGE, 'commit subject longer than 100 characters');
  const bodyText = args['body-file'] ? fs.readFileSync(args['body-file'], 'utf8') : '';
  const msgFindings = scanLanguageText('COMMIT_MESSAGE', `${subject}\n${bodyText}`, cfg);
  if (msgFindings.length > 0) die(EXIT.USAGE, `commit message must be English: ${msgFindings[0].message}`);

  let pathspec;
  try {
    pathspec = validatePathspec([...csv(args.paths), ...(args.path ?? [])]);
  } catch (err) {
    die(EXIT.USAGE, err.message);
  }
  const exclude = csv(args.exclude);
  const jobDocs = [`docs/gaps/${job}.md`, `docs/jobs/${job}/**`];
  const ownedGlobs = [...pathspec, ...jobDocs];
  const owned = makeMatcher(ownedGlobs);
  const excluded = makeMatcher(exclude);
  const sharedGlobs = cfg.sharedGlobs ?? [];
  const sharedMatch = makeMatcher(sharedGlobs);
  const hashExclude = [...exclude, ...sharedGlobs];
  const isOwned = (p) => (owned(p) && !(exclude.length > 0 && excluded(p))) || (sharedGlobs.length > 0 && sharedMatch(p));
  const allowShrink = parseAllowances(args['allow-shrink']);
  const allowDelete = parseAllowances(args['allow-delete']);

  const status = parseStatus(git(root, ['-c', 'status.renames=false', 'status', '--porcelain=v1', '-z', '--untracked-files=all']).stdout);
  const inside = [];
  const outsideTracked = [];
  const outsideUntracked = [];
  for (const e of status) {
    const untracked = e.x === '?' && e.y === '?';
    if (isOwned(e.path)) inside.push({ ...e, untracked });
    else if (untracked) outsideUntracked.push(e.path);
    else outsideTracked.push(e.path);
  }
  const staged = gitOut(root, ['diff', '--cached', '--name-only', '-z']).split('\0').filter(Boolean);
  const stagedOutside = staged.filter((p) => !isOwned(p));
  if (outsideTracked.length > 0 || stagedOutside.length > 0) {
    const list = [...new Set([...outsideTracked, ...stagedOutside])];
    die(EXIT.OUTSIDE, `tracked files outside your owned paths are modified or staged:\n  ${list.slice(0, 40).join('\n  ')}\nUndo those edits (git restore --source=HEAD --staged --worktree -- <file>) unless they truly belong to your job; if a change outside your ownership is needed, describe it in docs/gaps/${job}.md instead of making it.`);
  }
  if (inside.length === 0) die(EXIT.NOTHING, 'nothing to commit inside the owned paths');

  const problems = [];
  const files = [];
  let added = 0;
  let removed = 0;
  for (const e of inside) {
    const abs = path.join(root, e.path);
    const exists = fs.existsSync(abs);
    const headText = e.untracked ? null : readHead(root, e.path);
    if (!exists) {
      if (headText === null) continue; // vanished untracked file
      const lines = lineCount(headText);
      removed += lines;
      if (!allowDelete.some((a) => a.match(e.path))) problems.push(`DELETE ${e.path} (${lines} lines): add --allow-delete "${e.path}:<reason>" if this deletion is intended and justified`);
      files.push({ path: e.path, status: 'D', old: lines, new: 0 });
      continue;
    }
    const text = fs.readFileSync(abs, 'utf8');
    if (isBinary(text)) {
      files.push({ path: e.path, status: headText === null ? 'A' : 'M', binary: true });
      continue;
    }
    const nNew = lineCount(text);
    const nOld = headText === null ? 0 : lineCount(headText);
    added += Math.max(0, nNew - nOld);
    removed += Math.max(0, nOld - nNew);
    files.push({ path: e.path, status: headText === null ? 'A' : 'M', old: nOld, new: nNew });
    if (headText !== null && nOld - nNew >= 40 && nNew < nOld * 0.7 && !allowShrink.some((a) => a.match(e.path))) {
      problems.push(`SHRINK ${e.path}: ${nOld} -> ${nNew} lines. Restore the missing code or add --allow-shrink "${e.path}:<reason>" when the reduction is intended.`);
    }
    const bad = syntaxProblem(root, e.path, text);
    if (bad) problems.push(`SYNTAX ${e.path}: ${bad}`);
    if (e.path.endsWith('.sql')) {
      for (const f of lintSql(text, { sql: cfg.sql })) if (f.severity === 'error') problems.push(`SQL ${e.path}:${f.line} ${f.rule}: ${f.message}`);
    }
    for (const f of scanSecretsText(e.path, text, cfg)) problems.push(`SECRET ${e.path}:${f.line} ${f.message}`);
  }
  if (removed > 2000 && removed > added * 3 && !allowShrink.some((a) => a.path === '*')) problems.push(`TOTAL deletion ${removed} lines vs ${added} added: add --allow-shrink "*:<reason>" if this clean-up is intended`);

  if (problems.length > 0) die(EXIT.FAIL, `refusing to commit:\n  ${problems.join('\n  ')}`);

  let evidenceHash = null;
  const dir = resultsDir(root, cfg);
  if (!args['no-gate-check']) {
    const result = readJson(path.join(dir, `${job}.json`));
    if (!result) die(EXIT.FAIL, `no gate result for ${job}: run  node scripts/truth/gate.mjs job --job ${job} --owned "${pathspec.join(',')}"  first`);
    if (result.overall !== 'pass') die(EXIT.FAIL, `the last gate run for ${job} did not pass (overall=${result.overall}); fix the failing steps and re-run the gate`);
    const same = JSON.stringify([...(result.ownedGlobs ?? [])].sort()) === JSON.stringify([...pathspec].sort()) && JSON.stringify([...(result.excludeGlobs ?? [])].sort()) === JSON.stringify([...exclude].sort());
    if (!same) die(EXIT.FAIL, 'the gate was run with different owned paths than --paths/--exclude here: use identical values');
    evidenceHash = result.ownedHash;
    if (ownedContentHash(root, ownedGlobs, hashExclude) !== evidenceHash) die(EXIT.FAIL, 'files changed after the last passing gate run: re-run the gate, then commit');
  }

  if (args['dry-run']) {
    process.stdout.write(`${JSON.stringify({ dryRun: true, job, files, added, removed, mode: resolveMode(root, cfg) }, null, 2)}\n`);
    return;
  }

  const paths = files.map((f) => f.path);
  for (let i = 0; i < paths.length; i += 200) {
    const r = git(root, ['add', '--', ...paths.slice(i, i + 200)]);
    if (r.code !== 0) die(EXIT.FAIL, `git add failed: ${r.stderr.trim()}`);
  }
  const trailers = [`Job: ${job}`, ...(args.trailer ?? [])];
  const msg = [subject, bodyText.trim(), trailers.join('\n')].filter(Boolean).join('\n\n');
  const env = { ...process.env };
  if (!git(root, ['config', 'user.email']).stdout.trim()) {
    env.GIT_AUTHOR_NAME ??= 'Ottili Truth Job';
    env.GIT_AUTHOR_EMAIL ??= 'truth-job@ottili.invalid';
    env.GIT_COMMITTER_NAME ??= env.GIT_AUTHOR_NAME;
    env.GIT_COMMITTER_EMAIL ??= env.GIT_AUTHOR_EMAIL;
  }
  const c = git(root, ['commit', '-m', msg, '--only', '--', ...paths], { env });
  if (c.code !== 0) die(EXIT.FAIL, `git commit failed: ${(c.stderr || c.stdout).trim().split('\n').slice(-6).join(' | ')}`);
  const sha = gitOut(root, ['rev-parse', 'HEAD']).trim();
  const record = { job, repo: repoName(root, cfg), commit: sha, committedAt: nowIso(), files, added, removed };

  if (args.integrate) {
    const landed = await integrate({ root, cfg, job, ownedGlobs: [...ownedGlobs, ...sharedGlobs], excludeGlobs: exclude, hashExclude, hashGlobs: ownedGlobs, evidenceHash });
    Object.assign(record, { integration: landed, preRebaseCommit: record.commit });
    if (landed.trunkSha) record.commit = landed.trunkSha;
    const diff = gitOut(root, ['diff', '--name-only', '-z', `${sha}~1`, sha]).split('\0').filter(Boolean);
    record.committedPaths = diff.length;
  }
  writeJson(path.join(dir, `${job}.commit.json`), record);
  process.stdout.write(`${JSON.stringify(record, null, 2)}\n`);
}

main().catch((err) => die(EXIT.FAIL, err.stack || err.message));
