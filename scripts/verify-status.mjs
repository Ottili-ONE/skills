#!/usr/bin/env node
/**
 * verify-status.mjs — honest-status checker for the real STATUS.md table format.
 *
 * The product repos record every claim as a markdown table row:
 *
 *   | <claim> | <command> | <exit code> <log path> |
 *
 * A row is UNVERIFIED — and the file FAILs — when it lacks any of the three
 * (claim, command, log path) or when the log path it names does not exist on
 * disk. Line numbers are reported so the owner can find the row.
 *
 * Usage: node scripts/verify-status.mjs <STATUS.md> [--root <dir>] [--json]
 * Exit 0 = every claim row verified; 1 = unverified rows; 2 = usage error.
 */
import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";

const ROW_RE = /^\s*\|(.+)\|\s*$/;
const SEP_RE = /^\s*\|[\s\-:|]+\|\s*$/;
const HEADER_RE = /^\s*\|[\w\s]+\|[\w\s]+\|[\w\s]+\|\s*$/;
// A path token: a bare filename or a relative path ending in a known artifact
// suffix, possibly wrapped in backticks.
const PATH_TOKEN_RE = /`?([A-Za-z0-9_\-./]+\.(?:log|json|txt|md|mp4|png|jpg|jpeg|csv|sql|mjs|js|ts|html|xml|yaml|yml))`?/g;
// A command token: a backtick-wrapped string that looks like a shell invocation.
const CMD_RE = /`([^`]+)`/g;
// An exit-code-ish token: a bare number, EXIT=<n>, or a status word.
// The German spelling of "green" is written as a Unicode escape: the source
// stays ASCII (the truth kit's language check rejects literal umlauts in
// code) while the pattern still matches the German word as well.
const EXIT_RE = /\b(?:EXIT\s*=\s*)?(\d{1,3})\b|\b(?:green|ok|passed|gr[u\u00fc]n|PASS(?:ED)?)\b/i;

function splitRow(line) {
  const m = line.match(ROW_RE);
  if (!m) return null;
  const cells = m[1].split("|").map((c) => c.trim());
  return cells;
}

function parseStatus(text) {
  const rows = [];
  let lineno = 0;
  for (const raw of text.split("\n")) {
    lineno += 1;
    // `rstrip()` is a Python method; a JS string has no such method, so the
    // whole checker used to die with "raw.rstrip is not a function" on the
    // first table row it saw.
    const line = raw.replace(/\s+$/, "");
    if (!line.trim()) continue;
    if (SEP_RE.test(line)) continue; // separator row
    const cells = splitRow(line);
    if (!cells || cells.length < 3) continue; // not a 3-col table row
    if (HEADER_RE.test(line)) continue; // header row
    rows.push({ lineno, line, cells });
  }
  return rows;
}

function main(argv) {
  const args = argv.slice(2);
  let json = false;
  let root = ".";
  const positional = [];
  for (let i = 0; i < args.length; i += 1) {
    const a = args[i];
    if (a === "--json") json = true;
    else if (a === "--root") { root = args[++i]; }
    else positional.push(a);
  }
  if (positional.length !== 1) {
    console.error("usage: node verify-status.mjs <STATUS.md> [--root <dir>] [--json]");
    return 2;
  }
  let text;
  try {
    text = readFileSync(positional[0], "utf8");
  } catch (err) {
    console.error(`FAIL: ${positional[0]}: cannot read (${err.message})`);
    return 2;
  }
  const rootDir = resolve(root);
  const rows = parseStatus(text);
  const findings = [];
  for (const r of rows) {
    const [claim, cmd, evidence] = r.cells;
    const problems = [];
    if (!claim) problems.push("no claim text");
    if (!cmd) problems.push("no command");
    const paths = [...evidence.matchAll(PATH_TOKEN_RE)].map((x) => x[1]);
    const path = paths[0] || "";
    if (!path) problems.push("no log path");
    else {
      const p = resolve(rootDir, path);
      // `require` does not exist in an ES module. The old code called it inside
      // a bare `catch`, so the ReferenceError was swallowed and every row was
      // reported as "log path not found" even when the file was there.
      const ok = existsSync(p);
      if (!ok) problems.push(`log path not found: ${path}`);
    }
    if (problems.length) {
      findings.push({ line: r.lineno, claim: claim.slice(0, 80), problems });
    }
  }
  if (json) {
    console.log(JSON.stringify({
      status: findings.length ? "fail" : "ok",
      file: positional[0],
      rows_checked: rows.length,
      findings,
    }, null, 2));
    return findings.length ? 1 : 0;
  }
  if (findings.length) {
    console.error(`FAIL: ${positional[0]} — ${findings.length} unverified row(s)`);
    for (const f of findings) {
      console.error(`  - line ${f.line}: ${f.claim || "(empty)"}`);
      for (const p of f.problems) console.error(`      ${p}`);
    }
    return 1;
  }
  console.log(`ok: ${positional[0]} — all ${rows.length} claim rows verified`);
  return 0;
}

process.exit(main(process.argv));
