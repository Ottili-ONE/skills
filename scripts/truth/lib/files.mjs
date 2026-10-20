// File helpers shared by safe-commit.mjs and gate.mjs.
import path from 'node:path';
import { requireFromRepo, run, git } from './common.mjs';

export function lineCount(text) {
  if (text === '') return 0;
  const n = text.split('\n').length;
  return text.endsWith('\n') ? n - 1 : n;
}

export function readHead(root, rel) {
  const r = run('git', ['-C', root, 'show', `HEAD:${rel}`], { maxBuffer: 64 * 1024 * 1024 });
  return r.code === 0 ? r.stdout : null;
}

export function isBinary(text) {
  return text.includes('\u0000');
}

export function syntaxProblem(root, rel, text) {
  const ext = path.extname(rel).toLowerCase();
  const abs = path.join(root, rel);
  if (['.mjs', '.cjs', '.js'].includes(ext)) {
    const r = run(process.execPath, ['--check', abs]);
    return r.code === 0 ? null : r.stderr.trim().split('\n').slice(0, 6).join(' | ');
  }
  if (ext === '.json' && !/(^|\/)(tsconfig[^/]*|\.eslintrc[^/]*|jsconfig[^/]*)\.json$/.test(rel)) {
    try {
      JSON.parse(text);
    } catch (err) {
      return `invalid JSON: ${err.message}`;
    }
  }
  if (ext === '.py') {
    const r = run('python3', ['-I', '-c', 'import sys;compile(open(sys.argv[1]).read(), sys.argv[1], "exec")', abs]);
    return r.code === 0 ? null : r.stderr.trim().split('\n').slice(-2).join(' | ');
  }
  if (ext === '.sh') {
    const r = run('bash', ['-n', abs]);
    return r.code === 0 ? null : r.stderr.trim().split('\n')[0];
  }
  if (['.jsx', '.tsx', '.ts', '.mts'].includes(ext)) {
    const esbuild = requireFromRepo(root, 'esbuild');
    if (esbuild?.transformSync) {
      try {
        esbuild.transformSync(text, { loader: ext === '.jsx' ? 'jsx' : ext === '.tsx' ? 'tsx' : 'ts', logLevel: 'silent' });
      } catch (err) {
        return `parse error: ${String(err.message).split('\n')[0]}`;
      }
    }
  }
  return null;
}

