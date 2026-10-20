# Gaps — SKL-W0-01 (TASK-0004)

## G1 (RESOLVED 2026-10-20 — keep the history, do not act on it): `scripts/truth/preflight.mjs` and the truth harness do not exist in this repo

> **RESOLVED (2026-10-20):** the truth kit 1.1.0 is installed in this repository since commit
> `40ce066` (`chore(truth): install Ottili truth kit 1.1.0`). `preflight.mjs`, `gate.mjs`,
> `safe-commit.mjs`, `db.mjs` and `port.mjs` are present and working: the preflight prints
> `ok`, the gate runs all steps and `safe-commit.mjs` is the only sanctioned way to commit.
> The text below is the observation of 2026-10-16 and is kept as history — it is no longer
> a live gap.

- **Claim in task:** "Start by running: `node scripts/truth/preflight.mjs --job SKL-W0-01 --status` (exit 20 means BLOCKED, and so does a missing or crashing script)."
- **Observed (2026-10-16):** `node scripts/truth/preflight.mjs --job SKL-W0-01 --status` exits 1 with
  `Cannot find module '/srv/ottili/repo/skills/scripts/truth/preflight.mjs'`. The whole `scripts/truth/`
  directory is absent from the working tree and from `git ls-files scripts/`. The same holds for
  `gate.mjs`, `safe-commit.mjs`, `db.mjs`, `port.mjs`.
- **Search:** `find / -name "preflight.mjs" 2>/dev/null` returns only unrelated copies under other repos'
  `node_modules/tsx/dist/`, other jobs' `tests/support/`, and other products' `src/`. No copy belongs to
  the `skills` repo or to the truth kit.
- **Ownership:** `scripts/truth/**` is on this job's own EXCLUDE list, so it is another job's prerequisite,
  not mine to create.
- **Impact:** the blocked-check, gate, and commit-and-merge commands in the job card cannot be executed
  from this repo as written. Every later task of SKL-W0-01 that calls them stops at once.
- **Request (cross-job):** provide `scripts/truth/{preflight,gate,safe-commit,db,port}.mjs` (plus the
  manifest/README they expect) for the `skills` repo, or point SKL-W0-01 at an existing kit location.
  Recorded in `docs/truth/REPAIR_LOG.md`.
- **Workaround used in this pass:** the DONE WHEN criteria were verified directly with `git ls-files`,
  `find`, `git grep`, and `node scripts/gen-catalog.mjs --check` instead of the gate harness.

## G2 (informational): `README.md` and `catalog.json` mention `business-de`

- These reference the **package** `skills/business-de` (the canonical copy), which exists. They are not
  stale references to the deleted top-level `business-de/` duplicate.
- Verified: `skills/business-de/` exists and holds the business skills;
  `catalog.json` `packages["business-de"].path` = `skills/business-de`.
- No tracked file references a top-level `business-de/` path. README.md:19 explicitly notes
  "canonical copy under skills/business-de/".
- Action: none required; recorded for completeness.

## G3 (verification record for TASK-0004, 2026-10-16)

Grep for `business-de` across this job's paths, as the task requires before any delete:

| Path | Result |
|---|---|
| `scripts/` | no match (install.sh derives packages from `skills/` folders; no hardcoded `business-de`) |
| `tests/` | no match |
| `docs/` | `docs/truth/REPAIR_LOG.md` and `docs/truth/REPO_SHAPE.md` mention it **historically** (D-004, "stale top-level duplicate"); `docs/R3_OWNERS.json` lists `skills/business-de/**` as owned by `skills-business-de-r3` |
| `catalog.json` | matches only the **package** `skills/business-de` (`packages["business-de"].path` = `skills/business-de`, 26 skill paths under it) |
| `README.md` | one match at line 19 — the `business-de/` entry in the layout tree. **Stale:** it carried the leftover comment "canonical copy under skills/business-de/", which referred to the deleted duplicate. Fixed in this pass (see commit). |

Conclusion: nothing references the deleted top-level `business-de/`. The canonical copy is
`skills/business-de/` (10 SKILL.md), owned by `skills-business-de-r3`, and stays.

## G4 (state.json files are inside another job's skills, not at the root)

`git ls-files | grep state.json` returns three files, all under `skills/business-de/`:
- `skills/business-de/immutability-state.json`
- `skills/business-de/period_lock_state.json`
- `skills/business-de/skr-journal-mapping/period_lock_state.json`

These are owned by `skills-business-de-r3` (`skills/business-de/**`) and are part of that job's
EVALS fixtures/state. They are **not** root state files and are not in scope for deletion.

