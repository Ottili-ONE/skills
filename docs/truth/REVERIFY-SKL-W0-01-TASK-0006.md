# REVERIFY — SKL-W0-01 TASK-0006 (repository invariants as tests)

Verification date: 2026-10-16. Scope: `tests/hygiene/*.test.mjs` + `_fixture.mjs`.

## Method

1. `git log --oneline -15` — confirmed the TASK-0006 commits from the prior pass
   (`c2efd8e` … `641247e`) are present on `main`.
2. Ran every test module against the **real** repository and confirmed each
   broken-fixture assertion actually **fails** on a throwaway git repository.
3. Re-derived the ground truth independently with `git ls-files`, `stat`,
   `readlink`, `ls` — not from the tests' own output.

## Ground truth (independent of the tests)

| Check | Command | Result |
|---|---|---|
| tracked root entries | `git ls-files \| awk -F/ '{print $1}' \| sort -u` | `.github .gitignore .npmrc AGENTS.md CONTRIBUTING.md LICENSE README.md catalog.json docs index schema scripts skills templates tests` — all 15 in `rootAllowlist` |
| tracked symlinks | `git ls-files \| while read f; do [ -L "$f" ] …` | none |
| tracked files > 5 MiB | `git ls-files \| while read f; do stat …` | none |
| tracked db/journal artefacts | `git ls-files \| grep -E '…(db\|sqlite\|journal)…'` | none |
| tracked package.json | `git ls-files \| grep 'package.json$'` | none — the workspace-protocol invariant is **vacuously** true here |
| `skills/` top-level folders | `ls -d skills/*/` | agentic-data, business-de, community, core, curated, engineering, ottili-ai — 7 packages, 32 skills, no duplicate names |
| `.npmrc` scope | `cat .npmrc` | exactly one `@ottili:registry=${OTTILI_REGISTRY_URL:-http://127.0.0.1:18873}`, no npmjs.org fallback |

## Test results

| Module | real repo | broken fixture fails |
|---|---|---|
| `no-bad-symlinks.test.mjs` | 3/3 PASS | 3/3 FAIL-as-expected |
| `no-database-files.test.mjs` | 1/1 PASS | 5/5 FAIL-as-expected |
| `no-large-files.test.mjs` | 1/1 PASS | 1/1 FAIL-as-expected |
| `npmrc-scope.test.mjs` | 1/1 PASS | 2/2 FAIL-as-expected |
| `root-allowlist.test.mjs` | 1/1 PASS | 2/2 FAIL-as-expected |
| `unique-projects.test.mjs` | 1/1 PASS | 1/1 FAIL-as-expected |
| `workspace-protocol.test.mjs` | 1/1 PASS | 2/2 FAIL-as-expected |

`node tests/hygiene/clean-tree.test.mjs` exits 1, but only because of three
**pre-existing** entries that belong to other jobs and were present before this
pass (see GAPS G5). No test in TASK-0006 writes into the real worktree — every
broken fixture is created with `mkdtemp` under `/tmp` and removed in a `finally`
block. Re-running the full suite leaves exactly those three pre-existing entries.

## Gaps carried forward

- **G1 (blocking, cross-job):** `scripts/truth/{preflight,gate,safe-commit,db,port}.mjs`
  and `scripts/truth/heavy.sh` do not exist in this repo. The job card's
  blocked-check / gate / commit-and-land commands cannot be executed as written.
  All verification in this pass therefore used `node …` and `git …` directly.
- **G5 (pre-existing):** `M skills/agentic-data/…/report_test.json`,
  `?? docs/truth/REPO_PROBE.txt`, `?? scripts/verify-status.mjs` dirty the tree
  before any TASK-0006 test runs. Not owned by SKL-W0-01.
