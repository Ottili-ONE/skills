#!/usr/bin/env node
/**
 * verify-status.mjs — the repository-level entry point of the honest-status checker.
 *
 * The implementation lives in the skill that ships it, so the tool of this
 * repository and the skill an agent installs can never disagree:
 *
 *   skills/engineering/honest-status/scripts/check_status_evidence.py
 *
 * That checker understands both status grammars: the buckets of the skill
 * (DONE / VERIFIED / IN_PROGRESS / BLOCKED / FALSE_DONE) and the claim table
 * of the product repositories, where a row that asserts a success must name
 * the command that was run, the exit code it returned and the log file that
 * proves it. A log file that does not exist proves nothing.
 *
 * Usage: node scripts/verify-status.mjs <STATUS.md> [--root <dir>] [--json]
 *                                       [--format auto|bucket|table]
 * Exit 0 = every claim verified; 1 = unverified claims; 2 = usage error.
 */
import { spawnSync } from "node:child_process";
import { existsSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const CHECKER = resolve(ROOT, "skills/engineering/honest-status/scripts/check_status_evidence.py");
const PYTHON = process.env.PYTHON || "python3";

if (!existsSync(CHECKER)) {
  console.error(`FAIL: the honest-status checker is missing: ${CHECKER}`);
  process.exit(2);
}

const probe = spawnSync(PYTHON, ["--version"], { stdio: "ignore" });
if (probe.error) {
  console.error(`FAIL: ${PYTHON} is not available: ${probe.error.message}`);
  process.exit(2);
}

const result = spawnSync(PYTHON, [CHECKER, ...process.argv.slice(2)], { stdio: "inherit" });
if (result.error) {
  console.error(`FAIL: cannot run ${CHECKER}: ${result.error.message}`);
  process.exit(2);
}
process.exit(result.status ?? 1);