## G4 (verification record for TASK-0006, 2026-10-16)

Repository invariants turned into executable tests under `tests/hygiene/`:

| Invariant | Test | Real repo | Broken fixture |
|---|---|---|---|
| no tracked symlink with an absolute target | `no-bad-symlinks.test.mjs` | PASS | PASS (fails) |
| no tracked symlink that is a self-loop | `no-bad-symlinks.test.mjs` | PASS | PASS (fails) |
| no tracked symlink with a dangling target | `no-bad-symlinks.test.mjs` | PASS | PASS (fails) |
| no tracked database/journal files | `no-database-files.test.mjs` | PASS | PASS (fails) |
| root entries restricted to `rootAllowlist` | `root-allowlist.test.mjs` | PASS | PASS (fails) |
| no tracked file above 5 MiB without a reason | `no-large-files.test.mjs` | PASS | PASS (fails) |
| every workspace project name is unique | `unique-projects.test.mjs` | PASS | PASS (fails) |
| every internal dependency uses the workspace protocol | `workspace-protocol.test.mjs` | PASS | PASS (fails) |
| `.npmrc` maps `@ottili` to the private registry, no public fallback | `npmrc-scope.test.mjs` | PASS | PASS (fails) |

- **Shared helper:** `tests/hygiene/_fixture.mjs` (creates throwaway git repositories for the broken
  fixtures; never writes into the real worktree).
- **`scripts/truth/heavy.sh` is absent** from this repo (see G1), so the tests were run directly with
  `node tests/hygiene/<name>.test.mjs`. They are plain Node 22 `node:test` modules with no
  dependencies beyond Node and git.
- **Pre-existing, not mine:** `skills/agentic-data/skill-authoring-evals/report_test.json` shows as
  modified; it was already modified before this pass and belongs to the `skills-agentic-data-r3-02`
  job. Left untouched.

## G5 (observation, TASK-0006): `tests/hygiene/clean-tree.test.mjs` is red on a pre-existing dirty tree

- `node tests/hygiene/clean-tree.test.mjs` exits 1. The three culprits were present **before** this pass
  (timestamps 01:12 and 01:43, i.e. the TASK-0005 pass), not created by any test in this task:
  - `M skills/agentic-data/skill-authoring-evals/report_test.json` — modified by the
    `skills-agentic-data-r3-02` job; not mine to touch.
  - `?? docs/truth/REPO_PROBE.txt` — empty (0 bytes) probe file, untracked, uncommitted.
  - `?? scripts/verify-status.mjs` — untracked `STATUS.md` honest-status checker, uncommitted.
- Every test written in TASK-0006 creates its broken fixture in a throwaway `mkdtemp` git repository
  under `/tmp` and cleans it up in a `finally` block, so none of them dirties the worktree. Verified:
  running the full suite leaves only the three pre-existing entries above.
- Action: none required from SKL-W0-01. The two untracked files are scratch from another job's pass;
  deleting tracked/untracked files I do not own is outside my remit. Recorded so the next pass does not
  mistake this for a TASK-0006 regression.

## G6 (UNVERIFIED, TASK-0008): Docker leak test (`pg-rls-leak-test.sh`)

- `docker` is installed (`/usr/bin/docker`, rc=0) but no live Postgres container was
  spun up in this pass, so the end-to-end tenant-isolation leak test was **not** run.
- The checker-level proof stands: `check_rls_migration.py` passes
  `references/examples/good_migration.sql` (rc=0) and fails all three hostile fixtures
  (rc=1), and its self-test passes (rc=0). That is static analysis, not a live
  cross-tenant read assertion.
- **To verify:** `cd skills/engineering/pg-rls-multitenant/scripts && ./pg-rls-leak-test.sh
  <migration.sql>` against a real hq migration. Requires Docker + network pull of
  `postgres:18-alpine`. Not attempted here — recorded as an open item, not a gap in
  the shipped artefacts.

## G7 (UNVERIFIED, TASK-0008): the GUC name decision is hardcoded

- `check_rls_migration.py` has `TENANT_GUC = "app.company_id"` as a module constant
  (line 28); there is **no** `config.json` or env var in the skill that lets an
  operator switch it. The D-006 evidence table (995 / 4 / 733 / 347 hits for
  `app.company_id` across hq-v2, ld3-v2, alran-core-v2, console-v2) is the basis for
  the choice and is recorded in `docs/truth/REPAIR_LOG.md`, but the decision cannot be
  re-tuned from outside the code without an edit.
