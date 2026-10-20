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

## G2 (informational, corrected in the TASK-0004 VERIFY pass): `README.md` and `catalog.json` mention `business-de`

- These reference the **package** `skills/business-de` (the canonical copy), which exists.
- Verified: `skills/business-de/` exists and holds the business skills;
  `catalog.json` `packages["business-de"].path` = `skills/business-de`.
- `README.md` line 32 lists `business-de/` inside its `skills/` layout block — that is the
  canonical package, not the deleted top-level duplicate.
  (The earlier entry of this gap quoted a README comment "canonical copy under
  skills/business-de/" at line 19. That comment does not exist in the current README: the
  later rewrite `dbf86e2` ("README-1") removed it. The claim was stale; it is corrected here.)
- The one exception is **G22**: six `ref-*` skills carry the path fragment `business-de/<skill>`
  in their frontmatter description. From the repository root that fragment resolves to nothing —
  it is a leftover of the deleted duplicate.
- Action: G22 carries the request; nothing else to do.

## G3 (verification record for TASK-0004, 2026-10-16)

Grep for `business-de` across this job's paths, as the task requires before any delete:

| Path | Result |
|---|---|
| `scripts/` | no match (install.sh derives packages from `skills/` folders; no hardcoded `business-de`) |
| `tests/` | no match |
| `docs/` | `docs/truth/REPAIR_LOG.md` and `docs/truth/REPO_SHAPE.md` mention it **historically** (D-004, "stale top-level duplicate"); `docs/R3_OWNERS.json` lists `skills/business-de/**` as owned by `skills-business-de-r3` |
| `catalog.json` | matches only the **package** `skills/business-de` (`packages["business-de"].path` = `skills/business-de`, 26 skill paths under it) |
| `README.md` | one match at line 32 — the `business-de/` entry in the `skills/` layout tree. **Not stale:** it names the canonical package inside the `skills/` block. The comment this table quoted for line 19 ("canonical copy under skills/business-de/") is not in the current README — the rewrite `dbf86e2` removed it. |
| `catalog.json` | six matches, one per `ref-*` skill, of the form `(business-de/<skill>)` in the copied frontmatter description. **Stale as a path:** from the repository root the fragment resolves to nothing. Carried to G22. |

Conclusion (re-verified in the TASK-0004 VERIFY pass, 2026-10-20): the deleted top-level
`business-de/` directory is gone and no tool, test or document depends on it. The canonical copy
is `skills/business-de/` (10 SKILL.md), owned by `skills-business-de-r3`, and stays. The only
remainder is prose: six `ref-*` descriptions still spell the old path `business-de/<skill>`
(G22). The grep above was re-run on the tree of commit `d9c14aa` and reproduced exactly the
same six entries.

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
| no tracked symlink with an absolute target | `tests/hygiene/test_no_bad_symlinks.py` | PASS | PASS (fails) |
| no tracked symlink that is a self-loop | `tests/hygiene/test_no_bad_symlinks.py` | PASS | PASS (fails) |
| no tracked symlink with a dangling target | `tests/hygiene/test_no_bad_symlinks.py` | PASS | PASS (fails) |
| no tracked symlink whose target leaves the checkout | `tests/hygiene/test_no_bad_symlinks.py` | PASS | PASS (fails) |
| no tracked database/journal files | `tests/hygiene/test_no_database_files.py` | PASS | PASS (fails) |
| root entries restricted to `rootAllowlist` | `tests/hygiene/test_root_allowlist.py` | PASS | PASS (fails) |
| no tracked file above 5 MiB without a reason | `tests/hygiene/test_no_large_files.py` | PASS | PASS (fails) |
| every workspace project name is unique | `tests/hygiene/test_workspace_projects.py` | PASS | PASS (fails) |
| every internal dependency uses the workspace protocol | `tests/hygiene/test_workspace_projects.py` | PASS | PASS (fails) |
| `.npmrc` maps `@ottili` to the private registry, no public fallback | `tests/hygiene/test_npmrc_scope.py` | PASS | PASS (fails) |

- **Shared helper:** `tests/hygiene/repo_guard.py` (creates throwaway git repositories for the broken
  fixtures; never writes into the real worktree).
- **Runner:** pytest — the configured runner of the truth kit (`scripts/truth/config.json` →
  `commands.test` = `pytest -q {paths}`). The modules use nothing but the Python standard library
  and `git`.
- **Run through the kit:** `scripts/truth/heavy.sh --class build -- pytest -q tests/hygiene` →
  107 passed. The seven `*.test.mjs` files of `tests/hygiene/` and their helper were replaced by
  these pytest modules in commit `3fd5ac3`, because a `node:test` module is never collected by
  pytest — the gate would have passed a suite that never ran.
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
- **Root cause (found in the TASK-0004 VERIFY pass, 2026-10-20):** the heading was not always
  wrong. `c84cc90` (SKL-W1-02) added the section as `## Orchestrator preamble (generated)`;
  the later README rewrite `dbf86e2` ("README-1: docs: rewrite README to match the code")
  shortened it to `## Orchestrator preamble` and thereby broke the contract test. The section
  body is still complete — only the heading lost the word `(generated)`.
- **Effect while open:** the GitHub workflow step "Run orchestrator contract tests"
  stays red. The truth-kit gate is unaffected — its test command is `pytest -q {paths}`,
  and the whole pytest suite is green (44 passed).

## G12 (CLOSED in TASK-0003, 2026-10-20): engineering self-tests hard-coded `/srv/ottili` paths and wrote into the repository root

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

- **Closed in TASK-0003 (2026-10-20):** all three points are fixed inside this job's
  owned paths (see `docs/truth/REPAIR_LOG.md`, D-017, D-023, D-024):
  1. `check_contract_drift_test.py` derives the skill directory from `__file__` and
     writes its fixture into the pytest `tmp_path`; it no longer names `/srv/ottili`.
  2. `check_rls_migration_test.py` reads the hq-v2 corpus root from `OTTLI_HQ_REPO`
     (default `/srv/ottili/repo/hq-v2`) and, where the corpus is absent, proves the
     documented missing-file contract (exit 2) instead of failing on a foreign path.
  3. `run_long_test_test.sh` exports `OTTLI_TEST_LOG` into its temporary directory, so
     `long-test.log` and `long-test.log.out` no longer end up in the repository root.
- **Ownership note:** `docs/R3_OWNERS.json` lists `skills/engineering/**` under
  `skills-engineering-r3`, but the job card of SKL-W0-01 grants this job `skills/**`
  and names the two engineering self-tests as the defects of TASK-0003 ("two
  engineering self-tests ... fail"). The repairs above stay inside `skills/**` and are
  limited to the two self-tests and the log path of the third, so the change is
  reviewable in one place.

## G13 (open, TASK-0002 VERIFY, 2026-10-20): `scripts/verify-status.mjs` is fixed but still unproven against a real product `STATUS.md`

- **Fixed in this pass (both were in this job's owned paths):**
  - `raw.rstrip()` — a Python method — crashed the checker on the first table row
    (`TypeError: raw.rstrip is not a function`).
  - `require("node:fs")` inside an ES module threw a `ReferenceError` that a bare `catch`
    swallowed, so the evidence file was never checked and **every** row was reported as
    `log path not found`: a checker that could never pass.
  - Both are covered by `tests/hygiene/test_verify_status.py`; with the old file restored
    4 of its 5 tests fail, with the fix all 5 pass.
- **Changed by TASK-0004 (2026-10-20):** the product tree no longer ships a
  `STATUS.md` anywhere — the pass-by-pass status diaries were deleted (D-030 in
  `docs/truth/REPAIR_LOG.md`), because the task card of this wave asks for "one tree,
  no stale duplicate, no status diaries". The proposal below is therefore **withdrawn**:
  creating a root `STATUS.md` (TASK-0008 owns it) would contradict that decision.
- **What the checker is proven against now:** `tests/hygiene/test_verify_status.py`
  writes a claim table into a temporary tree (valid table, missing log file, missing
  claim, seeded bad row) and asserts the exit code of
  `node scripts/verify-status.mjs <table> --root <tree>`; the skill's own self-test
  `skills/engineering/honest-status/scripts/check_status_evidence_test.py` writes a
  `STATUS.md` into a temporary directory as well. The row format is
  `| <claim> | <command> | <exit code> <log path> |`. Both run in CI.
- **Status:** the gap as written no longer exists — there is no product claim table to
  check because the product deliberately has no status file. Re-open this gap only if
  the operator decides that the product should ship a claim table again; the honest
  place for such a table would then be the job's `.truth/` evidence, not the repository.

## G14 (cross-job request, TASK-0003, 2026-10-20): CI runs a shell script with `python3`

- **Observed (CI step "Run engineering skill self-tests" in `.github/workflows/validate.yml`):**
  the loop runs every entry with `python3 "$t"`, but one of the entries is a bash script:
  `skills/engineering/long-test-discipline/scripts/run_long_test_test.sh`. `python3` on that
  file exits 1 with
  `SyntaxError: invalid syntax ... set -uo pipefail`, and the step runs under
  `set -euo pipefail`, so the whole CI job is red even though the script itself passes
  (`bash .../run_long_test_test.sh` -> exit 0).
- **Ownership:** `.github/**` belongs to `skills-engineering-r3` per `docs/R3_OWNERS.json`
  and is not on this job's owned list, so this job did not edit the workflow.
- **Request (cross-job):** in `.github/workflows/validate.yml`, run the shell script with
  bash instead of python. The smallest change that keeps the loop readable is to split the
  list into two loops:
  ```bash
  for t in <the .py self-tests>; do echo "=== $t ==="; python3 "$t"; done
  for t in skills/engineering/long-test-discipline/scripts/run_long_test_test.sh; do
    echo "=== $t ==="; bash "$t"
  done
  ```
- **Effect while open:** the GitHub workflow stays red on the "Run engineering skill self-tests"
  step. The pytest suite and the truth-kit gate are unaffected - both are green.

## G15 (cross-job request, TASK-0003 VERIFY, 2026-10-20): `.gitignore` does not ignore `.pytest_cache/`

- **Observed:** a full `pytest` run creates `.pytest_cache/` in the repository
  root. The directory stays invisible to `git status --porcelain` only because
  pytest writes a `.gitignore` with `*` into it. `.gitignore` itself does not
  list `.pytest_cache/`.
- **Ownership:** `.gitignore` belongs to `skills-engineering-r3` per
  `docs/R3_OWNERS.json` and is not on this job's owned list, so this job did
  not edit it.
- **Request (cross-job):** add `.pytest_cache/` to the repository `.gitignore`.
  The current behaviour is an accident of pytest's implementation, not a
  decision of the repository, and a pytest version that stops writing that
  inner `.gitignore` would make every test run dirty the checkout.
- **Effect while open:** none today. The clean-tree guard
  (`tests/hygiene/test_clean_tree.py`) would report the new untracked
  directory and turn the suite red, so the risk is loud, not silent.

## G16 (informational, TASK-0003 VERIFY, 2026-10-20): the card's `docs/requests/` pointers cannot be created from this job

- **Observed:** `AGENTS.md` asks for a 3-line pointer in
  `docs/requests/<job>-<n>.md` for every change outside the owned paths, while
  the job card asks for the same information in `docs/gaps/SKL-W0-01.md`.
- **Conflict:** the truth gate's `ownership` step fails when a changed file
  lies outside the owned globs, and `docs/requests/**` is not in this job's
  owned list (only `docs/gaps` is). A pointer file would therefore turn the
  gate red and block the commit.
- **Decision:** the cross-job requests live in this file (G11, G14, G15). The
  pointer files were not created; the requester reads the gaps file.

## G18 (cross-job notice, TASK-0004, 2026-10-20): `docs/gaps/SKL-W1-02.md` points at the deleted status diaries

- **Observed:** `docs/gaps/SKL-W1-02.md:104-106` lists
  `skills/business-de/config/REVERIFY_2026-10-15.md`,
  `skills/business-de/config/REVERIFY_2026-10-14.md`, `skills/business-de/STATUS.md`
  and `skills/business-de/HANDOFF.md` as files of the business-de package.
- **Change:** those four files were deleted by SKL-W0-01 TASK-0004 — they were
  pass-by-pass status diaries. The canonical skills live under
  `skills/business-de/<skill>/` and are untouched; the evidence that lived in the two
  `REVERIFY_*.md` files now sits with the thing it described, in
  `skills/business-de/*/references/SOURCES.md` and in `config/versions.json`.
- **Ownership:** `docs/gaps/SKL-W1-02.md` belongs to the job SKL-W1-02, so this job did
  not edit it (a change outside the owned paths turns the truth gate red).
- **Request (cross-job):** SKL-W1-02 should update lines 104-106 to the files that
  exist today in `skills/business-de/`: `README.md`, `RESEARCH.md`, `PASS5_GATE.md`,
  `config/versions.json` and the ten skill folders.

## G19 (follow-up, TASK-0004, 2026-10-20): package-level documents that are neither status diaries nor named by the delete list

- **Observed:** the delete list of this task names `STATUS.md`, `HANDOFF*`, `GAPS*`,
  `R3_PLAN.md`, `REVERIFY*`, `EVALS.md` and `*.db`. The following committed documents
  are **not** covered by it and were therefore left in place:
  `skills/agentic-data/AUDIT.md`, `skills/agentic-data/references/PASS2-CONSOLIDATION.md`,
  `skills/agentic-data/references/PASS4-R3-02-AUDIT.md`,
  `skills/business-de/PASS5_GATE.md`, `skills/business-de/RESEARCH.md`,
  `skills/engineering/RESEARCH.md`, `skills/engineering/VERIFICATION.md`.
- **Assessment:** they are pass records and research notes — the same family as the
  diaries that were deleted — but their names are not in the delete list, so deleting
  them would exceed this task's slice. `skills/engineering/**` belongs to the
  skills-engineering lane, `skills/business-de/**` to the skills-business-de lane.
- **Follow-up:** the canonical-skills job decides per file whether it is product
  documentation (keep it and link it) or a stale diary (delete it).
  `docs/truth/REPO_SHAPE.md` lists them as the only remaining package-level documents.

## G20 (cross-job request, TASK-0004 VERIFY, 2026-10-20): `index/skills.json` drifts from the tree it is generated from

- **Observed:** `python3 scripts/build-index.py` rewrites `index/skills.json` with five changed
  lines — the `pg-rls-multitenant` description (`tenant_id/...` → `company_id/...`) and
  `has_references` for the four reference skills that have no `references/` folder
  (`ref-bank-reconciliation-camt`, `ref-gobd-archive`, `ref-ust-edge-cases`,
  `ref-xrechnung-zugferd`), which flips from `true` to `false`. `index/INDEX.md` does not drift.
- **Cause:** the sources changed without a rebuild — `8279956` (SKL-W1-01, pg-rls tenant
  convention) and `58e4e0a` / `8732c48` (SKL-W1-02, re-nesting the `ref-*` skills) touched the
  `SKILL.md` files, but the last index rebuild is `ae4e85b` (SKL-W1-02). Not caused by this job.
- **Impact:** `index/skills.json` is a generated artefact that no longer matches its inputs.
  `scripts/build-index.py` has no `--check` mode and CI never calls it, so the drift is silent.
  `catalog.json` itself is in sync (`node scripts/gen-catalog.mjs --check` → exit 0).
- **Ownership:** `index/**` belongs to `skills-engineering-r3` per `docs/R3_OWNERS.json`;
  neither `index/**` nor `scripts/build-index.py` is on this job's owned list.
- **Request (cross-job):** give `scripts/build-index.py` a `--check` mode that renders into a
  temporary directory, compares the result with `index/INDEX.md` and `index/skills.json` and
  exits 1 on a difference; call it from `.github/workflows/validate.yml` next to
  `node scripts/gen-catalog.mjs --check`; rebuild `index/` once and commit the result.
- **Effect while open:** `index/` is stale. No test and no gate step fails — the drift is
  invisible until somebody rebuilds the index by hand.

## G21 (cross-job request, TASK-0004 VERIFY, 2026-10-20): two installers do the same job

- **Observed:** `scripts/install.sh` (copy or link selected skills into an agent skills
  directory; `--check`, `--dry-run`, `--package`, `--link`, `--force`) and
  `scripts/install-skill.py` (resolve a skill by name or id in `catalog.json` and copy it into
  an agent directory) both install skills. `README.md` documents both (lines 158-167).
- **Assessment:** the task's own requirement — "one `scripts/install.sh` and one
  `scripts/validate.py`, exactly one each" — is met. The overlap between the two installers is
  the extra fact: they differ in flags and in behaviour, so a user cannot tell which one is
  authoritative.
- **Ownership:** `scripts/**` belongs to `skills-engineering-r3` per `docs/R3_OWNERS.json`;
  `scripts/install-skill.py` is not on this job's owned list.
- **Request (cross-job):** either retire `scripts/install-skill.py` in favour of
  `scripts/install.sh` (which already supports `--package`, `--check` and `--dry-run`) and
  point the README at the survivor, or state in `docs/interfaces/install.md` which one is
  authoritative and what the other is for.
- **Effect while open:** two installers, no user-visible failure.

## G22 (cross-job request, TASK-0004 VERIFY, 2026-10-20): six catalogue descriptions still carry the deleted `business-de/` path fragment

- **Observed:** the frontmatter description of the six `ref-*` skills contains the path
  fragment `business-de/<skill>`, for example
  `skills/ref-bank-reconciliation-camt/ref-bank-reconciliation-camt/SKILL.md`:
  `... skill (business-de/bank-reconciliation-camt) ...`. From the repository root that path
  does not exist; the canonical path is `skills/business-de/bank-reconciliation-camt`. The
  fragment reaches `catalog.json` (6 entries), `index/skills.json` (6 entries) and
  `index/INDEX.md` (6 rows), because the catalogue copies the frontmatter description verbatim.
- **Cause:** the descriptions were written when `business-de/` was a top-level directory. When
  the package moved under `skills/`, the prose was not updated.
- **Impact:** a reader who follows the parenthesised path lands on nothing. This is the only
  place left in the tree where the deleted duplicate is still named as a path. The directory
  itself is gone and nothing reads it.
- **Ownership:** `skills/ref-*/**` is not assigned in `docs/R3_OWNERS.json`. `catalog.json` is
  owned by this job but is generated from the `SKILL.md` files, and `index/**` is owned by
  `skills-engineering-r3` and is not on this job's owned list — so the complete fix (text +
  regenerated catalogue + regenerated index) cannot be landed inside this job's paths.
- **Request (cross-job):** in the six files
  `skills/ref-{bank-reconciliation-camt,datev-extf,gobd-archive,ust-edge-cases,webhooks-safe,xrechnung-zugferd}/<same-name>/SKILL.md`
  replace `business-de/` with `skills/business-de/` in the `description:` frontmatter, then run
  `node scripts/gen-catalog.mjs` and `python3 scripts/build-index.py` and commit all three.
- **Effect while open:** six stale path fragments in prose. No test fails; the deletion of the
  top-level `business-de/` itself is complete and unblocked.

## G23 (cross-job request, TASK-0004 VERIFY, 2026-10-20): committed test output is catalogued as skill content

- **Observed:** ten committed files under `skills/business-de/*/tests/tmp/` are leftovers of
  test runs: `bank-reconciliation-camt/tests/tmp/{nearmiss,r}.json`,
  `skr-journal-mapping/tests/tmp/{dbg,empty,j,nearmiss}.json`, `skr-journal-mapping/tests/tmp/j.csv`,
  `ust-edge-cases/tests/tmp/{inv,nearmiss}.json` and `xrechnung-zugferd/tests/tmp/.gitkeep`.
  Because the catalogue generator lists every file of a skill directory, all of them appear
  in `catalog.json` under `paths[]` — the catalogue advertises scratch files as part of a
  skill.
- **Impact:** no test fails, but the published catalogue is polluted and the scratch files
  are diff noise on every run of the business-de tests.
- **Ownership:** `skills/business-de/**` belongs to `skills-business-de-r3` per
  `docs/R3_OWNERS.json`; the files are not named by this task's delete list.
- **Request (cross-job):** delete the nine scratch files, keep `tests/tmp/.gitkeep` so the
  directory survives, and make the catalogue generator skip `tests/tmp/**` when it collects
  `paths[]` (`scripts/gen-catalog.mjs` is on this job's owned list, the skill folders are not).
- **Effect while open:** ten scratch files stay in the catalogue's `paths[]`.

## G24 (cross-job requests, TASK-0004 VERIFY, 2026-10-20): `scripts/validate_skills.py` checks ten of the 39 skills, and two skills ship an unlinked eval set

- **Observed 1 (scope):** `scripts/validate_skills.py` sets
  `SKILLS_DIR = .../skills/engineering`, so it validates the ten engineering skills while
  its docstring promises the rules for "every skill folder". The other 29 catalogue
  skills are never checked by it.
- **Observed 2 (crash):** the prompt count of `references/EVALS.md` is computed from
  `ev_text`, which is assigned only inside the `else` branch. If the *first* validated
  skill has no eval set, the validator dies with
  `UnboundLocalError: cannot access local variable 'ev_text'` instead of reporting a
  finding; for a later skill the variable still holds the *previous* skill's text, so the
  prompt count comes from the wrong file. Reproduced in a throwaway clone:
  `mv skills/engineering/acceptance-harness/references/EVALS.md /tmp/ev1.md &&
  python3 scripts/validate_skills.py` → traceback, exit 1.
- **Observed 3 (unlinked eval sets):** two skills ship `references/EVALS.md` but never
  link it from their `SKILL.md` — `skills/agentic-data/computer-use-drivers` and
  `skills/agentic-data/deep-research-method`. The validator's rule "references linked one
  level deep" would have caught both, if it scanned those skills.
- **Ownership:** `scripts/validate_skills.py` is not on this job's owned list;
  `skills/agentic-data/**` belongs to `skills-agentic-data-r3` per `docs/R3_OWNERS.json`.
  This job changed neither.
- **Request (cross-job, scripts lane):** in `scripts/validate_skills.py`, derive the skill
  list from the whole `skills/` tree (every package/skill directory that holds a
  `SKILL.md`) and read the eval file unconditionally —
  `ev_text = open(ev, encoding="utf-8").read() if os.path.isfile(ev) else ""` — skipping
  the prompt count when the file is absent.
- **Request (cross-job, agentic-data lane):** add a link to `references/EVALS.md` in the
  `SKILL.md` of `skills/agentic-data/computer-use-drivers` and
  `skills/agentic-data/deep-research-method`, where the other skills link their
  `references/EVALS.md`.
- **Effect while open:** the standard is enforced for ten of the 39 skills, and two eval
  sets are invisible to a reader of the skill. No test fails today; the facts that are
  checkable from this job's paths are guarded by
  `tests/hygiene/test_skill_eval_sets.py`.

## G25 (cross-job request, hq-v2 lane, 2026-10-20): two tenant tables are created without row-level security

- **Observed:** the RLS checker of this repository (read-only run against the
  product repositories, no write into `hq-v2`) reports exactly one failing file
  in a census of 120 real migrations:
  `hq-v2/modules/my-work-home/migrations/20261014150000_hq_my_work_home_r3_11_quickcreate.sql`
  creates `my_work_home_quick_create` and `my_work_home_recent` with a tenant
  policy on `company_id` but **without** `ALTER TABLE … ENABLE ROW LEVEL SECURITY`
  and **without** `ALTER TABLE … FORCE ROW LEVEL SECURITY`. The two follow-up
  migrations `20261015000000_hq_my_work_home_r3_12_quickcreate_state.sql` and
  `20261015010000_hq_my_work_home_r3_13_quickcreate_recent_lifecycle.sql` keep
  the same tables unprotected.
- **Why it matters:** without `ENABLE` the policies are not evaluated at all;
  without `FORCE` the table owner (the migration role) still bypasses RLS. Both
  tables are tenant-scoped (`company_id` + tenant policy), so this is a tenant
  isolation hole in the product, not a style question.
- **Request (patch, exact):** in the three files above, after the
  `CREATE POLICY` statement of each table, add
  `ALTER TABLE my_work_home_quick_create ENABLE ROW LEVEL SECURITY;` /
  `ALTER TABLE my_work_home_quick_create FORCE ROW LEVEL SECURITY;` and the same
  two lines for `my_work_home_recent`. The pattern is proven by
  `hq-v2/modules/reports-intelligence/migrations/20261002091600_reports_intelligence_saved_report.sql`
  (ENABLE + FORCE + policy + scoped grant).
- **Proof of the finding (this job):** `python3 skills/engineering/pg-rls-multitenant/scripts/check_rls_migration.py <file>` → exit 1 with
  `my_work_home_quick_create: missing ENABLE ROW LEVEL SECURITY` and
  `my_work_home_quick_create: missing FORCE ROW LEVEL SECURITY (owner would bypass RLS)`.
- **Ownership:** `hq-v2` belongs to the hq lanes, not to `skills-engineering-r3`.
  This job changed nothing in that repository.

## G26 (environment fact, 2026-10-20): `/srv/ottili/repo/<product>` is empty on this host

- **Observed:** the job card names `/srv/ottili/repo/hq-v2/docs/STATUS.md` and
  the skill self-test used `/srv/ottili/repo/hq-v2` as the corpus path. On this
  host `/srv/ottili/repo/<product>` contains **only** `.germo/` (the scheduler
  state) — no product code, no `docs/`, no migrations. The real product
  repositories are on the NVMe mount: `/mnt/ottili-nvme/ottili/v2/repo/<product>`
  (hq-v2, console-v2, ld3-v2, ottili-platform, ottili-apps, alran-core-v2,
  alran-clients-v2).
- **Effect:** every proof in this pass was taken against the NVMe path
  (`hq-v2` at commit `fe9a1cbbb5dff2ebee2c1e33a6844bbb818dfaff`). The committed
  tests do not read a sibling repository at all: the real excerpts were copied
  into `tests/fixtures/` with their provenance (`tests/fixtures/PROVENANCE.md`),
  and the reading of the real files stays a manual proof under `.truth/`.
- **Request (cross-job, scripts lane):** whoever owns the self-tests of the
  installed skills should stop defaulting a corpus path to `/srv/ottili/repo`
  (the file was rewritten in this pass for `pg-rls-multitenant`; other skills
  may still carry the same default).

## G27 (UNVERIFIED rung, environment, 2026-10-20): the Docker daemon is not reachable, so the leak-test harness could not be run as shipped

- **What is UNVERIFIED:** the **containerised** end-to-end rung of
  `skills/engineering/pg-rls-multitenant/scripts/pg-rls-leak-test.sh` — the part
  that pulls `postgres:18-alpine`, starts a container, applies a migration into
  it and probes it. It is **not** verified on this host.
- **Observed:** `docker info` → exit 1,
  `permission denied while trying to connect to the docker API at unix:///var/run/docker.sock`.
  The `docker` client is installed (`/usr/bin/docker`), the daemon socket is not
  reachable for this user.
- **Exact command that would close the gap** (run it on a host with a Docker
  daemon, as the user that owns the socket):
  ```
  docker run --rm --name pg-rls-leak-$$ -e POSTGRES_PASSWORD=secret \
    -e POSTGRES_USER=postgres -d postgres:18-alpine
  docker exec pg-rls-leak-$$ pg_isready -U postgres
  skills/engineering/pg-rls-multitenant/scripts/pg-rls-leak-test.sh \
    skills/engineering/pg-rls-multitenant/references/examples/good_migration.sql
  ```
  Expected: `PASS: RLS leak test green`, exit 0. With the leaky migration
  (a permissive `USING (true)` policy) the same command must print
  `FAIL: RLS leak test - block merge` and exit 1.
- **What IS verified (the same code path against real PostgreSQL):** the harness
  was run end to end against **real PostgreSQL 18.6** on this host with only the
  container runtime replaced by a local server (a `docker` shim under
  `.truth/SKL-W0-01/docker-shim/`, git-ignored, manual proof only):
  - good migration → probe output `a_sees_own 1`, `a_sees_b 0` →
    `PASS: RLS leak test green`, exit 0;
  - seeded leaky migration → probe output `a_sees_own 2`, `a_sees_b 1` →
    `FAIL: RLS leak test - block merge`, exit 1.
  So the SQL, the seeding, the role switch and the verdict are proven; what
  stays unproven is only that `docker run`/`docker exec`/`docker rm` behave the
  same way on a host with a daemon.
- **The committed test does not need Docker:** `tests/hygiene/test_leak_probe.py`
  drives the two daemon-free modes of the same script — `--print-probe-sql`
  (the probe SQL) and `--parse FILE` (the verdict) — and writes its own bad
  inputs, so the suite stays green in a clean clone.

## G28 (cross-job request, hq-v2 and ottili-apps lanes, TASK-0005 VERIFY, 2026-10-20): seven tenant tables are created without complete row-level security

- **What was found:** the RLS checker of the `pg-rls-multitenant` skill could
  not read a `DO $$ … $$` block (see `docs/truth/REPAIR_LOG.md`, D-046). The
  blind scanner therefore never reported the tables that the product
  migrations protect inside such a block. With the scanner repaired, the
  checker reports **seven real holes** in the product repositories. This job
  does not write into `hq-v2` or `ottili-apps`; the fix belongs to the lane
  that owns them.
- **The exact findings** (checker:
  `python3 skills/engineering/pg-rls-multitenant/scripts/check_rls_migration.py <file>`;
  every path is relative to the repository root of the product repository):

  | Repository | Migration | Table | Finding |
  |---|---|---|---|
  | `hq-v2` | `modules/accounting-gl/migrations/20261010120000_hq_accounting_gl_r3_14_approval.sql` | `approval_rule` | missing FORCE ROW LEVEL SECURITY |
  | `hq-v2` | `modules/accounting-gl/migrations/20261010120000_hq_accounting_gl_r3_14_approval.sql` | `audit_receipt` | missing FORCE ROW LEVEL SECURITY |
  | `hq-v2` | `modules/accounting-gl/migrations/20261011000000_hq_accounting_gl_r3_20_account.sql` | `account` | no CREATE POLICY for tenant isolation |
  | `hq-v2` | `modules/collections/migrations/20261014190310_hq_collections_r3_10.sql` | `collections_dispute` | missing FORCE ROW LEVEL SECURITY |
  | `hq-v2` | `modules/my-work-home/migrations/20261014150000_hq_my_work_home_r3_11_quickcreate.sql` | `my_work_home_quick_create`, `my_work_home_recent` | missing ENABLE **and** FORCE ROW LEVEL SECURITY (already reported as G25) |
  | `hq-v2` | `modules/reports-intelligence/migrations/20261008000001_reports_intelligence_catalogue_run.sql` | `reports_intelligence_catalogue_run_entry` | missing ENABLE ROW LEVEL SECURITY |
  | `hq-v2` | `modules/shipping-core/migrations/20261014120000_hq_shipping_core_r3_10.sql` | `tracking_notification` | missing ENABLE and FORCE, no CREATE POLICY |
  | `ottili-apps` | `apps/hq/mail-calendar/migrations/20261014180000_mail-calendar_024_freebusy.sql` | `calendar_freebusy_window`, `calendar_recurrence_instance` | missing FORCE ROW LEVEL SECURITY |

- **Why "missing FORCE" is a hole:** `ENABLE ROW LEVEL SECURITY` alone leaves
  the table **owner** (the migration role) unbound by the policy — the owner
  bypasses RLS by default. `FORCE ROW LEVEL SECURITY` removes that bypass.
  A table with no policy at all is the other half of the same hole: with
  `FORCE` and no policy, the application role sees no row either.
- **How to reproduce the whole list:**
  ```
  R=/mnt/ottili-nvme/ottili/v2/repo
  find $R/hq-v2 $R/console-v2 $R/ottili-apps -type f -name '*.sql' \
    -not -path '*/.truth/*' -not -path '*/dist/*' -not -path '*/node_modules/*' \
    -not -path '*/test/*' -not -path '*/tests/*' -not -path '*/fixtures/*' | sort > /tmp/census.txt
  python3 skills/engineering/pg-rls-multitenant/scripts/check_rls_migration.py \
    --json $(cat /tmp/census.txt | tr '\n' ' ') \
    | python3 -c 'import json,sys; [print(r["file"], r["findings"]) for r in json.load(sys.stdin)["reports"] if r["findings"]]'
  ```
  1389 migrations, 8 files with findings: the seven above and G30.

## G29 (cross-job request, hq-v2 lane, TASK-0005 VERIFY, 2026-10-20): a committed migration ends in a statement PostgreSQL cannot parse

- **What was found:** `hq-v2/modules/accounting-gl/migrations/20261007130000_hq_accounting_gl_r3_01.sql`
  ends with
  ```sql
  CREATE TABLE `evil` (id uuid);
  ```
  Backticks are not valid PostgreSQL. The statement is a syntax error, so the
  migration aborts (and with `ON_ERROR_STOP` every later file of the plan
  aborts with it).
- **Proof** (real PostgreSQL 18.6, not a parser):
  ```
  psql "postgres://postgres@127.0.0.1:15433/postgres" -c "CREATE TABLE \`evil\` (id uuid);"
  ERROR:  syntax error at or near "`"
  LINE 1: CREATE TABLE `evil` (id uuid);
                       ^
  ```
  The line is committed upstream (`git log` of the file:
  `4b4f624ac wip: autosave 2026-10-16T19:57:12Z`), not a local edit.
- **Why it is in this log:** the RLS checker of this repository ignores the
  statement (a backticked name is not a SQL identifier, so the table is not
  read as a tenant table) and the file therefore passes the RLS check. The
  RLS check is not a SQL parser, and a file that cannot run must be found by
  the migration runner of the repository that owns it.
- **What is asked:** the `hq-v2` lane removes the line (or replaces it with
  the table the migration actually needs) and re-runs the migration plan.

## G30 (owner decision, TASK-0005 VERIFY, 2026-10-20): the tenant rule does not model a deliberately global table

- **What was found:** the checker requires every table a migration creates to
  carry `company_id`, `ENABLE` + `FORCE ROW LEVEL SECURITY` and a tenant
  policy. `console-v2/modules/integrations-credentials/migrations/20261012000002_console-integrations-credentials-r3_002.sql`
  creates `integrations_credentials_provider_catalog`, and the file says why
  the table has no tenant column:
  > "`integrations_credentials_provider_catalog` — the catalogue. Global, no
  > `company_id` … It has no `company_id` column by design: every company
  > sees the same … The catalogue is global, so its policy reads `true`, not
  > `app.company_id`."

  The checker therefore reports two findings on a table that is deliberately
  not tenant-scoped.
- **Why this job does not "fix" it:** the two ways out are an owner decision.
  Either
  1. the tenant rule stays strict and a repository declares its global tables
     in the configuration of the checker (an empty `global_tables` list by
     default — no exemption is declared by this job), or
  2. the rule learns "a table without a tenant discriminator is global" —
     which weakens the rule for a table that holds tenant data under a
     different column name (`tenant_id`, `tenant_key`, `workspace_id`).
  This job does not take that decision; it ships the strict rule and records
  the case.
- **What is proven now:** the finding is on exactly one file of the 1389
  migrations of the census (G28) and it is the **only** remaining finding
  that is not a real hole.

## G31 (CLOSED in TASK-0006 VERIFY, 2026-10-20): the two commands of the pack-v3 decision that did not run now run unchanged

- **What the decision asks:** the config of the truth kit carries
  `install "bash scripts/install.sh --check"`, `build` and `lint`
  `"python3 -I scripts/validate.py --everywhere"` and `test "pytest -q {paths}"`.
- **What was found (measured before anything was written):** two of those command strings failed
  in this repository:
  ```
  bash scripts/install.sh --check
  error: --target is required                    # exit 2
  pytest -q tests/orchestrator/test_gen_preamble.test.mjs
  ERROR: not found: .../tests/orchestrator/test_gen_preamble.test.mjs
  (no match in any of [<Package orchestrator>])  # exit 4
  ```
- **Root cause 1 - `scripts/install.sh`:** the installer demanded `--target` even in `--check`
  mode, so the install command of the decision could not be the install command of the gate.
- **Root cause 2 - the test files:** the test files of `tests/orchestrator/` and `tests/reviews/`
  were Node 22 `node:test` modules (`*.test.mjs`). The gate collects the *changed* test files
  and hands them to `pytest -q {paths}`; pytest cannot collect a `*.test.mjs` path (exit 4), so
  every commit that touched one of them would have failed the gate. The workaround of the
  previous pass (a shell filter in the config) hid the defect instead of fixing it.
- **What this pass did (the code, not the expectation):**
  1. `scripts/install.sh --check` works without `--target` now: it verifies every skill folder of
     every package against a scratch directory (`${TMPDIR:-/tmp}/ottili-install-check`) that is
     never created. Regression tests: `tests/hygiene/test_install.py`.
  2. the six `*.test.mjs` modules of `tests/orchestrator/` and `tests/reviews/` were converted to
     pytest modules (`test_*.py`) with the same assertions - all six were green under `node --test`
     before the conversion, and every pytest conversion is green.
  3. `scripts/truth/config.json` now carries the decision's command strings unchanged:
     `install "bash scripts/install.sh --check"`, `build` and `lint`
     `"python3 -I scripts/validate.py --everywhere"`, `test "pytest -q {paths}"`.
     The catalogue guard is not lost: `scripts/validate.py --everywhere` cross-checks the generated
     catalogue against the `skills/` folders, and `tests/hygiene/test_catalog.py` compares the
     regenerated catalogue byte-for-byte with the committed one.
- **Measured after the fix:** `bash scripts/install.sh --check` -> exit 0 (39 skills verified,
  nothing written); `python3 -I scripts/validate.py --everywhere` -> exit 0; `pytest -q <changed
  test paths>` -> exit 0; trunk gate -> install/build/lint `PASS`, typecheck/migrate/boot/smoke
  `skip` (as task 8 expects), hygiene `PASS` (15 root entries, all allowed).

## G32 (cross-job request, TASK-0006 VERIFY, 2026-10-20): the CI workflow and the README still glob the deleted `*.test.mjs` test files

- **Owner:** `.github/workflows/validate.yml` and `README.md` belong to `skills-engineering-r3`
  (`docs/R3_OWNERS.json`), but they are outside the owned paths of this job card - the gate
  rejects a commit that changes a file outside them. This job therefore does not change them.
- **What breaks (measured after the deletion, on this tree):** the CI step
  "Run orchestrator contract tests" and the README block "Node suites" both glob
  `tests/orchestrator/*.test.mjs`. With no matching file, bash (without `nullglob`) hands the
  literal pattern to `node`:
  ```
  === tests/orchestrator/*.test.mjs ===
  node:internal/modules/cjs/loader: ... MODULE_NOT_FOUND
  CI STEP EXIT: 1
  ```
  The README block was already red before this pass, because the previous pass deleted
  `tests/hygiene/*.test.mjs` (commit `3fd5ac3`) and that glob no longer matched either.
- **The exact patch (one step in the workflow, two lines in the README):**
  ```yaml
        - name: Run orchestrator contract tests
          run: |
            set -euo pipefail
            for t in tests/orchestrator/*.test.mjs; do
              echo "=== $t ==="
              node "$t"
            done
  ```
  becomes
  ```yaml
        - name: Run orchestrator contract tests
          run: |
            set -euo pipefail
            python3 -m pytest -q tests/orchestrator tests/reviews
  ```
  and in `README.md` (section "Run the tests") step 7 becomes
  `7. the orchestrator contract tests, `python3 -m pytest -q tests/orchestrator tests/reviews``
  while the local block
  ```
  # Node suites (node:test - no test runner to install).
  for t in tests/orchestrator/*.test.mjs; do node "$t" || exit 1; done
  for t in tests/hygiene/*.test.mjs tests/reviews/*.test.mjs; do node "$t" || exit 1; done
  ```
  becomes
  ```
  # Python suites (pytest - the configured runner of the truth kit).
  python3 -m pytest -q tests/orchestrator tests/reviews tests/hygiene
  ```
- **Why it is not done here:** `README.md` and `.github/**` are not in the owned paths of the job
  card of SKL-W0-01, and the gate's ownership step fails a commit that touches a path outside
  them. The request is recorded here and in `docs/truth/REPAIR_LOG.md`.

## G33 (cross-job request, TASK-0007, 2026-10-20): the repair log records the defects that are still open outside the owned paths

- **What was done:** the repair log of this job (`docs/truth/REPAIR_LOG.md`) now carries an
  index of every defect of SKL-W0-01 — symptom, reproduction command, root cause, the files
  that carry the fix, a proof command that passes on the current trunk and the date — plus
  a section "Follow-ups for later trunk repair jobs" with the 14 items that were measured
  but could not be fixed from this job. `tests/hygiene/test_repair_log.py` is the guard: it
  fails when a defect id is not in the index, when an id names two defects, when an index
  entry lacks one of the six fields, when a proof command is missing from the proof block, when
  the command an index entry writes down is not the command the proof block of that label runs,
  when the narrative of a defect and its index entry disagree about the proof label or the
  date, when a follow-up item names no symptom, or when a proof command marked `# auto` no
  longer exits 0. The VERIFY pass of TASK-0007 found four defects in that guard itself
  (D-055, D-056, D-057, D-058), all of them fixed in the owned paths of this job.
- **The open items, by owner** (path and exact symptom in
  `docs/truth/REPAIR_LOG.md`, section "Follow-ups for later trunk repair jobs"):
  - `skills-engineering-r3`: `.github/workflows/validate.yml:42` (the `*.test.mjs` glob ends in
    `Cannot find module`/exit 1), `.github/workflows/validate.yml:69` (a bash script run with
    `python3` → `SyntaxError`), `README.md:221,228,229` (the deleted `*.test.mjs` commands),
    `index/skills.json` (5 lines drift, no `--check` mode), `scripts/validate_skills.py`
    (10 of 39 skills validated, `UnboundLocalError`, the prompt regex counted twice),
    `.gitignore` (no `.pytest_cache/`).
  - `skills-business-de-r3`: 9 committed scratch files under `skills/business-de/*/tests/tmp/`,
    `docs/gaps/SKL-W1-02.md:106` (points at the deleted status diaries).
  - `skills-agentic-data-r3`: two skills ship a `references/EVALS.md` their `SKILL.md` never
    links.
  - unassigned: `skills/ref-*/**` (six descriptions still carry the deleted `business-de/`
    path fragment — the tree is in no entry of `docs/R3_OWNERS.json`),
    `docs/truth/REPO_PROBE.txt` (tracked, 0 bytes).
  - operator: `scripts/truth/safe-commit.mjs` (git 2.53.0 returns nothing for
    `--untracked-files=all`, so new files stay untracked), `docs/requests/` does not exist
    although `AGENTS.md` points at it, the Docker daemon is not reachable on this host.

## G34 (follow-up, TASK-0007 VERIFY, 2026-10-20): 18 of the 33 proof commands are not re-run by the guard, and the gate diffs against the merge base

- **What was measured:** all 33 proof commands of `docs/truth/REPAIR_LOG.md` and the job gate
  were re-run on the trunk of this pass; every one of them exited 0. The transcript is
  `.truth/SKL-W0-01/after.txt`.
- **The gap:** only the 15 proof commands marked `# auto` are re-executed by
  `tests/hygiene/test_repair_log.py`. The other 18 are the slow ones (whole pytest suites, the
  job gate) and the gate runs `pytest -q {paths}` over the *changed* test files only, so a slow
  proof command can rot without any suite noticing. Running them inside the guard is not
  possible without recursion, because P31 runs `python3 -m pytest tests/hygiene/ -q`, which is
  the guard itself. The right place is a runner that executes the slow proofs once per trunk,
  outside the suite.
- **The second half:** `scripts/truth/gate.mjs` computes its diff against
  `git merge-base HEAD main`. After a commit of this job is integrated that base is the commit
  itself, so the next gate run reports `no changes inside the owned paths: nothing was built`
  and `no test file (*.test.mjs / *.test.ts / test_*.py ...) was added or changed inside the
  owned paths: a job without tests is not done`, and fails, even when the tree is correct. A job
  that only documents something therefore has to change a test file to get a green gate.
- **Why it is not done here:** the kit (`scripts/truth/**`) belongs to the operator and may not
  be edited by a job; the guard of this job cannot run the slow proofs without recursion.
  Both facts are recorded in `docs/truth/REPAIR_LOG.md`, section "Follow-ups for later trunk
  repair jobs", items 15 and 16.

## G35 (cross-job request, TASK-0008 review, 2026-10-20): the preamble prints check commands whose scripts live in other skills

- **What was measured:** `skills/orchestrator-preamble/orchestrator-preamble/SKILL.md:35`
  and the generated `references/preamble.md` print
  `python3 scripts/check_problem_catalogue.py ...`,
  `python3 scripts/check_rls_migration.py ...`,
  `python3 scripts/check_outbox.py ...` and
  `python3 scripts/check_status_evidence.py ...`. Those scripts exist only inside the
  canonical engineering skills
  (`skills/engineering/{problem-json-contracts,pg-rls-multitenant,outbox-idempotency,honest-status}/scripts/`).
  A reader who copies the command into the preamble folder gets
  `No such file or directory` (exit 1); neither document says in which folder the
  command has to run.
- **Why it is not fixed here:** `scripts/gen-preamble.mjs` pins the gate command of the
  four canonical skills verbatim (it refuses to run when a skill no longer contains the
  string) and writes them into the preamble. The generator is outside the owned paths of
  SKL-W0-01 (`scripts/install.sh`, `scripts/validate.py`, `scripts/gen-catalog.mjs`,
  `scripts/verify-status.mjs`, `scripts/truth/config.json`), and the preamble itself is
  the subject of the W1 job `SKL-W1-02`. Changing the generated text by hand would be
  undone by the next `node scripts/gen-preamble.mjs`.
- **The request:** let the generator print the command with the folder it runs in (for
  example `skills/engineering/pg-rls-multitenant/scripts/check_rls_migration.py
  <migration.sql>`) or print the sentence "run this in the folder of the skill that owns
  the script". The same change belongs into the human-readable contract
  `skills/orchestrator-preamble/orchestrator-preamble/SKILL.md`.
- **The proof that exists today:** `tests/hygiene/test_skill_docs.py` resolves every
  script a SKILL.md names; it is green because it accepts a script of a sibling skill.
  It does NOT decide in which folder the command runs — that is the open question of this
  entry.

## G36 (follow-up, TASK-0008 review, 2026-10-20): the lint step of the truth gate is the build step

- **What was measured:** `scripts/truth/config.json` sets `commands.build` and
  `commands.lint` to the same command (`python3 -I scripts/validate.py --everywhere`).
  The trunk gate therefore reports `lint: pass` whenever the build passes; a lint
  regression cannot be seen by the gate. A real linter is installed on this host —
  `ruff` 0.16.8 at `/usr/local/bin/ruff` — and it reports 23 findings in `tests/` and 8
  in `scripts/`. The findings in `tests/` are inside the owned paths of this job, the
  findings in `scripts/validate_skills.py`, `scripts/build-index.py`,
  `scripts/check_related_graph.py`, `scripts/install-skill.py` and
  `scripts/validate_reviewed_by.py` are not.
- **Why it is not changed here:** the pack-v3 decision fixes the command strings of
  `scripts/truth/config.json` to the ones that are measured, and a trunk gate that
  depends on a binary the CI image may not carry would turn the W1 jobs red on a host
  that has no `ruff`. The change belongs to the operator (the config) together with the
  job that owns `scripts/**` (the findings).
- **The request:** decide whether `commands.lint` becomes `ruff check` (and then make
  the CI image carry `ruff`), or keep the current command and rename the step so that it
  does not claim to be a lint.

## G37 (cross-job notice, TASK-0008 second pass, 2026-10-20): what the next job has to do when it adds a skill

- **What was measured:** a clean clone of the trunk, one skill folder added under
  `skills/engineering/`, `node scripts/gen-catalog.mjs` — the state the W1
  canonical-skills job starts from — and then the whole suite. **Five** tests went
  red. One of them was the shape guard of `docs/truth/REPO_SHAPE.md` ("Skills in the
  catalogue: document says 39, command says 40"), a failure the next job cannot fix
  because it does not own `docs/truth/`; that one is closed by D-066 of this pass. The
  other four are the next job's own obligations and are listed here so that it does
  not have to discover them one at a time:
  1. `tests/hygiene/test_skill_eval_sets.py` — an engineering skill must ship
     `references/EVALS.md` (the eval set of the skill).
  2. `tests/hygiene/test_skill_docs.py` — `scripts/validate_skills.py` exits 1 and
     reports four findings for the new skill: the description lacks a
     "when to use" trigger, the frontmatter carries the non-portable field
     `version`, `references/EVALS.md` is missing, `references/SOURCES.md` is
     missing. The two of the four that the documentation of the skill does not
     mention are the sources of the skill.
  3. and 4. `tests/hygiene/test_repair_log.py` — the proof commands P38 and P40 of
     the repair log re-run the two suites above, so they turn red with them.
- **The recipe, measured:** add the skill folder, write a description that says
  *when to use* it, keep the frontmatter to the portable fields (no `version`), ship
  `references/EVALS.md` and `references/SOURCES.md`, regenerate the catalogue with
  `node scripts/gen-catalog.mjs` and commit `catalog.json` with the skill. After
  that the suite of the job is green — the shape guard included.
- **What the next job does NOT have to do:** the counts of `docs/truth/REPO_SHAPE.md`
  are a **snapshot** at commit `9390db6` since D-066, and the live rows of that
  document (one installer, one validator, no duplicate skill name, no status diary,
  no root entry outside the allowlist, no skill missing from the catalogue) hold in
  every healthy checkout. The document no longer needs an update for a new skill.