- **To verify:** an operator must confirm `app.company_id` is still the product
  standard at the next product-lane pass, or request a `config.json` /
  `--guc` flag on the checker so the choice is data-driven rather than hardcoded.

## G8 (INTEGRATION STATUS, TASK-0008): commits landed on local `main`, not yet on `origin/main`

- **State:** local `main` is a clean fast-forward of `origin/main` (merge-base
  `53e1499`; `git log origin/main..main` lists only this job's 28 commits; `git log
  main..origin/main` is empty). There is **no divergence and no rebase conflict** —
  the integration step is a plain push, not a merge.
- **Blocked:** `git push origin main` exits 126 with
  `git-guard: blocked 'git push origin main' (shared working tree, R3 rules)`.
  The GIT GUARD also blocks checkout/switch/restore/stash/clean/rebase/merge/pull/
  `add -A`/`add .`/`commit -a`/`reset --hard`, so there is no in-job way to move the
  commits onto `origin/main`.
- **Also blocked:** the card's `node scripts/truth/safe-commit.mjs --integrate`
  cannot run — `scripts/truth/**` does not exist in this repo (G1, cross-job
  prerequisite on this job's EXCLUDE list). This job therefore lands via plain
  `git commit` guarded to its owned paths, exactly as TASK-0001–TASK-0007 did.
- **To finish integration:** an operator (or the guard owner) runs
  `git push origin main` from this tree. After that, `origin/main` will carry
  `efcbc48` and the W1 jobs (canonical-skills, domain-references-and-preamble) will
  see the integrated state.
- **Verified on the integrated local state:** `python3 -I scripts/validate.py` →
  `ok: 32 skills validated`; `node scripts/gen-catalog.mjs --check` →
  `ok: catalog unchanged (32 skills, 5 packages)`; `git status --porcelain` shows
  only the three pre-existing entries from G5.

## G9 (cross-job request, TASK-0002, 2026-10-20): `.gitignore` does not ignore `.germo/`

- **Observed:** the GERMO orchestrator writes its own state into `.germo/` at the repository
  root (`notes/SKL-W0-01.md`, `notes/task_history.log`, `state.journal`, `state.json`). The
  truth kit enumerates untracked files with `git ls-files --others --exclude-standard`, so
  these four files appeared in the job's diff and the gate's `ownership` step failed with
  `4 changed file(s) outside the owned paths (other jobs own them)`.
- **Ownership:** `.gitignore` is owned by `skills-engineering-r3` (per `docs/R3_OWNERS.json`),
  not by this job, so this job did not edit it.
- **Request (cross-job):** add one line to `.gitignore`:
  ```
  .germo/
  ```
  `.truth/` is already ignored there; `.germo/` is the orchestrator's equivalent.
- **Workaround used in this pass:** `.germo/` was added to the worktree-local
  `.git/info/exclude` (not a tracked file, nothing committed). The gate's `ownership` step
  passes with it. The repository-level fix is still wanted: every job in every worktree hits
  the same failure otherwise.
- **Also relevant:** `tests/hygiene/clean-tree.test.mjs` is red for the same reason (an
  untracked directory at the root). It goes green as soon as `.germo/` is ignored.

## G10 (tooling defect, TASK-0002, 2026-10-20): git 2.53.0 hides untracked files from `safe-commit`

- **Observed:** `scripts/truth/safe-commit.mjs` enumerates the working tree with
  `git status --porcelain=v1 -z --untracked-files=all`. On this host (git 2.53.0) that command
  prints **nothing** — reproducible in an empty scratch repository, with and without `-z`, with
  `--porcelain=v1` and with `--porcelain=v2`. `--untracked-files=normal` and
  `git ls-files --others --exclude-standard` (which `scripts/truth/gate.mjs` uses) are unaffected.
- **Impact:** `safe-commit` cannot see a NEW file, so a job that creates a file can commit it
  only if the file is staged first. In this pass the first `safe-commit` run committed 6 of 9
  owned paths and left the three new test files untracked; they landed in a second commit after
  an explicit `git add -- <paths>` (which AGENTS.md permits).
- **Ownership:** `scripts/truth/**` is operator-owned and on this job's EXCLUDE list.
- **Request (cross-job):** in `scripts/truth/safe-commit.mjs`, enumerate the working tree with
  `git status --porcelain=v1 -z` (default untracked mode) plus
  `git ls-files --others --exclude-standard -z` for untracked files, instead of
  `--untracked-files=all`. One line, no behaviour change on unaffected git versions.
- **Workaround used in this pass:** stage new files with an explicit `git add -- <paths>` before
  calling `safe-commit`.

## G11 (cross-job request, TASK-0002 VERIFY, 2026-10-20): `README.md` heading does not match the orchestrator contract test

- **Observed:** `node tests/orchestrator/test_preamble_contracts.test.mjs` fails with
  `README has no preamble section`. The test (in this job's owned paths) asserts
  `readme.includes('## Orchestrator preamble (generated)')`; `README.md` line 268 says
  `## Orchestrator preamble`. The second assertion of the same test
  (`node scripts/gen-preamble.mjs --check`) does pass.
- **Ownership:** `README.md` belongs to `skills-engineering-r3` per `docs/R3_OWNERS.json`
  and is **not** on this job's owned list, so this job did not edit it. The test file is
  owned by this job, but relaxing the assertion would only hide the drift, so the test was
  left strict on purpose.
- **Request (cross-job):** in `README.md`, change the heading on line 268 from
  `## Orchestrator preamble` to `## Orchestrator preamble (generated)` so it names the
  generated artefact the same way the golden body names it
  (`# Orchestrator Preamble (generated)`).
- **Effect while open:** the GitHub workflow step "Run orchestrator contract tests"
  stays red. The truth-kit gate is unaffected — its test command is `pytest -q {paths}`,
  and the whole pytest suite is green (44 passed).

## G12 (cross-job request, TASK-0002 VERIFY, 2026-10-20): engineering self-tests hard-code `/srv/ottili` paths and write into the repository root

- **Observed (CI step "Run engineering skill self-tests"):** 2 of 14 self-tests fail on this
  host, both because they point at paths that only exist on a developer machine:
  - `skills/engineering/pg-rls-multitenant/scripts/check_rls_migration_test.py` expects
    `/srv/ottili/repo/hq-v2/modules/procure-to-stock/migrations/20261010000000_hq_procure_to_stock_r3_04_audit.sql`
    (`file not found`).
  - `skills/engineering/module-contract-first/scripts/check_contract_drift_test.py` expects
    `/srv/ottili/repo/skills/skills/engineering/module-contract-first`.
- **Second effect:** `skills/engineering/long-test-discipline/scripts/run_long_test_test.sh`
  passes, but it leaves `long-test.log` and `long-test.log.out` in the **repository root**,
  which makes `tests/hygiene/clean-tree.test.mjs` red on every CI run.
- **Ownership:** `skills/engineering/**` belongs to `skills-engineering-r3` per
  `docs/R3_OWNERS.json`; this job did not touch those files. The two stray log files were
  produced by running the self-test in this pass and were removed again, so the worktree is
  clean.
- **Request (cross-job):**
  1. Make the two self-tests resolve their fixtures relative to the repository
     (`Path(__file__).resolve().parents[...]` / a fixture inside the skill folder) instead of
     `/srv/ottili/repo/...`, or skip the assertion when the external repo is absent.
  2. In `run_long_test_test.sh`, export `OTTLI_TEST_LOG` to a path inside a temporary
     directory. `skills/engineering/long-test-discipline/scripts/run_long_test.sh` already
     honours `OTTLI_TEST_LOG="${OTTLI_TEST_LOG:-long-test.log}"`, so no change to the
     script itself is needed.

## G13 (open, TASK-0002 VERIFY, 2026-10-20): `scripts/verify-status.mjs` is fixed but still unproven against a real product `STATUS.md`

- **Fixed in this pass (both were in this job's owned paths):**
  - `raw.rstrip()` — a Python method — crashed the checker on the first table row
    (`TypeError: raw.rstrip is not a function`).
  - `require("node:fs")` inside an ES module threw a `ReferenceError` that a bare `catch`
    swallowed, so the evidence file was never checked and **every** row was reported as
    `log path not found`: a checker that could never pass.
  - Both are covered by `tests/hygiene/test_verify_status.py`; with the old file restored
    4 of its 5 tests fail, with the fix all 5 pass.
- **Still open:** the repository has **no root `STATUS.md`** (only `skills/*/STATUS.md`,
  which belong to other jobs), so the checker has never been run against a product-repo
  claim table. The row format it expects is
  `| <claim> | <command> | <exit code> <log path> |`.
- **To close:** create the root `STATUS.md` (TASK-0008 owns it) with claim rows that point
  at log files that exist in the tree, then run
  `node scripts/verify-status.mjs STATUS.md --root .` and expect exit 0.
