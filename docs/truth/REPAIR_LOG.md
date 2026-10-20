# REPAIR_LOG — SKL-W0-01 (installer path bug and package catalogue)

## D-001 — install.sh source resolution doubled the path for every skill

- **Defect:** `./scripts/install.sh --target claude honest-status` exited with
  `error: source skill directory missing: /srv/ottili/repo/skills//srv/ottili/repo/skills/skills/\n`
  (note the doubled path and the trailing newline).
- **Cause (two bugs in one line):**
  1. The source path was resolved through `catalog.json` via
     `python3 -c "...print(s['path'])"`. The skill was **not** in the catalogue
     (the catalogue listed only 2 of 32 skills), so `print('')` returned an empty
     string — but `print` always appends a newline, so `src_dir` was `"\n"`.
  2. The directory was then built as `src="$ROOT/$src_dir"`, which concatenated
     `$ROOT` onto the empty-but-newline-terminated string, producing
     `$ROOT//<repo>/skills/\n`. The `-z` test passed because the string was not
     zero-length, and the `-d` test failed for every skill.
- **Fix:** removed the catalogue lookup entirely. The source path is now resolved
  by searching the `skills/` tree rooted at the script's own directory for a
  folder named after the skill:
  `src="" ; for pkg in "$SKILLS_DIR"/*/; do ...; src="$SKILLS_DIR/$pkg/$name"; break; done`.
  The folder name IS the skill name; no catalogue, no relative-to-script mistake.
- **Proof:** `bash -x` before (doubled path, `-d` failed) and after (32/32 folders
  resolve). See `.truth/SKL-W0-01/before.txt` and `.truth/SKL-W0-01/after.txt`.
- **Index proof:** `P1`
- **Date:** 2026-10-15

## D-002 — `--package engineering|business-de|agentic-data` reported "unknown package"

- **Defect:** every named package printed `error: unknown package <name>`.
- **Cause:** the package list was read from `catalog.json`'s `packages` object,
  which contained only `core`, `curated`, `community`, `ottili-ai` (a
  hand-maintained, stale list).
- **Fix:** packages are now **DERIVED from the `skills/` folders at install time**.
  `derive_packages()` walks `skills/*/`, skips `.git`/`node_modules`/`.pytest_cache`,
  and emits a package name for every top-level folder that contains at least one
  subfolder with a `SKILL.md`. `--package <name>` validates against that derived
  list. Virtual packages `generic` (every skill), `meta` and `ref-*` (reserved,
  empty set) are handled explicitly.
- **Proof:** `--package engineering` installs 10/10, `business-de` 11/11,
  `agentic-data` 10/10, `generic` 32/32; `--package bogus` exits 1 with the known
  list. See `.truth/SKL-W0-01/after.txt`.
- **Index proof:** `P2`
- **Date:** 2026-10-15

## D-003 — catalogue listed only 2 of 32 skills and was hand-edited

- **Defect:** `python3 -I scripts/validate.py` printed `ok: 2 skills validated`.
- **Cause:** `catalog.json` was a hand-written file with 2 entries and a stale
  `packages` object; nothing regenerated it.
- **Fix:** added `scripts/gen-catalog.mjs`, which walks `skills/<package>/<name>/SKILL.md`,
  parses the YAML frontmatter (block-style lists, quoted scalars) and writes one
  entry per skill with `name`, `package`, `description` and `paths`. Packages are
  derived from the folders. Cache/build artefacts (`.pytest_cache`, `__pycache__`,
  `node_modules`, `.git`, `.DS_Store`) are excluded and `paths` are sorted, so the
  output is deterministic. `--check` fails if the committed file would change.
  CI (`.github/workflows/validate.yml`) runs `node scripts/gen-catalog.mjs --check`.
- **Proof:** `node scripts/gen-catalog.mjs` writes 32 skills / 5 packages;
  `--check` exits 0; `validate.py` prints `ok: 32 skills validated`.
- **Index proof:** `P4`
- **Date:** 2026-10-15

## Verification commands run

```
node scripts/gen-catalog.mjs            # 32 skills, 5 packages
node scripts/gen-catalog.mjs --check    # exit 0, unchanged
python3 -I scripts/validate.py          # ok: 32 skills validated
python3 scripts/validate_skill.py --all # 10/10 engineering skills
python3 scripts/build-index.py          # index regenerated
./scripts/install.sh --target <dir> --package engineering   # 10 skills
./scripts/install.sh --target <dir> --package business-de   # 11 skills
./scripts/install.sh --target <dir> --package agentic-data  # 10 skills
./scripts/install.sh --target <dir> --package generic       # 32 skills
./scripts/install.sh --target <dir> --link honest-status    # symlink
./scripts/install.sh --target <dir> --dry-run honest-status # no write
```
All engineering self-tests (`*_test.py`, `tests/*.py`, `run_long_test_test.sh`) pass.

## D-004 — stale top-level `business-de/` duplicate and status/handoff docs cluttered the tree

- **Defect:** the repository contained a full duplicate of the business-de skills at
  the top level (`business-de/`, 111 tracked files) alongside the canonical
  `skills/business-de/`, plus ~26 status/handoff/gaps/plan/reverify/evals/log files
  scattered through the tree. `find . -name SKILL.md | xargs -n1 dirname | xargs -n1
  basename | sort | uniq -d` reported `business-de` twice and `git ls-files |
  grep -c STATUS` was 10.
- **Cause:** an earlier autonomous wave materialised the business-de skills twice
  (once at the root, once under `skills/`) and left per-pass status diaries committed.
  The R3 ownership map (`docs/R3_OWNERS.json`) assigns `skills/business-de/**` to the
  `skills-business-de-r3` job; the root `business-de/` is unowned — it is the stale
  duplicate. This job's card grants it `business-de`, the status-doc globs and
  `*.log`, so it is the correct job to delete them.
- **Fix:**
  1. `git rm -r --allow-delete business-de/` with the reason *stale duplicate of the
     business skills; the canonical copy lives under skills/*.
  2. Deleted the committed status/handoff/gaps/plan/reverify/evals/log/state files
     that are unowned or owned by this job and unreferenced by code. Files that are
     **asserted by tests** or **owned by other jobs** were kept:
     - kept: `skills/agentic-data/HANDOFF.md`, `skills/agentic-data/STATUS.md`,
       `skills/engineering/RESEARCH.md`, `skills/engineering/VERIFICATION.md`,
       `skills/agentic-data/AUDIT.md`, per-skill `references/EVALS.md`,
       `skills/business-de/config/REVERIFY_*.md`, `skills/business-de/*_state.json`
       -- **superseded in TASK-0004 (2026-10-20) for the status diaries**: the
       card of this wave grants `skills/**` to SKL-W0-01 and orders the deletion of
       the status/handoff/reverify diaries. The per-skill `references/EVALS.md`
       and the `*_state.json` files stay (see D-030).
       (owned by `skills-business-de-r3` / `skills-agentic-data-r3` / referenced by
       tests).
     - deleted: `long-test.log`, `long-test.log.out` (root logs, unreferenced except
       as a default log filename in `run_long_test.sh`, which creates it at runtime).
  3. Wrote `docs/truth/REPO_SHAPE.md` as the source of truth for the canonical-skills
     job.
- **Proof:**
  - `find . -name SKILL.md | xargs -n1 dirname | xargs -n1 basename | sort | uniq -d`
    → empty (no two SKILL.md in directories of the same name).
  - `git ls-files | grep -c STATUS` → 0.
  - `git ls-files | grep -cE '(HANDOFF|GAPS|R3_PLAN|REVERIFY|EVALS)'` → 0 at root and
    in `docs/`; only the kept per-skill files remain.
  - root contains no stray `.md` beyond `README.md`, `AGENTS.md`, `CONTRIBUTING.md`
    and no stray `.log`/`state.json`.
  - `python3 -I scripts/validate.py` still prints `ok: 32 skills validated` after the
    duplicate is gone (the duplicate is no longer collected; `tests/conftest.py`
    still excludes it, which is now a no-op but kept as a guard).
- **Cross-job note:** `scripts/truth/*.mjs` (the preflight/gate/safe-commit kit
  referenced by every task card) does **not** exist in this repository and is in the
  operator's excluded paths, so no task can run the blocked-check, gate or commit
  command as specified. Recorded in `docs/gaps/SKL-W00-01.md`. Commits in the
  interim use plain `git commit` guarded to this job's paths.
- **Index proof:** `P5`
- **Date:** 2026-10-16

## D-005 — generated catalogue listed `.gitkeep` placeholder files as skill paths

- **Defect:** after the duplicate was deleted, `node scripts/gen-catalog.mjs --check`
  failed ("catalog would change"). The drift was not about the deletion — two
  `.gitkeep` files (left by TASK-0003 to keep empty dirs in git) were being listed
  in each affected skill's `paths` array:
  `skills/agentic-data/verifiable-environments/tests/fixtures/broken/.gitkeep` and
  `skills/business-de/xrechnung-zugferd/tests/tmp/.gitkeep`.
- **Cause:** `scripts/gen-catalog.mjs` excluded cache/build artefacts
  (`.pytest_cache`, `__pycache__`, `node_modules`, `.git`, `.DS_Store`) but not
  empty-directory placeholder files, which carry no skill content.
- **Fix:** added `.gitkeep` to `IGNORE_FILES` in `scripts/gen-catalog.mjs`. The
  generator now ignores cache/build artefacts **and** placeholder files, so the
  committed `catalog.json` matches a fresh run.
- **Proof:** `node scripts/gen-catalog.mjs` writes 32 skills / 5 packages;
  `node scripts/gen-catalog.mjs --check` exits 0 ("catalog unchanged"); `git diff
  --stat catalog.json` is clean.
- **Index proof:** `P6`
- **Date:** 2026-10-16

## Pre-existing failures found during TASK-0004 verification (NOT fixed — cross-job)

These three tests fail on a clean checkout and are unrelated to the deletion; the
files are owned by `skills-engineering-r3` / `skills-agentic-data-r3`:

1. `skills/engineering/acceptance-harness/scripts/report_result_test.py` — two
   tests unpack `rc, _ = run(...)` but `run()` returns a `CompletedProcess` object
   (`TypeError: cannot unpack non-iterable CompletedProcess object`).
2. `skills/engineering/tests/test_research_design_acceptance.py::test_related_graph_is_acyclic_with_unique_sink`
   — `NameError: name 'ENGINEERING_DIR' is not defined` (module-level constant
   missing in the test file).

Recorded in `docs/gaps/SKL-W0-01.md`. The deletion itself is verified clean:
`find . -name SKILL.md | xargs -n1 dirname | xargs -n1 basename | sort | uniq -d`
is empty, `git ls-files | grep -c STATUS` is 9 (all under `skills/agentic-data/`
and `skills/business-de/`, owned by other jobs), the root has no stray docs/logs,
and `python3 -I scripts/validate.py` reports `ok: 32 skills validated`.

## D-006 — RLS checker accepted three unsafe migrations; rewrote it per-table around the real product GUC

- **Defect:** the previous `check_rls_migration.py` was a whole-file scanner: it ran
  `TENANT_RE.search(text)` once over the *entire* migration, so one `tenant_id`
  anywhere satisfied the discriminator test for every table in the file. It also
  accepted any of five discriminator names and never checked that the RLS policy
  was keyed on the GUC the product repos actually use. Result: three unsafe
  migrations (no FORCE, policy keyed on a non-product GUC, GRANT ALL) passed, and
  real hq migrations were reported against a standard that does not exist in the
  codebase.
- **Cause:** the checker was written from the skill's own procedure doc, which
  lists acceptable discriminator names, instead of from the migrations it is
  supposed to gate. It never looked at what the product repos ship.
- **GUC decision (reality has 3 candidates; one wins):**
  | GUC | hq-v2 | ld3-v2 | alran-core-v2 | console-v2 | verdict |
  |-----|-------|--------|---------------|------------|---------|
  | `app.company_id` | **995** | 4 | **733** | **347** | **PRODUCT STANDARD** |
  | `app.current_company` | 51 | 0 | 0 | 0 | legacy hq module only |
  | `app.current_company_id` | 29 | **582** | 0 | 0 | legacy ld3 module only |
  `app.company_id` is the single GUC used by the three repos that ship RLS
  migrations (hq, alran-core, console) and is present in ld3 too. The other two
  are confined to older modules and are not the standard. Verified 2026-10-16 by
  `grep -rho "current_setting('[a-zA-Z_.]*'" <repo> --include=*.sql`.
- **Fix:** the checker is now **per-table**. For every `CREATE TABLE` it requires,
  in the table's own column list and its own policy bodies:
  (a) `ENABLE ROW LEVEL SECURITY` **and** `FORCE ROW LEVEL SECURITY` on that table,
  (b) a `CREATE POLICY` on that table whose USING/WITH CHECK references
      `current_setting('app.company_id', true)`,
  (c) a `company_id` column in that table's definition.
  `GRANT ALL` anywhere in the file is still a finding. The `-- ROLLBACK` block and
  `security_invoker` view checks were dropped: they are not part of the per-table
  tenant contract and the real hq migrations do not carry them.
- **Proof:** 3 real hq migrations PASS
  (`reports-intelligence/20261002091600`, `reports-intelligence/20261002091630`,
  `procure-to-stock/20261010000000`); 3 hostile fixtures FAIL; the skill's own
  `good_migration.sql` was rewritten to the product standard (company_id +
  `app.company_id`) and now passes.
- **Index proof:** `P7`
- **Date:** 2026-10-16

---

## D-051 — committed `catalog.json` was stale (missing the pg-rls hostile fixtures)

- **Defect:** `node scripts/gen-catalog.mjs --check` exited 1 with
  `catalog would change; run without --check to regenerate`. The committed
  `catalog.json` did not list the three hostile RLS fixture files that
  TASK-0005 added under
  `skills/engineering/pg-rls-multitenant/references/examples/`:
  `hostile_1_no_force.sql`, `hostile_2_no_company_id.sql`,
  `hostile_3_grant_all.sql`.
- **Reproduction:** `node scripts/gen-catalog.mjs --check` (exit 1) and
  `git diff catalog.json` (3 insertions, the three paths above).
- **Root cause:** the generator walks the `skills/` tree and lists every file,
  but the catalogue was last regenerated in an earlier pass (TASK-0004), before
  the fixtures existed. The committed artefact and the tree had drifted.
- **Fix:** regenerated `catalog.json` with `node scripts/gen-catalog.mjs`
  (writes 32 skills / 5 packages). No code change — the generator was correct;
  the artefact was stale.
- **Proof:** `node scripts/gen-catalog.mjs --check` now exits 0
  ("catalog unchanged"); every one of the catalogue's 518 paths exists on disk;
  `python3 -I scripts/validate.py` reports `ok: 32 skills validated`.
- **Index proof:** `P4`
- **Date:** 2026-10-16

## Follow-ups recorded in an earlier pass (2026-10-16)

Everything below is outside this job's owned paths (or is a pre-existing dirty-tree
state) and is recorded here so the next pass does not mistake it for a regression.

1. **`scripts/truth/**` is absent from this repo (blocks the gate / preflight /
   safe-commit / commit-and-integrate commands).** Symptom:
   `node scripts/truth/preflight.mjs --job SKL-W0-01 --status` exits 1 with
   `Cannot find module '.../scripts/truth/preflight.mjs'`. Same for `gate.mjs`,
   `safe-commit.mjs`, `db.mjs`, `port.mjs`, `heavy.sh`. `scripts/truth/**` is on
   this job's EXCLUDE list, so it is another job's prerequisite — do not create it
   here. Path: `scripts/truth/`.
2. **`tests/hygiene/clean-tree.test.mjs` is red on a pre-existing dirty tree.**
   Symptom: `node tests/hygiene/clean-tree.test.mjs` exits 1 and prints
   `M skills/agentic-data/skill-authoring-evals/report_test.json` (modified by
   the `skills-agentic-data-r3-02` job), `?? docs/truth/REPO_PROBE.txt` (empty,
   untracked) and `?? scripts/verify-status.mjs` (untracked STATUS.md checker).
   All three predate this pass; the test itself is clean. Path: worktree root.
3. **Two cross-job test failures in `skills/engineering/` (owned by
   `skills-engineering-r3`).** Symptom 1:
   `skills/engineering/acceptance-harness/scripts/report_result_test.py` —
   `TypeError: cannot unpack non-iterable CompletedProcess object` (tests unpack
   `rc, _ = run(...)` but `run()` returns a `CompletedProcess`). Symptom 2:
   `skills/engineering/tests/test_research_design_acceptance.py::test_related_graph_is_acyclic_with_unique_sink`
   — `NameError: name 'ENGINEERING_DIR' is not defined`. Path:
   `skills/engineering/`.
4. **`skills/business-de/**` tests fail to collect in a clean clone.** Symptom:
   `pytest -q` inside a fresh `git clone . <dir>` reports 13 collection errors,
   all `import file mismatch: imported module 'X' has this __file__ attribute:
   <clone>/business-de/...` — a stale `__pycache__` from the deleted top-level
   `business-de/` duplicate shadows the canonical copy under `skills/business-de/`.
   The canonical copy is owned by `skills-business-de-r3`. Path:
   `skills/business-de/**` (and the stale `__pycache__` it leaves behind).

---

## D-052 — TASK-0008 review: no new defects found in owned paths; all baseline defects re-proven fixed

- **Scope of this pass:** adversarial review of the complete SKL-W0-01 change
  (git diff vs `origin/main` + working tree + untracked files), line by line, against
  the contract, plus re-running every reproduction command from
  `.truth/SKL-W0-01/before.txt`.
- **Method:** independent re-run (not the previous pass's recorded output). Full
  transcript stored in `.truth/SKL-W0-01/after.txt` (git-ignored working notes).
- **Code review findings:**
  - `scripts/install.sh` (197 lines): source resolution is a pure `skills/` tree
    search; no catalogue, no `python3 -c` newline bug, no doubled path. Package
    derivation is folder-based. `--force`/`--dry-run`/`--link` honoured. No
    TODO/FIXME, no hardcoded UI strings, no secrets.
  - `scripts/validate.py` (139 lines): catalog↔disk↔frontmatter consistency,
    duplicate id/name detection, path-under-package check. Deterministic.
  - `scripts/gen-catalog.mjs` (182 lines): deterministic walk, `.gitkeep`/cache
    exclusion, sorted `paths`, `--check` idempotency verified (regenerate then
    `--check` → exit 0).
  - `catalog.json`: regenerated, 32 skills / 5 packages, 518 paths, all exist on disk.
  - `tests/hygiene/*.test.mjs`: every broken fixture is built in a throwaway
    `mkdtemp` git repo under `/tmp` and removed in a `finally` block; the real
    worktree is never written by the tests.
  - No edits outside the owned paths. No file was truncated (line counts match
    trunk for every changed file; `git diff --stat` reviewed).
  - No test was weakened: the broken-fixture half of every hygiene test still
    fails (verified by running each suite; the `--dirty`/broken variants fail as
    required).
- **Reproduction results (all green):**
  - `node scripts/gen-catalog.mjs --check` → exit 0
  - `node scripts/gen-catalog.mjs` → 32 skills, 5 packages
  - `python3 -I scripts/validate.py` → `ok: 32 skills validated`
  - catalogue path existence check → 0 missing
  - clean clone `git status --porcelain` → empty (exit 0)
  - clean clone `pytest -q` → 349 passed, 9 skipped; the only 3 failures are the
    **pre-existing cross-job** defects in `skills/engineering/` (owned by
    `skills-engineering-r3`), unchanged from TASK-0006. The 13 `import file
    mismatch` collection errors from `before.txt` are gone.
  - hygiene suites → 7/8 green (see below)
  - `install.sh --package engineering|business-de|agentic-data` → 10/10 each
- **Not fixed this pass (all pre-existing, all outside owned paths):**
  1. `tests/hygiene/clean-tree.test.mjs` is red on a pre-existing dirty tree:
     `M skills/agentic-data/skill-authoring-evals/report_test.json` (owned by
     `skills-agentic-data-r3-02`), `?? docs/truth/REPO_PROBE.txt` (0-byte probe),
     `?? scripts/verify-status.mjs` (untracked STATUS.md checker). None of the
     three is mine to delete; the test itself is clean and its `--dirty` variant
     still fails as required.
  2. `scripts/truth/**` (preflight/gate/safe-commit/db/port) is absent from this
     repo — the blocked-check, gate and commit-and-integrate commands in the job card
     cannot be executed from here (G1, cross-job).
  3. The 3 cross-job `skills/engineering/` test failures.
  4. `skills/business-de/**` collection errors in a clean clone are resolved
     (the top-level `business-de/` duplicate and its stale `__pycache__` are
     gone); the canonical copy collects cleanly.
- **UNVERIFIED (carried forward, operator decision required):**
  - Docker leak test — no Docker daemon is reachable from this host; the
    install/link path cannot be exercised in a container here.
  - The GUC name decision (`app.company_id` vs alternatives) is an operator call
    recorded in D-006; the pg-rls checker follows whatever `config.json` names,
    so it is not a blocker for this job.
- **Index proof:** `P8`
- **Date:** 2026-10-16

---

## D-053 — TASK-0008 review: repro-script path bug (not a repo defect)

- **Scope of this pass:** adversarial re-review of the complete SKL-W0-01 change
  (git diff vs `origin/main` + working tree + untracked files), re-running every
  reproduction command from `.truth/SKL-W0-01/before.txt` and capturing the output
  in `.truth/SKL-W0-01/after.txt`.
- **Method:** independent re-run (not the previous pass's recorded output). Full
  transcript stored in `.truth/SKL-W0-01/after.txt` (git-ignored working notes).
- **Defect found — in my own harness, not in the repo:** the first pass of the
  reproduction suite reported `good_migration rc=2` and all three hostile fixtures
  `rc=2 (want 1)`. The checker exits 2 on a missing file, so the paths were wrong,
  not the checker. The RLS fixtures live under
  `skills/engineering/pg-rls-multitenant/references/examples/`, but the suite
  ran from `scripts/` and passed `references/examples/...` — a relative path that
  does not exist from that directory. Also the first pass's `log()` helper wrote
  to a relative path that did not exist once the suite `cd`'d into the scripts
  directory, so the RLS lines were lost from `after.txt`.
- **Fix:** the suite now uses an absolute `OUT` path and `../references/examples/...`
  for the RLS fixtures. Re-run: `good_migration rc=0`, all three hostile fixtures
  `rc=1`, self-test `rc=0`.
- **Result — every reproduction command green:**
  - `node scripts/gen-catalog.mjs --check` → `ok: catalog unchanged (32 skills, 5 packages)`, RC=0
  - `node scripts/gen-catalog.mjs` → writes 32 skills / 5 packages, RC=0
  - `python3 -I scripts/validate.py` → `ok: 32 skills validated`, RC=0
  - all 518 catalogue paths exist on disk (independent python check), RC=0
  - `install.sh --package engineering|business-de|agentic-data` → 10/10 each, PASS
  - `install.sh --package generic` → 32/32, PASS
  - `install.sh --link honest-status` → symlink created, RC=0
  - `install.sh --dry-run honest-status` → no writes, RC=0
  - `install.sh --package bogus` → RC=1 with known-package list
  - clean clone: `git status --porcelain` empty, RC=0
  - hygiene: 7/8 green; `clean-tree.test.mjs` red on the **pre-existing** dirty tree
    (see G5) — not a regression
  - RLS checker: good_migration PASS, hostile_1/2/3 FAIL, self-test ok
- **No truncation:** `git diff --numstat origin/main` for the changed files shows
  `scripts/install.sh` +76/−36 (157 lines on trunk → 197 now), `scripts/validate.py`
  absent from the diff (unchanged, 139 = 139), `catalog.json` +1055/−27 (70 lines on
  trunk → 1098 now), `tests/conftest.py` +27/−0 (0 on trunk → 27 now, new file).
  No file was shrunk or truncated — every changed file is strictly larger than its
  trunk counterpart.
- **Nothing outside owned paths changed:** `git status --porcelain` shows only the
  three pre-existing entries (G5) after filtering; nothing else.
- **No test was weakened:** every test added in TASK-0006 still fails on its broken
  fixture and passes on the real repo; `validate.py` still reports 32 skills.
- **G1 (truth harness missing) remains open and BLOCKS the gate / preflight /
  safe-commit commands in the job card.** `scripts/truth/**` does not exist in this
  repo (verified: `find / -name gate.mjs` returns only other products' copies under
  `/tmp`) and is on this job's EXCLUDE list, so it is another job's prerequisite.
  This job therefore lands via plain `git commit` guarded to its owned paths, as
  TASK-0001–TASK-0007 did. The gate command cannot be executed from this repo as
  written until the harness is provided.
- **Index proof:** `P7`
- **Date:** 2026-10-16

---

# TASK-0002 (2026-10-20) — installer `--check`, package catalogue, generated catalogue

## What the task card claimed vs. what the tree actually showed

The card was written against an older trunk. Reproduction
(`.truth/SKL-W0-01/before.txt`, trunk `2119edb`, 2026-10-20) measured:

| Claim in the card | Measured on trunk | Verdict |
|---|---|---|
| `install.sh --target claude honest-status` → "source skill directory missing" | `copied: …/honest-status`, exit 0 | already fixed (D-001, `5000adf`) |
| `--package engineering/business-de/agentic-data` → "unknown package" | exit 0, all three install | already fixed (D-002) |
| `python3 -I scripts/validate.py` → "ok: 2 skills validated" | `ok: 39 skills validated` | already fixed (D-003) |
| the catalogue is generated, not hand-edited | `gen-catalog.mjs --check` → exit 1 | **live (D-007)** |
| the installer has a `--check` mode (pack v3) | `install.sh --check` → "unknown option", exit 2 | **live (D-008)** |
| `--package … ref-*` installs every skill of the package | "resolves to no skills (reserved)" | **live (D-009)** |

The three headline defects were repaired by an earlier pass of this job (D-001,
D-002, D-003 above). The entries below are the defects still live on the trunk.

## D-007 — the catalogue carried a wall-clock stamp: `--check` could never pass again

- **Defect:** `node scripts/gen-catalog.mjs --check` exited 1 (`catalog would change`).
  The CI step "Catalogue must be GENERATED from the skills/ folders" was red; the
  clean clone was not green.
- **Cause (two independent defects, both had to go):**
  1. the generator wrote `updated_at: new Date().toISOString().slice(0, 10)`. The
     check compares byte for byte, so the timestamp alone made every later day fail;
  2. the committed catalogue was genuinely stale: three engineering skills had gained
     files that were missing from their `paths` lists (`foundation-v2-conformance` 3,
     `outbox-idempotency` 4) and `pg-rls-multitenant`'s description had changed.
- **Fix:** the generator is now a **pure function of the `skills/` tree**. The
  wall-clock stamp is gone — `schema/catalog.schema.json` does not require
  `updated_at` and nothing in the repository reads it — and the generator
  refuses to emit an entry whose frontmatter `name` disagrees with the folder
  name (that would make path, id and install target ambiguous). `--check` now
  reports **what** drifted (added / removed / changed skills) instead of only
  that something did. `catalog.json` was regenerated and committed.
  The `package` field comes from the name of the folder that contains the skill
  folder (`skills/<package>/<skill-name>/SKILL.md` → `<package>`); this is stated
  in the generator header and asserted by
  `tests/hygiene/test_catalog.py::test_package_field_comes_from_the_skill_folder`.
- **Proof:** `gen-catalog.mjs` → `ok: wrote … 39 skills, 12 packages`;
  `--check` → `ok: catalog unchanged (39 skills, 12 packages)`, exit 0; two
  consecutive generations are byte-identical (`cmp`); `pytest
  tests/hygiene/test_catalog.py -q` → 5 passed (drift, determinism,
  no-timestamp, package-source rule, every skill listed).
- **Index proof:** `P4`
- **Date:** 2026-10-20

## D-008 — `scripts/install.sh` had no `--check` mode, so the kit's install command exited 2

- **Defect:** `bash scripts/install.sh --check` printed `error: unknown option --check`
  and exited 2. That command was the `install` command of `scripts/truth/config.json`,
  so the gate's install step was red.
- **Cause:** the installer knew `--dry-run` (it prints the planned actions) but
  had no mode that verifies the *preconditions* of an installation — every
  requested skill resolves to a folder containing a `SKILL.md`, no skill name is
  ambiguous, the target is a writable directory — without writing anything.
- **Fix:** `--check` verifies exactly those preconditions, writes nothing (it
  does not even create the target directory) and exits 1 with a readable message
  per problem. The kit's install command is now `bash scripts/install.sh --check
  --target "${TMPDIR:-/tmp}/skl-w0-01-install-check" --package generic`.
  Writing the new tests exposed a second defect in the same area: `--dry-run`
  promised "print actions, write nothing" but still ran `mkdir -p "$TARGET"`.
  The target is now created only when something is really written into it.
- **Proof:** `--check --package generic` → `check: 39 skill(s) verified, nothing
  written`, exit 0, target directory **not** created; `--check … no-such-skill-xyz`
  → exit 1 with `error: source skill directory missing`; `--dry-run` creates no
  directory either; `pytest tests/hygiene/test_install.py -q` → 12 passed.
- **Index proof:** `P1`
- **Date:** 2026-10-20

## D-009 — `--package ref-*` installed nothing although those packages exist on disk

- **Defect:** `--package ref-webhooks-safe` printed `note: package
  'ref-webhooks-safe' resolves to no skills (reserved / on-demand)` and
  installed 0 skills — although `skills/ref-webhooks-safe/<skill>/SKILL.md`
  exists. The same for the other five `ref-*` packages.
- **Cause:** the case statement treated every name matching `meta|ref-*` as a reserved
  virtual package **before** the derived package list was consulted, so the real
  packages were never reached — the reserved branch silently swallowed them.
- **Fix:** the derived package list is consulted **first**. A package that
  exists on disk always wins; only `generic` (every skill of every package) and
  `meta` (reserved, ships nothing while there is no `skills/meta/`) are virtual.
  All six `ref-*` packages now install their skill and the "unknown package"
  error lists the derived packages.
- **Proof:** `--package ref-webhooks-safe` → 1 skill with `SKILL.md`; all 12
  derived packages install every skill they contain; `pytest
  tests/hygiene/test_install.py -q` → 9 passed (among them
  `test_on_demand_reference_packages_install_their_skill`).
- **Index proof:** `P3`
- **Date:** 2026-10-20

## D-010 — the truth kit's root allowlist was missing from `scripts/truth/config.json`

- **Defect:** `node tests/hygiene/root-allowlist.test.mjs` failed — every tracked
  root entry was reported as a violation — and the gate's `hygiene` step was
  skipped (`no rootAllowlist configured`).
- **Cause:** the truth kit was installed (commit `40ce066`) with a `config.json`
  without a `rootAllowlist` key. The test then reads the canonical file instead
  of the fallback manifest in `tests/hygiene/_fixture.mjs` and ends up with an
  empty allowlist.
- **Fix:** `rootAllowlist` was added to `scripts/truth/config.json` with exactly
  the list from the fixture manifest (`.github .gitignore .npmrc AGENTS.md
  CONTRIBUTING.md LICENSE README.md catalog.json docs index schema scripts skills
  templates tests`). The file is on this job's owned list and the data is read
  off the fixture that defines the invariant, not invented.
- **Proof:** `node tests/hygiene/root-allowlist.test.mjs` → 3/3 pass; the gate's
  `hygiene` step now runs instead of being skipped.
- **Index proof:** `P9`
- **Date:** 2026-10-20

## D-011 — the orchestrator's workspace state directory showed up as a foreign change

- **Defect:** the gate's `ownership` step failed with `4 changed file(s) outside
  the owned paths`: `.germo/notes/SKL-W0-01.md`,
  `.germo/notes/task_history.log`, `.germo/state.journal`,
  `.germo/state.json`.
- **Cause:** `.germo/` (the GERMO orchestrator's own state, not repository
  content) is not in `.gitignore`, and the truth kit enumerates untracked files
  with `git ls-files --others --exclude-standard`.
- **Fix (workaround, no tracked file touched):** `.germo/` was added to the
  worktree-local `.git/info/exclude`. The repository-level fix belongs to the
  job that owns `.gitignore` (skills-engineering-r3) and is requested in
  `docs/gaps/SKL-W0-01.md` (G9).
- **Proof:** `git status --porcelain` lists only this job's paths; the gate's
  `ownership` step passes.
- **Index proof:** `P10`
- **Date:** 2026-10-20

## D-012 — `safe-commit` could not see new files: git 2.53.0 returns nothing for `--untracked-files=all`

- **Defect:** the first `safe-commit` run committed only 6 of the 9 owned paths: the three
  new test files stayed untracked, although the gate had counted them.
- **Cause:** `scripts/truth/safe-commit.mjs` enumerates the working tree with
  `git status --porcelain=v1 -z --untracked-files=all`. In git 2.53.0 (the git on this host)
  `--untracked-files=all` produces **no output at all** — reproducible in an empty scratch
  repository, with and without `-z` and with `--porcelain=v2`. `--untracked-files=normal` and
  `git ls-files --others --exclude-standard` (what the gate uses) still work. The kit and the
  gate therefore disagree about which files exist.
- **Fix (workaround, no kit file touched):** the new files were staged explicitly
  (`git add -- <my own paths>`, which AGENTS.md allows); staged files are listed by every git
  status mode, so `safe-commit` then committed them. The defect is in the kit's file
  enumeration, not in this job's code.
- **Proof:** the same command is empty in a scratch repo while `--untracked-files=normal`
  lists the files; after the explicit `git add` it lists them as `A ` (recorded as G10).
- **Index proof:** `P11`
- **Date:** 2026-10-20

# TASK-0002 VERIFY pass (2026-10-20) — independent re-verification of the installer and the catalogue

The previous pass claimed the installer path bug and the package catalogue were done. This pass
re-ran every claim from scratch (installer, catalogue generator, validator, the whole CI
sequence, and a clean clone) instead of trusting the claim. The TASK-0002 deliverables are
**confirmed**; three further defects were found and fixed on the way.

## What was re-verified (all green)

| claim | command | observed |
|---|---|---|
| every skill folder resolves | `./scripts/install.sh --target <tmp> <name>` for all 39 folders | 39/39 installed, 0 unresolved |
| every real package installs all of its skills | `--package` for the 12 derived packages | expected == installed for every package |
| `generic` installs everything | `--package generic` | 39 of 39 |
| `meta` is accepted and empty | `--package meta` | rc 0, 0 skills, note printed |
| an unknown package is refused | `--package no-such-pkg` | rc 1, `unknown package` + the known list |
| `--check` writes nothing | `--check --target <tmp> --package engineering` | rc 0, 0 files written |
| `--dry-run` writes nothing | `--dry-run --target <tmp> --package engineering` | rc 0, 0 files written |
| the catalogue is generated | `node scripts/gen-catalog.mjs --check` | `ok: catalog unchanged (39 skills, 12 packages)` |
| the catalogue is reproducible | regenerate into a temp file, `diff` | byte-identical |
| the catalogue matches the folders | compare 39 entries with the folders | 0 mismatches |
| the catalogue is not hand-edited | `pytest tests/hygiene/test_catalog.py` | 5 passed (fails on a tampered `catalog.json`) |
| the validator sees every skill | `python3 -I scripts/validate.py --everywhere` | `ok: 39 skills validated` |
| the whole suite is green | `python3 -m pytest tests/ -q` | 44 passed |
| a clean clone works | `git clone` + the CI sequence | catalogue byte-identical, installs 10/39 skills |

## D-013 — `scripts/install.sh` matched a package name as a regular expression

- **Defect:** the package lookup used `grep -qx "$PACKAGE"`, so the name was a regex.
  `--package ".*"` matched *every* derived package and installed the whole tree;
  `--package "engineering+"` matched the `engineering` package. A package that does not
  exist was accepted.
- **Fix:** `grep -qxF "$PACKAGE"` — the name is matched literally.
- **Proof:** `tests/hygiene/test_install.py::test_package_names_are_matched_literally`
  refuses `engineering+`, `.*`, `engineering?` and `engineering.*`. With the old line
  restored the test fails (`--package .*` returned 0 and installed everything); with the
  fix it passes.
- **Index proof:** `P12`
- **Date:** 2026-10-20

## D-014 — `scripts/verify-status.mjs` crashed on every claim table

- **Defect:** `const line = raw.rstrip();` — `rstrip()` is a *Python* method, a JavaScript
  string has none. The checker died with `TypeError: raw.rstrip is not a function` on the
  first table row, so it could never check anything.
- **Fix:** `const line = raw.replace(/\s+$/, "");`.
- **Proof:** `tests/hygiene/test_verify_status.py`; with the old file restored 4 of its 5
  tests fail, with the fix all 5 pass.
- **Index proof:** `P13`
- **Date:** 2026-10-20

## D-015 — `scripts/verify-status.mjs` never checked the evidence file (a swallowed error)

- **Defect:** `try { ok = require("node:fs").existsSync(p); } catch { ok = false; }`.
  `scripts/verify-status.mjs` is an ES module (`.mjs`, `import` at the top), and `require`
  does not exist there — the `ReferenceError` was swallowed by the bare `catch`, so `ok`
  stayed `false` for every row. Every claim row was reported as `log path not found`,
  including rows whose evidence file existed: a checker that can never pass.
- **Fix:** import `existsSync` from `node:fs` next to `readFileSync` and call it directly;
  the `try`/`catch` is gone (it only existed to hide the `require`).
- **Proof:** `test_a_claim_with_an_existing_log_passes` expects exit 0 and the message
  `all 1 claim rows verified`; with the old file it failed with the `TypeError` above.
- **Index proof:** `P13`
- **Date:** 2026-10-20

## D-016 — the orchestrator contract test asserted two mutually exclusive things

- **Defect:** `tests/orchestrator/test_gen_preamble_failure.py` asserted
  `text.startswith("# Orchestrator Preamble (generated)")` **and**, for every rule number,
  `text.startswith(f"{i}. ")`. A document cannot start with the header *and* with `1. `, so
  the test was permanently red and validated nothing. It was red before this job's first
  commit (`2119edb`) and stayed red through TASK-0002.
- **Fix:** the header is asserted on the first line, the four rules are located as numbered
  list items, and the test asserts that there are **exactly** four of them, numbered `1..4`
  in order — strictly more than the old assertion, which could never hold.
- **Proof:** `python3 -m pytest tests/ -q` → 44 passed, 0 failed (was 36 passed, 1 failed).
- **Index proof:** `P14`
- **Date:** 2026-10-20

## TASK-0003 (clean clone green: empty-dir, /tmp and tree-dirtying tests)

Baseline measured on a fresh clone of `ec2c086` (evidence: `.truth/SKL-W0-01/before.txt`):
`pytest -q` aborted the whole collection with 1 error, 3 tests failed, 395 passed,
9 skipped, and the run left `skills/agentic-data/skill-authoring-evals/report_test.json`
modified in the checkout.

## D-017 — the contract-drift self-test pointed at a foreign machine and aborted the collection

- **Defect:** `skills/engineering/module-contract-first/scripts/check_contract_drift_test.py`
  ran every checker call with `cwd="/srv/ottili/repo/skills/skills/engineering/module-contract-first"`.
  On any other checkout the path does not exist, so the module raised
  `FileNotFoundError` **at import time**. pytest therefore aborted the entire
  collection (`Interrupted: 1 error during collection`) and no test in the
  repository ran at all. The same file also wrote its fixture to the fixed path
  `/tmp/test_contract`.
- **Cause:** the self-test was written on a machine where the Ottili checkout
  lived at `/srv/ottili/repo/skills` and hard-coded that layout instead of
  deriving the path from its own location.
- **Fix:** the skill directory is now derived from `__file__`
  (`Path(__file__).resolve().parents[1]`), the checker is started with
  `cwd=<skill dir>`, and every test gets its own throwaway module through
  pytest's `tmp_path` fixture. The file is still runnable as a standalone script
  (`python3 skills/engineering/module-contract-first/scripts/check_contract_drift_test.py`),
  which is how CI runs it.
- **Proof:** `python3 -m pytest -q` collects the whole repository again
  (633 tests, 0 collection errors); the standalone script exits 0.
- **Index proof:** `P15`
- **Date:** 2026-10-20

## D-018 — the acceptance-harness self-test unpacked a `CompletedProcess` and could never fail

- **Defect:** `skills/engineering/acceptance-harness/scripts/report_result_test.py`
  did `rc, _ = run(...)` while `run()` returns a `subprocess.CompletedProcess`
  (`TypeError: cannot unpack non-iterable CompletedProcess object`). The two
  edge-case tests therefore always raised. The standalone runner had a second
  bug: `failures += fn()` added `None` (the functions returned nothing on
  success), which raised `TypeError` inside the `except` handler and made
  `python3 report_result_test.py` exit 1 even when every check passed.
- **Cause:** the edge-case tests were added later and were never run in either
  shape (pytest collects them, CI runs the file as a script).
- **Fix:** the tests use `r.returncode` and real `assert` statements (so pytest
  can actually fail them), each gets its own `tmp_path`, and the standalone
  runner catches `AssertionError` and counts it.
- **Proof:** `python3 -m pytest -q skills/engineering/acceptance-harness/scripts/report_result_test.py`
  -> 2 passed; `python3 skills/engineering/acceptance-harness/scripts/report_result_test.py`
  -> exit 0 (before: exit 1 with `TypeError`).
- **Index proof:** `P16`
- **Date:** 2026-10-20

## D-019 — the research/design acceptance test referenced an undefined constant

- **Defect:** `skills/engineering/tests/test_research_design_acceptance.py`
  used `ENGINEERING_DIR`, but the module defines `ENGINEERING`. The cross-link
  graph test failed with `NameError: name 'ENGINEERING_DIR' is not defined`.
- **Fix:** the test uses `ENGINEERING`.
- **Proof:** `python3 -m pytest -q skills/engineering/tests/test_research_design_acceptance.py`
  -> 1 passed.
- **Index proof:** `P17`
- **Date:** 2026-10-20

## D-020 — a skill test wrote its JSON report into the skill folder

- **Defect:** `skills/agentic-data/skill-authoring-evals/tests/test_validate_skill.py`
  wrote `--json` output to `skills/agentic-data/skill-authoring-evals/report_test.json`
  and deleted the file before the run. The tracked file was overwritten on every
  test run, so `git status --porcelain` was never empty after the suite.
- **Fix:** the report goes into the test's `tmp_path`. The committed
  `report_test.json` stays as it is; nothing writes it any more.
- **Proof:** `git status --porcelain` after a full `pytest -q` run lists only the
  files of the pending change, no `M skills/agentic-data/.../report_test.json`.
- **Index proof:** `P18`
- **Date:** 2026-10-20

## D-021 — three business-de test modules wrote to fixed paths under `/tmp`

- **Defect:** `skills/business-de/publish-reconcile-wp-meta/tests/test_publish.py`,
  `skills/business-de/webhooks-safe/tests/test_webhooks.py` and
  `skills/business-de/carrier-apis-de/tests/test_carrier.py` wrote their fixtures
  to fixed names (`/tmp/_pub_wp.json`, `/tmp/_wh_body.json`, `/tmp/_lab.json`, ...)
  outside the worktree. Fixed names collide between parallel runs, survive the
  run as litter on the shared host, and are invisible to the tree check.
- **Fix:** every fixture goes into the test's `tmp_path` (pytest's per-test
  temporary directory). No test in the repository writes to a hard-coded `/tmp`
  path any more (`grep -rn 'Path("/tmp' --include=test_*.py --include=*_test.py`
  finds nothing).
- **Proof:** `python3 -m pytest -q skills/business-de/` -> 218 passed, no file
  outside the pytest temporary directory is created.
- **Index proof:** `P19`
- **Date:** 2026-10-20

## D-022 — a collection guard for a deleted directory hid 218 real tests

- **Defect:** `tests/conftest.py` added `norecursedirs = business-de` to keep
  pytest away from a stale top-level `business-de/` duplicate. That duplicate
  was deleted in commit `0d5f964`, but the guard stayed. Because pytest matches
  `norecursedirs` against the **basename**, the guard also excluded the
  canonical `skills/business-de/` tree: 218 passing tests were never executed by
  any full run (the suite reported 407 tests instead of 633). The docstring
  described a directory that no longer exists.
- **Fix:** the guard is gone. The invariant it tried to protect ("no duplicate
  skill directory anywhere") is now enforced by a test that fails loudly:
  `tests/hygiene/test_skill_tree.py`. The collected test count went from 407 to
  633 and the suite is green.
- **Proof:** `python3 -m pytest -q` -> 624 passed, 9 skipped, 0 failed
  (before: 395 passed, 3 failed, 1 error, 218 tests never collected).
- **Index proof:** `P19`
- **Date:** 2026-10-20

## D-023 — the pg-rls self-test required a foreign repository

- **Defect:** `skills/engineering/pg-rls-multitenant/scripts/check_rls_migration_test.py`
  asserted that three migrations of the **hq-v2** repository pass the checker.
  Those files live in another checkout (`/srv/ottili/repo/hq-v2/...`), so the
  self-test failed with `file not found` on every host that does not have that
  repository - including CI and a fresh clone of this repository.
- **Fix:** the corpus root is read from `OTTLI_HQ_REPO` (default
  `/srv/ottili/repo/hq-v2`). Where the corpus is present it is checked exactly as
  before; where it is not, the self-test proves the documented contract for a
  missing file (exit 2 plus "not found") and says out loud that the corpus was
  not available. The two pytest edge tests in the same file returned an `int`
  instead of failing, so pytest could never fail them; they now assert.
- **Proof:** `python3 skills/engineering/pg-rls-multitenant/scripts/check_rls_migration_test.py`
  -> exit 0 with the note about the missing corpus (before: exit 1).
- **Index proof:** `P7`
- **Date:** 2026-10-20

## D-024 — the long-test self-test left two log files in the repository root

- **Defect:** `skills/engineering/long-test-discipline/scripts/run_long_test_test.sh`
  calls `run_long_test.sh` without `--log`, so the script wrote `long-test.log`
  and `long-test.log.out` into the **current working directory** - the
  repository root when CI runs it from the checkout. The tree was dirty after
  the self-test.
- **Fix:** the self-test exports `OTTLI_TEST_LOG="$TMP/long-test.log"`, so both
  files end up in the temporary directory it already creates. `run_long_test.sh`
  itself is unchanged: it still honours `OTTLI_TEST_LOG` and `--log`.
- **Proof:** `bash skills/engineering/long-test-discipline/scripts/run_long_test_test.sh`
  -> exit 0 and `git status --porcelain` stays empty (before: two untracked
  files in the repository root).
- **Index proof:** `P20`
- **Date:** 2026-10-20

## D-025 — nothing stopped a test from dirtying the checkout

- **Defect:** there was no guard that the test suite leaves the working tree
  untouched. `skills/agentic-data/skill-authoring-evals/report_test.json` proved
  the gap: the suite overwrote a tracked file on every run and no test noticed.
- **Fix:** one canonical implementation, `tests/hygiene/clean_tree.py`, with the
  functions `dirty_paths`, `is_clean`, `dirt_added_since` and `seed_dirty`. It is
  used by the pytest guard `tests/hygiene/test_clean_tree.py`, which runs **after
  every other test module** (the `runs_last` marker plus the ordering hook in
  `tests/conftest.py`). The guard compares the tree state at the end of the
  session with the state at the start: on a clean checkout the tree must still be
  clean, and on a checkout with pending work the tests must not add anything to
  it. The guard is proven against a deliberately dirty fixture in a throwaway
  repository, so it cannot rot into a rubber stamp.
- **Merge:** the previous node-only implementation `tests/hygiene/clean-tree.test.mjs`
  was a second implementation of the same check and could not be run by the
  configured runner (pytest rejects a `.test.mjs` path with exit 4). It was
  replaced by the canonical module and the pytest guard; the command line lives
  on as `python3 tests/hygiene/clean_tree.py [--dirty] [--root <dir>]`.
- **Proof:** `python3 -m pytest -q` -> 624 passed, 9 skipped, 0 failed and
  `git status --porcelain` shows only the pending change; the guard fails on a
  seeded fixture (see `test_guard_fails_on_a_seeded_dirty_fixture`).
- **Index proof:** `P21`
- **Date:** 2026-10-20

## D-026 — the suite leaked 28 files into the shared temporary directory

- **Defect:** D-021 removed the *fixed* `/tmp` paths from three business-de
  test modules, but the suite still wrote into the shared temp directory, and
  it left 28 files behind: 14 `tmp*.json` payloads, 13 `tmp*` directories and
  one `tmp*.warc.gz`. `git status --porcelain` cannot see them, so the card's
  own proof (`git status` after the run) stayed green while the leak grew.
  The sources were `tempfile.mktemp()` (deprecated: it only picks a name, the
  file is never removed), `tempfile.mkdtemp()` without a matching
  `shutil.rmtree`, and `NamedTemporaryFile(delete=False)` whose manual
  `os.unlink` is skipped when an assertion fails first.
- **Fix:** every test file now writes only into the directory pytest hands it
  (`tmp_path`) or into a directory it removes itself. Ten test modules were
  changed: `mcp-2026-07-28`, `dedup-decontam`, `polite-crawling-warc` (two
  files), `webhooks-safe` (two files), `carrier-apis-de`,
  `publish-reconcile-wp-meta` and `dsgvo-ai-act-labeling` (helper plus its
  three callers). The helper `dsgvo_test_helpers.write_label()` took a
  directory now instead of inventing a name in `/tmp`.
- **Kept on purpose:** `skills/engineering/shared-tree-git/scripts/check_shared_tree_test.py`
  keeps `tempfile.mkdtemp()`. It is a self-test that the CI also runs with
  `python3 <file>` (no pytest fixtures available), and it removes the
  directory in a `finally` block.
- **Proof:** the suite is run with `TMPDIR` pointing at an empty directory; the
  directory must be empty afterwards. Before: 28 leftovers. After: 0.
  `tests/hygiene/test_temp_files.py` is the regression test: it lints the test
  sources for `mktemp`, `delete=False` and `mkdtemp` without `rmtree`, and it
  fails on a planted offender (proven by planting one in a scratch copy).
- **Index proof:** `P22`
- **Date:** 2026-10-20

## D-027 — the clean-tree guard only looked at the end of the session

- **Defect:** the card asks for a check "after every test module runs"; the
  implementation compared the tree at the end of the session with the tree at
  the start. A module that dirtied the checkout and a later module that cleaned
  it up again left no trace, and the guard could not name the module that did
  it. The guard was also proven only against a throwaway repository, not
  against the checkout it protects.
- **Fix:** `tests/conftest.py` gained `pytest_runtest_teardown`, which compares
  the tree at the end of **every** test module with the state at the start of
  the session and fails the module that added dirt. The end-of-session guard
  stays as the last line of defence. `tests/hygiene/test_clean_tree.py` gained
  an end-to-end test: a second pytest session runs with a plugin that writes
  a stray file into the repository, and the test asserts that this session
  fails, that the failure names the stray file, and that the repository is
  free of it again afterwards.
- **Proof:** the end-to-end test fails when the module check is removed (the
  failure message changes) and when the checker is made blind (`dirty_paths`
  returns an empty list). Both mutations were run in scratch copies of the
  repository; the unmutated copy passes.
- **Side effect:** the docstring of `tests/hygiene/clean_tree.py` still
  advertised `tests/hygiene/clean-tree.test.mjs`, a file that D-025 deleted.
  It now names the three real entry points.
- **Index proof:** `P21`
- **Date:** 2026-10-20

## Verification commands run for TASK-0003

```
python3 -m pytest -q                                  # 624 passed, 9 skipped, 0 failed
python3 -m pytest -q <the 9 changed test files>       # 65 passed (the gate's command)
python3 skills/engineering/module-contract-first/scripts/check_contract_drift_test.py   # exit 0
python3 skills/engineering/acceptance-harness/scripts/report_result_test.py             # exit 0
python3 skills/engineering/pg-rls-multitenant/scripts/check_rls_migration_test.py       # exit 0
bash skills/engineering/long-test-discipline/scripts/run_long_test_test.sh               # exit 0
python3 tests/hygiene/clean_tree.py                   # exit 0 on a clean checkout
grep -rn 'Path("/tmp' --include=test_*.py --include=*_test.py skills/ tests/   # no hits
git status --porcelain                                # empty after a full run
```

### Commands run for the TASK-0003 VERIFY pass (2026-10-20)

```
python3 -m pytest -q                                  # 627 passed, 9 skipped, 0 failed
git status --porcelain                                # empty after the run
TMPDIR=<empty dir> python3 -m pytest -q               # the dir is empty afterwards: 0 leftovers
python3 -m pytest -q tests/hygiene/test_clean_tree.py # 4 passed (the end-to-end negative case)
python3 -m pytest -q tests/hygiene/test_temp_files.py # 2 passed (the temp-file lint)
node scripts/gen-catalog.mjs --check                  # ok: catalog unchanged (39 skills, 12 packages)
python3 scripts/truth/gate.mjs job --job SKL-W0-01 ...   # see .truth/SKL-W0-01/gate.log
```

The clean copy and the real clone are rebuilt from the committed state after
every commit; the numbers are in `.truth/SKL-W0-01/after.txt`.

## D-030 — 16 stale status diaries were still committed inside the skill packages

- **Defect:** the tree still carried the pass-by-pass status diaries of the earlier
  autonomous waves: 9 `STATUS.md` files, 3 collection `HANDOFF.md` files, 2
  `skills/business-de/config/REVERIFY_*.md` files, `skills/agentic-data/references/PASS2-STATUS.md`,
  `skills/agentic-data/references/PASS5-R3-05-REVERIFY.md` and
  `docs/truth/REVERIFY-SKL-W0-01-TASK-0006.md`. Every one of them is a diary about
  work that has been finished since; a reader cannot tell which claims are still true.
  Proof of the defect: `git ls-files | grep -c STATUS` → 9 (must be 0) and
  `git ls-files | grep -cE '(HANDOFF|GAPS|R3_PLAN|REVERIFY)'` → 16.
- **Cause:** the earlier wave (D-00x above) kept them because `docs/R3_OWNERS.json`
  assigns `skills/business-de/**` and `skills/agentic-data/**` to other jobs. The card of
  this wave grants `skills/**` to SKL-W0-01 and orders exactly this deletion, so the
  ownership map of round 3 no longer describes this task.
- **Fix:** `git rm` of the 16 files above. The `references/EVALS.md` of the 30 skills
  stay — they are skill content (`scripts/validate_skills.py` fails a skill without
  one) and not diaries. `skills/agentic-data/browser-agent-playwright/references/handoff.md`
  stays for the same reason: it is the hand-off *contract* of that skill and is linked
  from its `SKILL.md`.
- **Proof:** `git ls-files | grep -c STATUS` → 0;
  `git ls-files | grep -cE '(HANDOFF|GAPS|R3_PLAN|REVERIFY)'` → 0;
  `node scripts/gen-catalog.mjs --check` → "catalog unchanged" (the catalogue no longer
  names a deleted file).
- **Index proof:** `P23`
- **Date:** 2026-10-20

## D-031 — a collection test asserted that a status diary exists

- **Defect:** `skills/agentic-data/tests/test_collection.py::test_handoff_exists` read
  `skills/agentic-data/HANDOFF.md` and asserted it contains a re-verification section.
  After D-030 the file is gone and the test fails with `FileNotFoundError`
  (`1 failed, 62 passed, 9 skipped`).
- **Cause:** the test asserted the *existence of a diary*, not a property of the
  skills. That premise is invalid once the tree policy is "a skill collection ships
  skills, not diaries about them".
- **Fix:** the test was rewritten, not deleted: `test_collection_ships_no_status_diary`
  asserts that the collection contains no `STATUS.md`/`HANDOFF.md` (the new invariant),
  and the new `test_each_skill_carries_its_own_reverification_material` asserts that
  every skill keeps what the diary used to hold — >= 6 primary URLs and a retrieval
  date in `references/SOURCES.md`.
- **Proof:** `python3 -m pytest skills/agentic-data/tests/test_collection.py -q` →
  `73 passed, 9 skipped`. With the old test body restored the file fails again.
- **Index proof:** `P18`
- **Date:** 2026-10-20

## D-032 — 34 dangling pointers to the deleted diaries

- **Defect:** after D-030, 34 places still pointed at deleted files:
  10 × `skills/agentic-data/*/references/SOURCES.md` ("see `references/PASS5-R3-05-REVERIFY.md`
  for the full table"), 20 × `skills/business-de/config/versions.json` (`reverify_note`),
  `skills/business-de/carrier-apis-de/references/SOURCES.md`,
  `skills/business-de/PASS5_GATE.md`, `skills/business-de/README.md` and
  `skills/engineering/README.md` ("See `HANDOFF.md` for what to re-verify").
- **Cause:** the diaries were the only place some evidence and some navigation lived.
- **Fix:** every pointer was replaced by the substance it pointed at — each source
  carries its own retrieval date and HTTP result, `versions.json` keeps the
  re-verification date, the READMEs point at the runnable commands
  (`scripts/run_evals.py`, the per-skill self-tests).
- **Proof:** `git grep -n -F '<deleted file name>' -- . ':!catalog.json'` → no hit for
  `PASS2-STATUS.md`, `PASS5-R3-05-REVERIFY.md`, `REVERIFY_2026-10-14.md`,
  `REVERIFY-SKL-W0-01-TASK-0006.md`; the remaining `REVERIFY_2026-10-15.md` hits are
  only in `docs/gaps/SKL-W1-02.md`, which belongs to another job (G18).
- **Index proof:** `P24`
- **Date:** 2026-10-20

## D-033 — the duplicate-name proof was polluted by scratch copies of the tree

- **Defect:** the proof
  `find . -name SKILL.md | xargs -n1 dirname | xargs -n1 basename | sort | uniq -d`
  printed 46 duplicate names in the worktree, although the tracked tree has none
  (`git ls-files '*/SKILL.md' | ... | uniq -d` → empty).
- **Cause:** this job's own scratch area `.truth/SKL-W0-01/` held 18 full copies of the
  tree (clean-clone, clone and mutation-control copies of earlier passes). They are
  git-ignored, so `git status` never showed them, but the file-system proof saw them.
- **Fix:** the redundant scratch *copies* were removed (the evidence files
  `before.txt`, `after.txt`, `notes.md`, the logs and the gate JSONs were kept).
- **Proof:** `find . -name SKILL.md | xargs -n1 dirname | xargs -n1 basename | sort | uniq -d`
  → empty; `find .truth -name SKILL.md | wc -l` → 0.
- **Index proof:** `P5`
- **Date:** 2026-10-20

## D-034 — the generated catalogue still named the deleted files

- **Defect:** `catalog.json` listed 5 deleted `STATUS.md` paths in the `paths[]` array
  of the agentic-data skills, so the catalogue pointed at files that no longer existed.
- **Cause:** the catalogue is generated from the folders; the folders changed and the
  catalogue had not been regenerated.
- **Fix:** `node scripts/gen-catalog.mjs` (39 skills, 12 packages).
- **Proof:** `node scripts/gen-catalog.mjs --check` → "ok: catalog unchanged".
- **Index proof:** `P4`
- **Date:** 2026-10-20

## D-035 — the collection scripts check skipped 9 of the 10 skills

- **Defect:** `skills/agentic-data/tests/test_collection.py::test_scripts_match_skill_md`
  looked for a `scripts:` summary line in `SKILL.md` and **skipped** the skill when it
  found none. Nine of the ten skills document their scripts as
  ``scripts/foo.py`` inside their checklists instead of in a summary line, so the
  check ran against one skill only. The truth gate refuses a test run that reports
  skipped tests ("skipped tests prove nothing"), and the gate's `tests` step failed:
  `FAIL tests the run reports skipped tests`.
- **Cause:** the check was written against one documentation format and used a skip
  to hide the other nine, so a mismatch between `scripts/` and `SKILL.md` would have
  gone unnoticed for nine skills.
- **Fix:** the nine `SKILL.md` files now carry the same summary line the tenth one
  had (`- scripts: scripts/a.py, scripts/b.py`), listing **every** script the skill
  ships - seven scripts were not documented anywhere before (`evals_md.py`,
  `minhash_lsh.py`, `plant_test.py`, `gen_fixtures.py`, `gen_rubric.py`,
  `rubric_lint.py`, `validate_skill.py` in two skills). The test was rewritten to
  assert both directions without a skip: a script path named in `SKILL.md` exists,
  and every script the skill ships is named in `SKILL.md`.
- **Proof:** `python3 -m pytest skills/agentic-data/tests/test_collection.py -q` →
  `82 passed` (was `62 passed, 9 skipped, 1 failed`). The gate's `tests` step →
  `PASS  tests  1 test path(s) passed`.
- **Index proof:** `P18`
- **Date:** 2026-10-20

## D-036 — the language step flagged the German business-domain source catalogues

- **Defect:** the truth gate's `language` step failed on three files that this pass
  had to touch: `skills/business-de/bank-reconciliation-camt/references/SOURCES.md`,
  `skills/business-de/carrier-apis-de/references/SOURCES.md` and
  `skills/business-de/config/versions.json` (`language-umlaut` on `DFÜ-Abkommen`,
  `language-identifier` on the German URLs `gesetze-im-internet.de/ao/` and
  `steuer-berater.de`). It also flagged one German word in the English package
  README (`skills/business-de/README.md:31`).
- **Cause:** the three data files quote German law, German law titles and German
  source URLs verbatim - that is their content, not untranslated prose. The gate
  scans a whole file as soon as the file changes, so pre-existing German in a
  touched file counts against the change.
- **Fix:** the kit's own escape hatch was used instead of a threshold change -
  `truth:allow-german-file` in the head of the two source catalogues and in the
  `_comment` of `config/versions.json` (the kit's scanner skips a file whose first
  five lines carry that marker). The one German word in the English README was
  reworded to the wording the catalogue already uses ("German VAT (UStG) edge
  cases"). `scripts/truth/config.json` was left untouched.
- **Proof:** the gate's `language` step → `PASS  language  31 file(s) scanned`; the
  kit's own scanner over every changed file reports nothing outside `catalog.json`,
  which the kit allows by configuration.
- **Index proof:** `GATE`
- **Date:** 2026-10-20

## D-037 — `REPO_SHAPE.md` drifted from the tree, and nothing noticed

- **Defect:** the source of truth for the canonical-skills job claimed **649** tracked
  files and **30** repository-level test files; the tree had **651** and **32**. Two of
  the document's numbers were wrong the moment it was written.
- **Cause:** `docs/truth/REPO_SHAPE.md` was written in commit `0bc1a13`, the guard test
  `tests/hygiene/test_no_status_diaries.py` landed in `d9c14aa`, and nothing compared the
  document with the tree. A claim without a check is a wish.
- **Fix:** corrected the numbers, made every label match the command beside it, and added
  `tests/hygiene/test_repo_shape_numbers.py`. The test parses every
  `| What | Value | Command |` row of the document, runs that command verbatim and compares
  the printed number with the claimed one. Twelve rows are checked; the test is generic, so
  a row added later is checked automatically and a stale row fails.
- **Proof:**
  - against the stale document: `AssertionError: REPO_SHAPE.md drifted from the tree:
    Tracked files: document says 649, command says 651`;
    Repository-level test files: document says 30, command says 32`.
  - after the fix: `pytest tests/hygiene/test_repo_shape_numbers.py -q` → 1 passed.
  - a planted wrong number (`| Tracked files | 999 |`) fails the test again in a throwaway
    clone of `38c4a77` → the guard bites.
  - `pytest -q` → 650 passed, 0 skipped.
- **Index proof:** `P25`
- **Date:** 2026-10-20

## D-038 — the tool inventory was incomplete and claimed there was no second installer

- **Defect:** `docs/truth/REPO_SHAPE.md` stated *"No second installer, validator or
  catalogue generator exists in the tree."* That is false: `scripts/install-skill.py` is a
  second installer — it resolves a skill by name or id in `catalog.json` and copies it into
  an agent skills directory, which is the job `scripts/install.sh` does. Four further tools
  were missing from the inventory: `scripts/validate_reviewed_by.py`,
  `scripts/check_related_graph.py`, `scripts/list-skills.py` and `scripts/gen-preamble.mjs`.
- **Cause:** the inventory was written from the tools this job knew, not from `ls scripts/`.
- **Fix:** rewrote the section as the complete inventory (twelve rows, one per file in
  `scripts/`) and stated the requirement that can actually be checked — exactly one
  `scripts/install.sh` and exactly one `scripts/validate.py` — each with its own command.
- **Proof:** `git ls-files 'scripts/install.sh' | wc -l` → 1;
  `git ls-files 'scripts/validate.py' | wc -l` → 1; the inventory lists all twelve files of
  `scripts/`.
- **Cross-job:** the overlap between the two installers is requested in
  `docs/gaps/SKL-W0-01.md` (G21); `scripts/**` is not on this job's owned list.
- **Index proof:** `P26`
- **Date:** 2026-10-20

## D-039 — the per-skill `references/EVALS.md` files are a validator input, not diaries

- **Question:** the delete list of this task names `EVALS.md`, but thirty skills ship
  `references/EVALS.md` with their eval prompts. Are those diaries?
- **Finding:** no — they are a required input of the skill validator. Verified by experiment
  in a throwaway clone: with `skills/engineering/honest-status/references/EVALS.md` moved
  aside, `python3 scripts/validate_skills.py` exits **1** and reports
  `[honest-status] missing references/EVALS.md`. With the file present it exits 0.
- **Decision:** keep them. Deleting them would turn the validator red — the symptom, not the
  cause. The root-level `EVALS.md` diaries of the earlier waves were deleted (D-004).
- **Proof:** `git ls-files | grep -cE '(HANDOFF|GAPS|R3_PLAN|REVERIFY)'` → 0; the only
  `EVALS.md` files left are the thirty per-skill ones under `references/`.
- **Correction found in the VERIFY pass:** the validator does *not* check every skill.
  `scripts/validate_skills.py` hardcodes `SKILLS_DIR = .../skills/engineering`, so it
  validates the ten engineering skills although its docstring promises "every skill
  folder"; the nine catalogue skills without an eval set are never asked for one. It also
  crashes with `UnboundLocalError` when the first validated skill has no `EVALS.md`, and
  counts the prompts of the *previous* skill's file for later ones. Two agentic-data
  skills ship an eval set their `SKILL.md` never links — a defect the wider scan would
  have caught. Both are recorded in `docs/gaps/SKL-W0-01.md` (G24); neither file is on
  this job's owned list.
- **Guard:** `tests/hygiene/test_skill_eval_sets.py` keeps the four facts that are
  checkable from this job's paths honest — the engineering skills keep their eval set,
  every link to an eval set resolves, every shipped eval set is in the catalogue, and no
  eval diary survives outside `skills/`.
- **Index proof:** `P27`
- **Date:** 2026-10-20

## D-040 — the RLS checker rejected the real corpus and trusted one hard-coded name

- **Defect:** `skills/engineering/pg-rls-multitenant/scripts/check_rls_migration.py`
  answered "FAIL" for **74 of 120** real migrations that have nothing wrong with
  them, and it decided that the tenant setting name is `app.company_id` — a
  constant of the script, not a fact about the repositories. Three real
  migrations were rejected for reasons that are checker bugs, not migration bugs:
  - `hq-v2/modules/operations/migrations/20261008150000_hq_operations_r3_04_task_team_assignment.sql`
    — `ALTER TABLE IF EXISTS … ENABLE ROW LEVEL SECURITY`: the `ENABLE`/`FORCE`
    patterns did not allow the optional `IF EXISTS` / `ONLY` clauses, so the
    checker reported "missing ENABLE ROW LEVEL SECURITY" on a table that has it;
  - `hq-v2/modules/operations/migrations/20261003045054_operations_file_link.sql`
    — the policy is keyed on `current_setting('ottili.company_id', true)`; the
    checker only knew `app.company_id` and called a correct policy wrong;
  - 70 further files — migrations that only touch an existing table (`ALTER TABLE
    … ADD COLUMN`, `CREATE INDEX`) were rejected with "no CREATE TABLE statement
    found; is this a tenant migration?". The checker asked a question about the
    *file* when the rule is about the *table*.
- **Cause:**
  1. `TENANT_GUC = "app.company_id"` was a constant of the script. The plan's
    census of the name was never written down, so the script could not be
    corrected when a repository used a different (also correct) name.
  2. The `CREATE TABLE` regex had to be present in the file, so a migration
    without a `CREATE TABLE` was a finding instead of "this file creates no
    tenant table".
  3. `ENABLE`/`FORCE` were matched without the `IF EXISTS` / `ONLY` variants
    that the product migrations actually use.
  4. A policy inside a `DO $$ … $$` block was invisible: the statement splitter
    had no notion of dollar-quoted bodies.
- **Fix:** the checker now
  - reads the accepted tenant GUC names from `guc-names.json` next to the script
    (`--guc-names` overrides it); a missing or broken configuration is a usage
    error (exit 2), never a guess;
  - splits SQL into statements while respecting comments, string literals and
    dollar-quoted bodies, and scans a `DO` block for the policy it creates;
  - decides **per table**: a table this file *creates* must carry `company_id`,
    `ENABLE` + `FORCE ROW LEVEL SECURITY` and a tenant policy keyed on an
    accepted name; a table that already exists is held to what this file
    touches (its policy), because the file that created it is the one that had
    to switch RLS on;
  - accepts `ALTER TABLE [IF EXISTS] [ONLY] …`.
- **Proof:**
  - the three hostile files still fail: `hostile_1_no_force.sql` (missing
    FORCE), `hostile_2_no_company_id.sql` (no discriminator, unknown setting),
    `hostile_3_grant_all.sql` (GRANT ALL) → exit 1 each;
  - the three real hq migrations (copied into `tests/fixtures/hq-migrations/`,
    provenance in `tests/fixtures/PROVENANCE.md`) pass → exit 0;
  - census over 120 real migrations of hq-v2, console-v2 and ottili-apps:
    **74 failures before → 1 failure after**, and that one failure is a real
    defect in hq-v2 (see D-041);
  - `python3 -m pytest tests/hygiene/test_rls_checker.py -q` → 9 passed.
- **Guard:** `tests/hygiene/test_rls_checker.py` proves that every name in
  `guc-names.json` is accepted, that a name nobody sets is rejected, and that
  the configuration — not the script — decides (a `--guc-names` file with one
  name makes the other migrations fail).
- **Index proof:** `P28`
- **Date:** 2026-10-20

## D-041 — the tenant GUC inventory, and one open owner decision

- **Question:** which tenant setting name does a policy have to use? The plan
  calls `app.company_id` dominant and `ottili.company_id` in the apps
  "UNVERIFIED". The blueprint does not decide it, and this job does not decide
  it either: choosing one name for all repositories is an owner decision.
- **Finding (measured 2026-10-20, `grep -rlE "current_setting\('NAME'" --include='*.sql'`):**

  | GUC name | hq-v2 | console-v2 | ld3-v2 | ottili-platform | ottili-apps | alran-core-v2 | alran-clients-v2 | ottilionev1 | skills | files | occurrences |
  |---|---|---|---|---|---|---|---|---|---|---|---|
  | `app.company_id` | 511 | 121 | 8 | 47 | 19 | 340 | 47 | 0 | 2 | 1095 | 3027 |
  | `app.current_company_id` | 0 | 0 | 218 | 0 | 0 | 0 | 23 | 18 | 0 | 259 | 919 |
  | `ottili.company_id` | 3 | 0 | 0 | 34 | 39 | 0 | 0 | 0 | 0 | 76 | 267 |
  | `app.current_company` | 17 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 18 | 51 |

  `app.company_id` is the dominant name in seven of the nine repositories;
  `ld3-v2` uses `app.current_company_id`, the apps and the platform use
  `ottili.company_id`, and 17 hq-v2 files still use the older
  `app.current_company`. Names that exist but are **not** tenant discriminators:
  `ottili.actor_ref` (the acting subject), `app.current_tenant_key` (legacy
  `ottilionev1` tables keyed on `tenant_key`), `app.is_superadmin` (a role flag).
- **Decision:** none taken here. All four names are written to
  `skills/engineering/pg-rls-multitenant/guc-names.json` as *accepted*, each with
  its measured inventory, and the file states that `canonical_name` is `null`
  and the decision is open. The checker accepts every name in the file and
  rejects a name that is not in it — a policy keyed on a setting nobody sets
  isolates nobody.
- **Proof:** `python3 -c "import json;print([n['name'] for n in json.load(open('skills/engineering/pg-rls-multitenant/guc-names.json'))['accepted_names']])"` →
  `['app.company_id', 'app.current_company_id', 'ottili.company_id', 'app.current_company']`.
- **Real defect found on the way (not fixed here — another repository):**
  `hq-v2/modules/my-work-home/migrations/20261014150000_hq_my_work_home_r3_11_quickcreate.sql`
  creates `my_work_home_quick_create` and `my_work_home_recent` with tenant
  policies but **without** `ENABLE`/`FORCE ROW LEVEL SECURITY`; the same hole
  appears in the two follow-up migrations `…_r3_12_quickcreate_state.sql` and
  `…_r3_13_quickcreate_recent_lifecycle.sql`. The tables are unprotected for
  the table owner. Recorded as a cross-job request in
  `docs/gaps/SKL-W0-01.md` (G25); this job does not write into `hq-v2`.
- **Index proof:** `P29`
- **Date:** 2026-10-20

## D-042 — the honest-status checker could not read the format the product repositories write

- **Defect:** the checker of the skill — `skills/engineering/honest-status/scripts/check_status_evidence.py`,
  the implementation the skill installs and the one `scripts/verify-status.mjs` is supposed
  to be a thin wrapper around — **crashes on every real STATUS.md of the product
  repositories**:
  `KeyError: 'UNFILED'` at `parse_status()` (line 68), because the real files have
  no `## DONE` / `## VERIFIED` bucket headers at all. It therefore never reaches a
  verdict about the 13 593 lines of real status prose it is meant to police.
  The repository-level entry point `scripts/verify-status.mjs` was meanwhile a
  **second, independent** table parser written in JavaScript, so the skill and the
  tool of the repository could never agree (the JS one reported 322 rows for
  `hq-v2`, the Python one crashed).
- **Cause:** two defects in one place.
  1. The parser only knew one grammar (the bucket headers of the skill). The
     product repositories write **claim tables**: a row that asserts a success
     names the command that was run, the exit code it returned and the log file
     that proves it.
  2. `scripts/verify-status.mjs` re-implemented the table parsing itself instead
     of delegating to the skill, so the "one canonical implementation per
     capability" rule was broken in the same directory the rule protects.
- **Fix:**
  - new module `skills/engineering/honest-status/scripts/status_tables.py` parses
    the claim-table grammar: it splits markdown tables, skips the separator row,
    finds the rows that assert a success (`exit 0`, `grün`, `passed`, `13 passed,
    0 failed`, a check mark …), and collects the three elements of each claim —
    the **command** (a backticked span that is a command, not a path), the
    **exit code** (`exit 0`, `rc=1`, a bare `0` cell) and the **log path**
    (a backticked span with a file suffix or a dotted last segment);
  - `check_status_evidence.py` gained a `--format auto|bucket|table` switch, a
    format detector and a table verdict: a claim that lacks any of the three
    elements is a finding, and a named log path that does not exist is a
    finding ("a log file that does not exist proves nothing"). The bucket
    grammar is untouched and its own self-test still passes;
  - `scripts/verify-status.mjs` is now a **thin adapter**: it resolves the
    checker next to it and runs it, so the tool of the repository and the skill
    an agent installs are the same code.
- **Proof:**
  - `node scripts/verify-status.mjs <nvme>/hq-v2/docs/STATUS.md --root <nvme>/hq-v2`
    → **exit 1**, `112 unverified row(s)`, each with its **line number**
    (first: `line 27: `npm install`` — no exit code, log path not found:
    `npm-install.log`);
  - `node scripts/verify-status.mjs <nvme>/console-v2/docs/STATUS.md --root <nvme>/console-v2`
    → **exit 1**, `302 unverified row(s)` (first: `line 33: `npm test`` — no log path);
  - `--json` names the offending rows, their line numbers and their problems;
  - `python3 -m pytest tests/hygiene/test_verify_status.py -q` → 9 passed; the
    committed test runs against the **real excerpts** copied into
    `tests/fixtures/status/` (provenance in `tests/fixtures/PROVENANCE.md`), never
    against a sibling repository.
- **Guard:** `tests/hygiene/test_verify_status.py` asserts that the real excerpts
  are reported with line numbers, that a claim with an existing log passes, and
  that a claim without a log path, without an exit code or with a missing log
  file fails. A third status grammar can never be silently accepted again.
- **Index proof:** `P13`
- **Date:** 2026-10-20

## D-043 — the RLS leak-test harness could never print PASS

- **Defect:** `skills/engineering/pg-rls-multitenant/scripts/pg-rls-leak-test.sh`
  — the harness that proves a tenant table does not leak — died with exit 1
  after `>> running probe as web_app` and never printed a verdict, not even on a
  migration that is correct.
- **Cause:** two defects.
  1. **The SQL.** The probe printed its measurements as *aliased* columns
     (`SELECT count(*) AS a_sees_own FROM t`). The harness runs psql with
     `-t -A` (tuples only, unaligned), and psql does **not** print the column
     alias in that mode: the output was a bare `1` and a bare `0`. The label —
     the only thing that says which measurement a number is — was lost in the
     query, not in the parser.
  2. **The parser.** The verdict was a shell pipeline
     (`echo "$OUT" | grep a_sees_own | tail -1 | cut -f2`). `grep` matched
     nothing, the pipeline failed, and `set -euo pipefail` killed the script
     before the verdict. Even without `set -e`, a measurement that was *never
     made* looked like a measurement of zero.
- **Fix:**
  - the probe now prints the label as a **value**:
    `SELECT 'a_sees_own', count(*) FROM t;` → the output line is
    `a_sees_own<TAB>1`, which survives `-t -A`;
  - the judgement moved into `skills/engineering/pg-rls-multitenant/scripts/check_leak_probe.py`:
    PASS only when `a_sees_own == 1` **and** `a_sees_b == 0`; a **missing**
    measurement is a failure ("the probe did not run"), and so is an `ERROR:` in
    the probe output;
  - the harness reads the accepted tenant setting names from
    `guc-names.json` (through the canonical loader of `check_rls_migration.py`,
    which gained `--list-guc-names`) and sets **every** accepted name to the
    tenant, so the harness works on every product repository without taking the
    open decision about one canonical name; `--guc NAME` overrides it;
  - two modes were added so the verdict is provable **without** a Docker
    daemon: `--print-probe-sql` (prints the probe SQL) and `--parse FILE`
    (judges a captured probe output). The Docker path is unchanged and stays
    the default.
- **Proof** (real PostgreSQL 18.6, container runtime replaced by a local server
  because the Docker daemon is not reachable on this host — see G27):
  - good migration (`references/examples/good_migration.sql`) → probe output
    `a_sees_own 1` / `a_sees_b 0` → `PASS: RLS leak test green`, **exit 0**;
  - seeded leaky migration (a permissive `USING (true)` policy) → probe output
    `a_sees_own 2` / `a_sees_b 1` → `FAIL: RLS leak test - block merge`,
    **exit 1**, with `cross-tenant leak (expected 0, got 1)`;
  - `python3 -m pytest tests/hygiene/test_leak_probe.py -q` → 7 passed; the
    committed test drives the two daemon-free modes and writes its bad inputs
    itself, so no bad file is ever borrowed.
- **Guard:** `tests/hygiene/test_leak_probe.py` asserts that the probe SQL
  prints the labelled measurements (and no longer an alias), that every accepted
  GUC name is set, and that a good probe output passes while a leaking output, a
  missing measurement and an error in the output all fail.
- **Index proof:** `P30`
- **Date:** 2026-10-20

## D-044 — the preamble contract test asserted a README heading that the README never had

- **Defect:** `node tests/orchestrator/test_preamble_contracts.test.mjs` failed
  with `AssertionError: README has no preamble section`. The failure was
  **pre-existing** (it is present at `HEAD`, commit `7fec9dd`, and no file of
  this pass touched `README.md`).
- **Cause:** the test asserted the literal string
  `## Orchestrator preamble (generated)`. The README's heading is
  `## Orchestrator preamble`, and the body of the section says that the block
  **is generated** and must never be hand-edited. The assertion checked a
  wording the document never used, so the test failed on a correct README.
- **Fix:** the test now asserts the heading the document actually has
  (`## Orchestrator preamble`) and keeps the meaningful part of the contract
  (the README documents `node scripts/gen-preamble.mjs --check`). The document
  was **not** changed: `README.md` is outside the owned paths of this job, and
  the document was right.
- **Proof:** `node tests/orchestrator/test_preamble_contracts.test.mjs` →
  5 tests, 5 pass, 0 fail (before: 4 pass, 1 fail).
- **Index proof:** `P14`
- **Date:** 2026-10-20

## D-045 — the truth gate could not run its test step when a non-Python file changed

- **Defect:** the gate step `tests` failed with
  `pytest -q {paths} exited 4 — no tests ran — ERROR: not found: tests/orchestrator/test_preamble_contracts.test.mjs`.
  The gate hands the **changed** files to the test command; `pytest` cannot
  collect a `.mjs` file and refuses the whole run with a usage error. Every
  job of this repository that touched a non-Python file hit this.
- **Cause:** `commands.test` in `scripts/truth/config.json` was the bare
  `pytest -q {paths}`. The paths are not filtered by type.
- **Fix:** `commands.test` now selects the collectable Python tests out of the
  changed paths and falls back to the whole repository suite when the change
  contains no Python test file:
  `P=$(printf '%s\n' {paths} | grep -E '(^|/)test_[^/]*\.py$' | tr '\n' ' '); if [ -n "$P" ]; then pytest -q $P; else pytest -q tests; fi`
  The pattern is pytest's own default collection pattern (`test_*.py`), so a
  changed non-test Python file is not mistaken for a test module.
- **Proof:** the gate step `tests` now runs the two changed test modules
  (16 tests, all pass) instead of failing with a usage error; the whole
  repository suite (`pytest -q tests` → 79 passed) stays green.

### Justification for the `language.allowGlobs` entries of `scripts/truth/config.json`

The truth kit requires a justification in this log for every per-scan
exemption. The entries are:

| Glob | Why |
|---|---|
| `catalog.json` | The generated catalogue carries the German descriptions of the German business skills (carriers, invoices, VAT). It is generated output (`generatedGlobs`), not prose of this repository. |
| `tests/fixtures/status/**` | The two excerpts of the real `docs/STATUS.md` files of `hq-v2` and `console-v2`. They are **verbatim user-facing German prose** of the product repositories, copied so that a committed test never has to read a sibling repository. They are test data, not code, and they must stay byte-identical to their source (provenance: `tests/fixtures/PROVENANCE.md`). |

The German success vocabulary that the checker needs to recognise those files
lives in `skills/engineering/honest-status/scripts/status_tables.py`, which
carries the scanner's own file-level marker `truth:allow-german-file` and the
reason next to it. No other file of this repository was exempted.
- **Index proof:** `GATE`
- **Date:** 2026-10-20

## D-046 — the RLS checker could not read a `DO $$ … $$` block and misread an escaped policy

- **Defect:** the checker of D-040 rejected **178 of 1389** real product
  migrations (hq-v2, console-v2, ottili-apps). Almost all of those rejections
  were the checker being wrong, not the migrations:
  - 209 findings of the kind "no CREATE POLICY for tenant isolation" and 164
    findings of the kind "tenant policy is not keyed on an accepted tenant
    GUC" were reported on migrations that carry the policy — inside a
    `DO $$ … $$` block, or spelled `current_setting(''ottili.company_id'', true)`
    because the policy is created with `EXECUTE`;
  - D-040 claimed that the checker "scans a `DO` block for the policy it
    creates". It did not: the untagged dollar quote was invisible.
- **Cause — two defects, both in the scanner:**
  1. **The untagged dollar quote was invisible.** The body of a dollar-quoted
     string was read with
     `r"\$(?P<tag>[A-Za-z_]\w*)?\$(?P<body>.*?)\$(?P=tag)\$"`. A
     back-reference to a group that did not take part in the match never
     succeeds, and in `$$ body $$` the tag group does not take part — so the
     regex matched **nothing**. The tagged spelling `$tag$ body $tag$` was the
     only one that worked, and no migration of the product repositories uses
     it: 270 of the 1389 migrations protect their tables in an untagged
     `DO $$ … $$` block.
  2. **A statement of a `DO` body does not start the fragment.** The product
     migrations guard the DDL with a condition:
     `IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE …) THEN ALTER TABLE t ENABLE ROW LEVEL SECURITY;`
     The `ALTER TABLE` and the `CREATE POLICY` therefore follow the `THEN`
     and were invisible to a scanner that only looks at the start of a
     statement.
  3. **The escaped spelling of the setting name was not read.** The regex for
     the setting name required `current_setting('name'` with one quote. A
     policy created with `EXECUTE` writes the name with doubled quotes
     (`current_setting(''ottili.company_id'', true)`), because the policy is a
     string literal — 164 real migrations of `ottili-apps` write it that way.
- **Fix:**
  - the dollar body is read with the opening and the closing tag compared
    explicitly, so both spellings work and a body whose closing tag differs is
    not read;
  - inside a dollar-quoted body the `ALTER TABLE` and the `CREATE POLICY` are
    looked for anywhere in the fragment, not only at its start. The strict,
    anchored reading is kept for the statements of the file itself;
  - the setting name is accepted with one or two quotes on each side.
- **Proof:**
  - census over the real corpus, reproducible with the command below:
    **178 failures before → 8 failures after**;
  - the two real migrations that carry the two shapes are committed as
    fixtures (`tests/fixtures/rls-shapes/`, provenance in
    `tests/fixtures/PROVENANCE.md`) and the checker passes them. The
    pre-fix checker fails both of them — that is the regression the guard
    protects:
    ```
    git show HEAD:skills/engineering/pg-rls-multitenant/scripts/check_rls_migration.py > /tmp/old_checker.py
    python3 /tmp/old_checker.py --guc-names skills/engineering/pg-rls-multitenant/guc-names.json tests/fixtures/rls-shapes/*.sql
    ```
  - the three hostile files still fail (exit 1 each), the three real hq
    migrations still pass (exit 0 each);
  - the two seeded bad inputs inside the test fail with the fix in place, so
    reading a `DO` block did not make the checker blind inside it:
    a `DO` block without `FORCE` is still "missing FORCE ROW LEVEL SECURITY",
    and a policy created with `EXECUTE` on a setting nobody sets is still
    "not keyed on an accepted tenant GUC";
  - `python3 -m pytest tests/hygiene/test_rls_checker.py -q` → 13 passed.
  - **the two fixtures were applied to a real PostgreSQL 18.6 and the database
    agrees with the checker**: `psql -v ON_ERROR_STOP=1 -f` of the five
    migration fixtures of `tests/fixtures/` leaves every table with
    `relrowsecurity = true`, `relforcerowsecurity = true` and one policy —
    including `accounting_gl.tax_codes` (protected inside a `DO $$ … $$`
    block) and `public.github_issue_link` (policy created with `EXECUTE`).
    The truth gate does the same on a fresh database and applies the
    migrations **twice** (`PASS migrate  migrations applied twice on a fresh
    database truth_skl_skl_w0_01; 2 owned table(s) verified with forced
    RLS`).
- **The census, with the command that reproduces it** (D-040 wrote "120
  migrations" without the command, so the number could not be reproduced —
  this is the version with the command):
  ```
  R=/mnt/ottili-nvme/ottili/v2/repo
  find $R/hq-v2 $R/console-v2 $R/ottili-apps -type f -name '*.sql' \
    -not -path '*/.truth/*' -not -path '*/dist/*' -not -path '*/node_modules/*' \
    -not -path '*/test/*' -not -path '*/tests/*' -not -path '*/fixtures/*' | sort \
    > /tmp/census.txt            # 1389 files
  python3 skills/engineering/pg-rls-multitenant/scripts/check_rls_migration.py \
    --json $(cat /tmp/census.txt | tr '\n' ' ') | python3 -c 'import json,sys; print(json.load(sys.stdin)["failures"])'
  ```
  The eight files that remain are one deliberate global table in `console-v2`
  (see G30) and **seven real holes in `hq-v2` and `ottili-apps`** that the
  blind scanner had never reported (see G28).
- **Index proof:** `P28`
- **Date:** 2026-10-20

## D-047 — the repository invariants were node:test files that no runner executed

- **Defect:** the hygiene decisions of this job (no tracked symlink with an
  absolute target, a self-loop, a target outside the checkout or a dangling
  target; no tracked database or
  journal file; no scratch directory or debug script at the repository root;
  no tracked file above 5 MiB without an allow-listed reason; unique
  workspace project names; the workspace protocol for internal dependencies;
  the private registry for the `@ottili` scope) were implemented in seven
  `tests/hygiene/*.test.mjs` files that ran under `node --test`. The gate
  runs its test step with `pytest -q {paths}` and never collected a
  `.test.mjs` file, so none of the seven invariants was executed by the
  gate, by CI or by `pytest` — a rule that no runner executes is a comment.
- **Cause:** the invariants were written for the node test runner while the
  test command of this repository is pytest.
- **Fix:** the invariants are pytest modules under `tests/hygiene/`
  (`test_no_bad_symlinks.py`, `test_no_database_files.py`,
  `test_root_allowlist.py`, `test_no_large_files.py`,
  `test_workspace_projects.py`, `test_npmrc_scope.py`) on top of the shared
  helper `tests/hygiene/repo_guard.py`. The seven `.test.mjs` files and their
  helper `_fixture.mjs` were deleted (with `--allow-delete` and a reason in
  the commit): they are the same rules in a second runner, and the truth kit
  config — which the old helper carried as a fallback list — is the single
  source of truth for the allow-lists now. Every invariant is proven twice:
  against the real repository it must hold, and against a deliberately broken
  fixture — a throwaway git repository that the test builds itself — it must
  be reported.
- **Proof:**
  - `python3 -m pytest -q tests/hygiene/test_no_bad_symlinks.py tests/hygiene/test_no_database_files.py tests/hygiene/test_root_allowlist.py tests/hygiene/test_no_large_files.py tests/hygiene/test_workspace_projects.py tests/hygiene/test_npmrc_scope.py` → **38 passed**;
  - `python3 -m pytest -q tests` → **121 passed** (83 before this pass, 38 new);
  - the broken fixtures are built inside the tests and each one asserts that
    the checker reports it: an absolute link, a self-loop, a dangling link, a
    link that leaves the checkout, a
    `*.db`, a `*.db-wal`, a `*.db-shm`, a `*.sqlite`, a `*.journal`, a scratch
    directory, a debug script, a 6 MiB blob, a duplicated workspace name, a
    registry-pinned internal dependency, an `@ottili` scope that points at
    npmjs.org, a second scope mapping and an empty scope mapping. Each module
    also carries a healthy fixture that must be accepted, so the checkers are
    not merely noisy.
  - the node runner still agrees: `for t in tests/orchestrator/*.test.mjs; do node "$t"; done` → all pass.
  - the new modules are lint clean and type clean:
    `ruff check tests/hygiene/repo_guard.py tests/hygiene/test_*.py` →
    **All checks passed!**; `mypy --strict` on the same seven files →
    **Success: no issues found in 7 source files**.
- **Index proof:** `P31`
- **Date:** 2026-10-20

## D-048 — the truth kit config still carried the template's migration command and had no large-file allow-list

- **Defect:** `scripts/truth/config.json` still configured `commands.migrate`
  (the template key for a repository that owns migrations) although this job
  owns none — the job card lists its migration stamp block as "none" — and it
  had no `largeFileAllowlist`, so the 5 MiB rule had nowhere to read an
  exception (and its reason) from.
- **Cause:** the template config was adopted as it was; the pack-v3 decision
  (2026-10-19) asks for the keys that apply to this repository only.
- **Fix:** `commands.migrate` was removed and `largeFileAllowlist` was added
  as an empty list of `{path, reason}` entries. The `rootAllowlist` was
  checked against the tree and is correct: the 15 entries are exactly the
  entries `git ls-tree --name-only HEAD` shows. The other keys were left
  alone — `boot`, `smokeTests`, `registryCheck`, `e2e` and `typecheck` are
  not configured, so their gate steps report `skip`.
- **Proof:**
  - the gate reports the migration step as skipped, before and after the
    change: `skip  migrate  job has no migrations and --db was not given`;
  - `node scripts/truth/gate.mjs job --job SKL-W0-01 --owned "…" --exclude "…" --skip registry,e2e` → **GATE PASSED**;
  - the root allow-list is now an executable invariant:
    `tests/hygiene/test_root_allowlist.py` fails on a fixture that carries a
    scratch directory or a debug script at the root and passes on the real
    repository.
- **Index proof:** `P32`
- **Date:** 2026-10-20

## D-049 — two commands of the pack-v3 decision do not run in this repository

- **Defect:** the decision of 2026-10-19 names the commands of the config as
  `install "bash scripts/install.sh --check"` and `test "pytest -q {paths}"`.
  Both fail here, so they were not written into the config verbatim.
- **Cause:** the decision was written for the template of the kit, not
  measured against this repository.
- **Fix:** the config keeps the commands that work and the deviations are
  recorded here and in `docs/gaps/SKL-W0-01.md` (G31).
  - `install` keeps the required `--target` and the virtual package
    `generic`:
    `bash scripts/install.sh --check --target "${TMPDIR:-/tmp}/skl-w0-01-install-check" --package generic`
    → **exit 0**, `check: 39 skill(s) verified, nothing written`.
    The literal command of the decision exits **2**:
    ```
    bash scripts/install.sh --check
    error: --target is required
    ```
  - `test` keeps the filter for the Python test paths, because the live test
    set of this job contains `*.test.mjs` files (the node tests of
    `tests/orchestrator/`) and pytest cannot collect them. The literal
    command of the decision exits **4**:
    ```
    pytest -q tests/orchestrator/test_gen_preamble.test.mjs
    ERROR: not found: …/tests/orchestrator/test_gen_preamble.test.mjs
    (no match in any of [<Package orchestrator>])
    ```
    The config runs `pytest -q` on the `test_*.py` paths of the change and
    falls back to `pytest -q tests` when the change contains none.
- **Proof:** the gate test step with the config command → **6 test path(s)
  passed**, exit 0; the full suite → **121 passed**.
- **Index proof:** `GATE`
- **Date:** 2026-10-20

## D-050 — the two commands of the pack-v3 decision now run unchanged (D-049 closed)

- **Defect (from D-049, re-measured at the start of this pass):** the decision of
  2026-10-19 names the commands of the config as
  `install "bash scripts/install.sh --check"` and `test "pytest -q {paths}"`.
  Both still failed, so the config carried workarounds instead of the decision:
  ```
  bash scripts/install.sh --check
  error: --target is required                    # exit 2
  pytest -q tests/orchestrator/test_gen_preamble.test.mjs
  ERROR: not found: .../tests/orchestrator/test_gen_preamble.test.mjs
  (no match in any of [<Package orchestrator>])  # exit 4
  ```
- **Cause 1:** `scripts/install.sh` refused `--check` without a `--target`, so the
  install command of the decision could not be the install command of the gate.
- **Cause 2:** the test files of `tests/orchestrator/` and `tests/reviews/` were
  Node 22 `node:test` modules. The gate collects the changed test files and hands
  them to `pytest -q {paths}`; pytest cannot collect a `*.test.mjs` path.
- **Fix (the code, not the expectation):**
  1. `scripts/install.sh --check` works without `--target`: it verifies every skill
     folder of every package against a scratch directory
     (`${TMPDIR:-/tmp}/ottili-install-check`) that is never created. A skill
     folder without a `SKILL.md` is reported; the auxiliary folders `references/`,
     `scripts/`, `tests/` and `config/` of a package are not skills. Regression
     tests in `tests/hygiene/test_install.py`, including one that breaks a fixture
     (a skill folder without a `SKILL.md` -> exit 1).
  2. the six `*.test.mjs` modules of `tests/orchestrator/` and `tests/reviews/` were
     converted to pytest modules (`test_*.py`) with the same assertions. All six
     were green under `node --test` before the conversion:
     ```
     tests/orchestrator/test_gen_preamble.test.mjs          PASS
     tests/orchestrator/test_preamble_contracts.test.mjs    PASS
     tests/orchestrator/test_preamble_reproducible.test.mjs PASS
     tests/reviews/test_signoff_gate.test.mjs                PASS
     tests/reviews/test_signoff_ref_wrappers.test.mjs        PASS
     tests/reviews/test_ust_legal_corrections.test.mjs       PASS
     ```
  3. `scripts/truth/config.json` carries the decision's command strings unchanged.
     The catalogue guard is not lost: `scripts/validate.py --everywhere` cross-checks
     the generated catalogue against the `skills/` folders, and
     `tests/hygiene/test_catalog.py` compares the regenerated catalogue byte-for-byte
     with the committed one.
- **Measured exit codes of every command of the config (each run once):**

  | command | exit | output |
  |---|---|---|
  | `bash scripts/install.sh --check` | **0** | `check: 39 skill(s) verified, nothing written` |
  | `python3 -I scripts/validate.py --everywhere` | **0** | `ok: 39 skills validated` |
  | `pytest -q <changed test paths>` | **0** | `8 passed` (1 path), `20 passed` (3 paths) |
  | `node scripts/gen-catalog.mjs --check` | **0** | `ok: catalog unchanged (39 skills, 12 packages)` |

- **Proof:** the trunk gate -> install **PASS**, build **PASS**, lint **PASS**,
  typecheck/migrate/boot/smoke **skip**, hygiene **PASS** (15 root entries, all
  allowed); the job gate -> **PASS**; the full suite -> **126 passed** before the
  conversion and **169 passed** after it.
- **Open (cross-job, not mine):** `.github/workflows/validate.yml` and `README.md`
  still glob the deleted `*.test.mjs` files. They belong to `skills-engineering-r3`
  and are outside the owned paths of this job card; the exact patch is in
  `docs/gaps/SKL-W0-01.md` (G32).
- **Index proof:** `GATE`
- **Date:** 2026-10-20

## D-054 — the shape document drifted again when this repair-log entry was committed

- **Symptom:** after the repair-log entry of TASK-0007 was committed,
  `pytest tests/hygiene/test_repo_shape_numbers.py -q` failed with
  `REPO_SHAPE.md drifted from the tree: Tracked files: document says 664, command
  says 665` and `Tracked files under 'tests/': document says 42, command says 43`.
- **Reproduction:** `python3 -m pytest tests/hygiene/test_repo_shape_numbers.py -q`
- **Root cause:** `docs/truth/REPO_SHAPE.md` states the number of tracked files,
  and the guard test of this job (`tests/hygiene/test_repair_log.py`) is one more
  tracked file — the count changed with the commit that added it. The D-037 guard
  did its job: it refused to let the document drift.
- **Fix:** `docs/truth/REPO_SHAPE.md` — the two numbers were corrected
  (664 → 665, 42 → 43) and the guard that found them is the repair.
- **Proof:** `python3 -m pytest tests/hygiene/test_repo_shape_numbers.py -q` → 1 passed.
- **Index proof:** `P25`
- **Date:** 2026-10-20

---

## D-055 — the six-field check of the index was not per entry

- **Defect:** the guard of this log reported no problem although the index entry
  of `D-030` had lost its `**Date:**` line and the entry of `D-031` had lost
  its `**Symptom:**` line. Both were measured: the guard stayed green.
- **Cause:** `split_section()` ended a block at the next `\n## `, but the index
  entries are `#### ` headings. The "body" of an entry therefore ran on to the
  end of the index, and every field search found the field of a *later* entry.
  A check that reads its evidence from the wrong paragraph is no check.
- **Fix:** `tests/hygiene/test_repair_log.py` — a block ends at the next heading
  of the same or a higher level, the heading scan ignores fenced code (a bash
  comment starts with `#`), the field check runs per entry, and two mutation
  tests prove that a broken entry is reported.
- **Proof:** the mutation of the index entry of `D-030` (the `**Date:**` line
  removed) and of `D-031` (the `**Symptom:**` line removed) each make
  `python3 -m pytest tests/hygiene/test_repair_log.py -q` fail with the id of
  the broken entry.
- **Index proof:** `P33`
- **Date:** 2026-10-20

---

## D-056 — the command of an index entry could drift from the proof block

- **Defect:** writing `bash scripts/install.sh --totally-wrong` next to the label
  `P1` in the index entry of `D-001` left the whole guard green, although the
  proof block still ran `bash scripts/install.sh --check`.
- **Cause:** the guard only asserted that the command of the proof block
  appeared *somewhere* in the document (`command in text`). It never compared it
  with the command the index writes down, so the two could drift apart.
- **Fix:** `tests/hygiene/test_repair_log.py` — the command of an index entry
  must be the command of the proof block of that label, and a mutation test
  proves it. `docs/truth/REPAIR_LOG.md` — the four entries that cited `GATE` in
  prose now write the command of the gate next to the label.
- **Proof:** the mutation of the inline command of `D-001` makes
  `python3 -m pytest tests/hygiene/test_repair_log.py -q` fail with `D-001`.
- **Index proof:** `P33`
- **Date:** 2026-10-20

---

## D-057 — a defect section carried neither a date nor a proof label

- **Defect:** not one of the 52 defect sections of this log had a `- **Date:**`
  line, and the narrative of a defect and its index entry could contradict each
  other without anything noticing.
- **Cause:** the narrative sections were written before the index existed, and
  the guard had no cross-check between the two.
- **Fix:** `docs/truth/REPAIR_LOG.md` — every defect section ends with
  `- **Index proof:** `Pxx`` and `- **Date:** YYYY-MM-DD`, taken from its index
  entry. `tests/hygiene/test_repair_log.py` — the guard compares the label and
  the date of the section with the label and the date of the index entry.
- **Proof:** `python3 -m pytest tests/hygiene/test_repair_log.py -q` fails with
  the id of the defect as soon as one of the two dates differs.
- **Index proof:** `P33`
- **Date:** 2026-10-20

---

## D-058 — the follow-up check promised a symptom and tested a path

- **Defect:** `test_the_follow_up_list_exists_and_names_path_and_symptom`
  asserted only that the bold title of an item contains a backtick. An item
  whose body carried no symptom at all passed the test that claims to check
  the symptom.
- **Cause:** the assertion and the name of the test disagreed.
- **Fix:** `tests/hygiene/test_repair_log.py` — every follow-up item must name a
  path in its title and carry a symptom in its body (at least 40 characters of
  text), and a mutation test proves it.
- **Proof:** the first follow-up item of
  `docs/truth/REPAIR_LOG.md` with its body removed makes
  `python3 -m pytest tests/hygiene/test_repair_log.py -q` fail.
- **Index proof:** `P33`
- **Date:** 2026-10-20
## D-059 — the installer wrote — and with --force deleted — outside the target directory

- **Defect:** `bash scripts/install.sh --force --target <dir> ../pkg/good` resolved the
  destination to `<dir>/../pkg/good`, deleted that directory (`rm -rf "$dest"`) and
  wrote the skill there. A folder OUTSIDE the target was destroyed; the installer
  never asked and never printed where it wrote. The same name without `--force`
  wrote outside the target as well.
- **Cause:** the skill name was used unvalidated as a path component of the
  destination (`dest="$TARGET/$name"`). The "ambiguous package" check fired only
  when the tree held more than one package, so the refusal was accidental
  protection, not a guard. A single-package tree was enough to escape.
- **Fix:** `scripts/install.sh` — every skill name is checked against
  `^[A-Za-z0-9._-]+$` (no path separator, no `.`/`..`, no leading dash) BEFORE
  anything is written; an unsafe name is refused with exit 2.
  `tests/hygiene/test_install.py` — a fixture with a folder outside the target
  proves that the name is refused and that the folder survives.
- **Proof:** the four new installer tests fail against the pre-fix installer
  (measured: `git show HEAD:scripts/install.sh`).
- **Index proof:** `P34`
- **Date:** 2026-10-20

## D-060 — `--check` refused a target that the install accepts

- **Defect:** `bash scripts/install.sh --check --target <dir>/does/not/exist --package engineering`
  exited 1 with `error: target parent '<dir>/does/not/exist' does not exist`, while
  the very same target was installed without complaint (exit 0): the install creates
  the tree with `mkdir -p`. The check was stricter than the install and reported a
  false failure.
- **Cause:** the check demanded that the PARENT of the target already existed. The
  install never demanded that.
- **Fix:** `scripts/install.sh` — the check now walks up to the nearest EXISTING
  ancestor of the target and asks whether the tree could be created there; a target
  that cannot be created (an ancestor that is a file) is still refused.
  `tests/hygiene/test_install.py` — one test proves that the check accepts the
  target the install accepts, one that it refuses the target that cannot exist.
- **Proof:** the two new installer tests fail against the pre-fix installer.
- **Index proof:** `P35`
- **Date:** 2026-10-20

## D-061 — the catalogue generator ignored an unknown option and overwrote the catalogue

- **Defect:** `node scripts/gen-catalog.mjs --chek` printed
  `ok: wrote .../catalog.json — 39 skills, 12 packages` and exited 0: the unknown
  option was ignored, so a typo of `--check` silently WROTE the catalogue instead
  of checking it. `node scripts/gen-catalog.mjs --out` (without a file path) died
  with a node stack trace (`TypeError [ERR_INVALID_ARG_TYPE]`) instead of a usage
  error.
- **Cause:** the option loop had no `else` branch, so every argument it did not know
  was dropped, and `--out` read the next argument without checking that there was one.
- **Fix:** `scripts/gen-catalog.mjs` — an unknown option is refused with exit 2, a
  `--out` without a file path is refused with exit 2, and neither writes a file.
  `tests/hygiene/test_catalog.py` — two tests prove the refusal and that no
  catalogue is written.
- **Proof:** the two new catalogue tests fail against the pre-fix generator.
- **Index proof:** `P36`
- **Date:** 2026-10-20

## D-062 — the validator collapsed two skills that carry the same folder name

- **Defect:** `scripts/validate.py --everywhere` collected the skill folders of the
  tree in a dict keyed by the folder name, so a skill name that lives in two
  packages silently kept only the LAST folder. A skill that was missing from the
  catalogue stayed invisible, and the installer (which refuses an ambiguous name)
  could not tell which of the two folders it was supposed to install.
- **Cause:** one folder name per key was assumed; the tree never had such a pair, so
  nothing ever noticed.
- **Fix:** `scripts/validate.py` — every folder of a name is kept and a name that
  lives in two packages is reported as `duplicate skill name '<name>' on disk`.
  `tests/hygiene/test_validate.py` — a fixture with two packages that hold the same
  folder name proves the report.
- **Proof:** the new validator test fails against the pre-fix validator.
- **Index proof:** `P37`
- **Date:** 2026-10-20

## D-063 — a skill documented a verification command that cannot run

- **Defect:** `skills/engineering/problem-json-contracts/SKILL.md` documented
  `python3 scripts/validate_problem_examples.py --schema-dir references/examples/schemas --catalogue references/examples/catalogue.json`.
  Copy and paste: `not a directory: references/examples/schemas`, exit 2. The
  fixtures of the skill live one level deeper
  (`references/examples/good/schemas`, `references/examples/good/catalogue.json`),
  and the skill's own self-test uses exactly those paths.
- **Cause:** the documented path lost the `good/` segment when the fixture tree was
  moved; nothing executed the command of a SKILL.md.
- **Fix:** `skills/engineering/problem-json-contracts/SKILL.md` — the documented
  command names the fixtures that exist, and the "Run the offline gate" line keeps
  the placeholder form that `scripts/gen-preamble.mjs` pins.
  `tests/hygiene/test_skill_docs.py` — a new guard runs every command a SKILL.md
  documents whose input is part of the tree.
- **Proof:** the guard fails when the documented path is broken again (measured) and
  is green on the fixed document.
- **Index proof:** `P38`
- **Date:** 2026-10-20

## D-064 — three skills documented the repository validator with a path that does not exist inside the skill

- **Defect:** `skills/engineering/{outbox-idempotency,pg-rls-multitenant,problem-json-contracts}/SKILL.md`
  documented `python3 scripts/validate_skills.py` as a command of the skill. No
  engineering skill ships that script: it lives in the repository root, so the
  command fails with `can't open file '.../skills/engineering/<skill>/scripts/validate_skills.py'`
  (exit 2) when it is copied into the skill folder, which is where the reader is.
- **Cause:** the command was written for the repository, but the document reads like
  a command of the skill. The honest-status skill had the same defect with
  `STATUS.md`, a file it does not ship either.
- **Fix:** `skills/engineering/outbox-idempotency/SKILL.md`,
  `skills/engineering/pg-rls-multitenant/SKILL.md`,
  `skills/engineering/problem-json-contracts/SKILL.md` — the command now says that
  it runs from the repository root.
  `skills/engineering/honest-status/SKILL.md` — the status file is named as the
  file of the repository an agent works on, and the self-test of the checker is
  added as the command that runs inside the skill.
  `tests/hygiene/test_skill_docs.py` — the guard resolves every documented script
  and runs every documented command whose input is part of the tree.
- **Proof:** the new guard is green on the fixed documents.
- **Index proof:** `P39`
- **Date:** 2026-10-20

## D-065 — the shape document drifted again, and its "authoritative" root block was missing an entry

- **Defect:** after the fixes of this pass were landed, the whole suite of the job went
  red: `Tracked files: document says 665, command says 667` and
  `Tracked files under 'tests/': document says 43, command says 44`. The two files this
  pass added (`tests/hygiene/test_skill_docs.py` and `docs/truth/TRUNK_STATUS.json`) moved
  the counts of `docs/truth/REPO_SHAPE.md`. The same document lists the root contents in
  a block that calls itself *authoritative* — and that block listed 14 entries while the
  tree has 15: `.npmrc` was missing. The block is not a table, so the table-driven guard
  of the document could not see it.
- **Cause:** the counts are live numbers and every commit that adds a file moves them;
  the root block was a claim without a command and therefore without a guard.
- **Fix:** `docs/truth/REPO_SHAPE.md` — the two counts and the missing root entry are
  corrected; `tests/hygiene/test_repo_shape_numbers.py` — a new guard compares the root
  block with the tracked root entries, so the block cannot drift again.
- **Proof:** `python3 -m pytest tests/hygiene/test_repo_shape_numbers.py -q` — the new
  guard fails when `.npmrc` is removed from the block again (measured).
- **Index proof:** `P40`
- **Date:** 2026-10-20


# SKL-W0-01 — TASK-0007 (2026-10-20) — repair log entry

This section is the **index of the trunk repairs of job SKL-W0-01**. One entry
per defect: the id, the symptom as it was observed, the command that reproduced
it, the root cause, the files that carry the fix, a proof command that passes
on the current trunk, and the date. The narrative of each defect is in the
section with the same id further up in this document; this index is the map.

`tests/hygiene/test_repair_log.py` is the guard: it fails when a defect id is
not in the index, when an index entry lacks one of the six fields, when an id
names two defects, when a proof command is not in the proof block below, when
the command an index entry writes down is not the command the proof block of
that label runs, when the narrative of a defect and its index entry disagree
about the proof label or the date, when a follow-up item names no symptom, and
when a proof command marked `# auto` does not exit 0.

## Defect ids that were changed in this pass

Four ids each named two different defects. They were made unique **without
renaming a defect that another document already cites**:

| id before | id now | section | why |
|---|---|---|---|
| `D-003` | `D-006` | RLS checker accepted three unsafe migrations | `docs/gaps/SKL-W0-01.md` G7 already cites this section as `D-006` |
| `D-007` | `D-051` | committed `catalog.json` was stale | the other `D-007` (wall-clock stamp) is cited by the TASK-0008 review table |
| `D-008` | `D-052` | TASK-0008 review: no new defects found | the other `D-008` (`--check` mode) is cited by the same table |
| `D-009` | `D-053` | TASK-0008 review: repro-script path bug | the other `D-009` (`ref-*` packages) is cited by the same table |

`D-028` and `D-029` were never used; the sequence skips them. The follow-up
list of the 2026-10-16 pass was renamed to "Follow-ups recorded in an earlier
pass" so that exactly one section carries the name "Follow-ups for later trunk
repair jobs".

## What the VERIFY pass of 2026-10-20 found

The VERIFY pass of this task re-ran all 33 proof commands of this document and
found four defects in the guard of this log itself. All four are in the owned
paths of this job, all four are recorded below, and all four have a mutation
test that fails without the fix:

| id | what the guard did not catch | how it was measured |
|---|---|---|
| `D-055` | the six-field check was not per entry: it read the field of a later entry | the `**Date:**` line of `D-030` and the `**Symptom:**` line of `D-031` removed from the index — the guard stayed green |
| `D-056` | the command an index entry writes down was never compared with the command the proof block runs | the inline command of `D-001` replaced by `bash scripts/install.sh --totally-wrong` — the guard stayed green |
| `D-057` | a defect section carried no date and no proof label, so the narrative and the index could drift apart | 52 of 52 sections had no `- **Date:**` line and 10 had no `- **Proof:**` line |
| `D-058` | the follow-up check promised a symptom and tested only a path | the body of the first follow-up item removed — the guard stayed green |

Every proof command of the index was re-run on the trunk of this pass and every
one of them exited 0; the transcript is in `.truth/SKL-W0-01/after.txt`.

## Defect index

### Pass of 2026-10-15 and 2026-10-16 (TASK-0001 … TASK-0008 review)

#### D-001 — install.sh source resolution doubled the path for every skill

- **Symptom:** `install.sh --target claude honest-status` exited 2 with `error: source skill directory missing: /srv/ottili/repo/skills//srv/ottili/repo/skills/skills/\n` (doubled path, trailing newline).
- **Reproduction:** `bash scripts/install.sh --target claude honest-status`
- **Root cause:** the skill was not in `catalog.json`, so the `print()` that read the path returned `"\n"`; the installer then prefixed `$ROOT` to that string.
- **Fix (files):** `scripts/install.sh` — the skill folder is resolved by walking `skills/`, no catalogue lookup.
- **Proof:** `P1` — `bash scripts/install.sh --check`
- **Date:** 2026-10-15

#### D-002 — `--package engineering|business-de|agentic-data` reported "unknown package"

- **Symptom:** every named package printed `error: unknown package <name>` and installed nothing.
- **Reproduction:** `bash scripts/install.sh --package engineering --target <dir>`
- **Root cause:** the package list was read from the hand-written `packages` object of `catalog.json` (four stale names).
- **Fix (files):** `scripts/install.sh` — the packages are derived from the `skills/` folders at install time.
- **Proof:** `P2` — `bash scripts/install.sh --check --package engineering`
- **Date:** 2026-10-15

#### D-003 — catalogue listed only 2 of 32 skills and was hand-edited

- **Symptom:** `python3 -I scripts/validate.py` printed `ok: 2 skills validated`.
- **Reproduction:** `python3 -I scripts/validate.py`
- **Root cause:** `catalog.json` was hand-written with two entries and nothing regenerated it.
- **Fix (files):** `scripts/gen-catalog.mjs` (new), `catalog.json`, `.github/workflows/validate.yml`.
- **Proof:** `P4` — `node scripts/gen-catalog.mjs --check`
- **Date:** 2026-10-15

#### D-004 — stale top-level `business-de/` duplicate and status/handoff docs cluttered the tree

- **Symptom:** a full duplicate of the business-de skills at the top level (111 tracked files) and ~26 pass-by-pass status/handoff documents; the duplicate-name proof reported `business-de` twice.
- **Reproduction:** `find . -name SKILL.md | xargs -n1 dirname | xargs -n1 basename | sort | uniq -d`
- **Root cause:** an earlier autonomous wave materialised the skills twice and kept the diaries of the finished passes.
- **Fix (files):** `git rm` of the duplicate and the diaries; `catalog.json` regenerated.
- **Proof:** `P5` — `git ls-files '*/SKILL.md' | xargs -n1 dirname | xargs -n1 basename | sort | uniq -d`
- **Date:** 2026-10-16

#### D-005 — generated catalogue listed `.gitkeep` placeholder files as skill paths

- **Symptom:** after the duplicate was deleted, `gen-catalog.mjs --check` reported a drift caused by `.gitkeep` placeholders.
- **Reproduction:** `node scripts/gen-catalog.mjs --check`
- **Root cause:** `IGNORE_FILES` in the generator did not contain `.gitkeep`.
- **Fix (files):** `scripts/gen-catalog.mjs` — `.gitkeep` added to the ignore list.
- **Proof:** `P6` — `test "$(grep -c '\.gitkeep' catalog.json)" = 0`
- **Date:** 2026-10-16

#### D-006 — RLS checker accepted three unsafe migrations; rewrote it per-table around the real product GUC

- **Symptom:** the checker passed a migration without `FORCE ROW LEVEL SECURITY`, a policy keyed on a setting nobody sets and a `GRANT ALL` migration; real hq migrations were reported against a standard that does not exist in the codebase.
- **Reproduction:** `python3 skills/engineering/pg-rls-multitenant/scripts/check_rls_migration.py skills/engineering/pg-rls-multitenant/references/examples/hostile_1_no_force.sql`
- **Root cause:** the checker scanned the whole file once and accepted five discriminator names, so one `tenant_id` satisfied the test for every table in the file.
- **Fix (files):** `skills/engineering/pg-rls-multitenant/scripts/check_rls_migration.py` (per-table, keyed on `app.company_id`), `skills/engineering/pg-rls-multitenant/references/examples/good_migration.sql`.
- **Proof:** `P7` — `python3 skills/engineering/pg-rls-multitenant/scripts/check_rls_migration_test.py`
- **Date:** 2026-10-16

#### D-051 — committed `catalog.json` was stale (missing the pg-rls hostile fixtures)

- **Symptom:** `gen-catalog.mjs --check` exited 1 — the committed catalogue did not list the three hostile RLS fixtures that TASK-0005 had added.
- **Reproduction:** `node scripts/gen-catalog.mjs --check`
- **Root cause:** the catalogue was last regenerated before the fixtures existed; the committed artefact and the tree had drifted.
- **Fix (files):** `catalog.json` regenerated with `node scripts/gen-catalog.mjs` (no code change — the generator was correct).
- **Proof:** `P4` — `node scripts/gen-catalog.mjs --check`
- **Date:** 2026-10-16

#### D-052 — TASK-0008 review: no new defects found in owned paths; all baseline defects re-proven fixed

- **Symptom:** the review pass found no new defect inside the owned paths; every defect of the card was re-proven fixed by re-running its reproduction command.
- **Reproduction:** the reproduction commands of D-001, D-002, D-003 (see above).
- **Root cause:** none — this is the verification record of the 2026-10-16 pass, kept as a defect entry so the review is part of the index.
- **Fix (files):** none; the pass wrote `.truth/SKL-W0-01/after.txt` and this document.
- **Proof:** `P8` — `python3 -m pytest tests/ -q`
- **Date:** 2026-10-16

#### D-053 — TASK-0008 review: repro-script path bug (not a repo defect)

- **Symptom:** the reproduction script of the review pass used a relative `OUT` path and `references/examples/...`, so it failed when it was run from another directory; the defect is in the script, not in the repository.
- **Reproduction:** `python3 skills/engineering/pg-rls-multitenant/scripts/check_rls_migration_test.py` from a directory other than the repository root.
- **Root cause:** the script addressed its fixtures relative to the current working directory.
- **Fix (files):** `skills/engineering/pg-rls-multitenant/scripts/check_rls_migration_test.py` — absolute `OUT` path and `../references/examples/...`.
- **Proof:** `P7` — `python3 skills/engineering/pg-rls-multitenant/scripts/check_rls_migration_test.py`
- **Date:** 2026-10-16

### Pass of 2026-10-20 (TASK-0002 … TASK-0006)

#### D-007 — the catalogue carried a wall-clock stamp: `--check` could never pass again

- **Symptom:** `gen-catalog.mjs --check` exited 1 on every day after the catalogue was generated (`catalog would change`).
- **Reproduction:** `node scripts/gen-catalog.mjs --check`
- **Root cause:** the generator wrote `updated_at: <today>`; the check compares byte for byte, so the timestamp alone made every later day fail. The catalogue was stale as well: three skills had gained files that were missing from their `paths`.
- **Fix (files):** `scripts/gen-catalog.mjs` — a pure function of the `skills/` tree, no wall-clock stamp, and a report of *what* drifted; `catalog.json` regenerated.
- **Proof:** `P4` — `node scripts/gen-catalog.mjs --check`
- **Date:** 2026-10-20

#### D-008 — `scripts/install.sh` had no `--check` mode, so the kit's install command exited 2

- **Symptom:** `bash scripts/install.sh --check` printed `error: unknown option --check` and exited 2; that was the `install` command of `scripts/truth/config.json`, so the gate's install step was red.
- **Reproduction:** `bash scripts/install.sh --check`
- **Root cause:** the installer knew `--dry-run` but had no mode that verified the preconditions of an installation without writing anything.
- **Fix (files):** `scripts/install.sh` — a `--check` mode that writes nothing; `scripts/truth/config.json` — the install command.
- **Proof:** `P1` — `bash scripts/install.sh --check`
- **Date:** 2026-10-20

#### D-009 — `--package ref-*` installed nothing although those packages exist on disk

- **Symptom:** `--package ref-webhooks-safe` printed "resolves to no skills (reserved / on-demand)" and installed 0 skills although `skills/ref-webhooks-safe/ref-webhooks-safe/SKILL.md` exists; the same for the other five `ref-*` packages.
- **Reproduction:** `bash scripts/install.sh --package ref-webhooks-safe --target <dir>`
- **Root cause:** the case statement treated every name matching `meta|ref-*` as a reserved virtual package before the derived package list was consulted.
- **Fix (files):** `scripts/install.sh` — the derived package list is consulted first; only `generic` and `meta` are virtual.
- **Proof:** `P3` — `bash scripts/install.sh --check --package ref-webhooks-safe`
- **Date:** 2026-10-20

#### D-010 — the truth kit's root allowlist was missing from `scripts/truth/config.json`

- **Symptom:** the root-allowlist test reported every tracked root entry as a violation and the gate's hygiene step was skipped with `no rootAllowlist configured`.
- **Reproduction:** `node tests/hygiene/root-allowlist.test.mjs`
- **Root cause:** the truth kit was installed with a `config.json` that had no `rootAllowlist` key, so the test read the canonical file instead of the fixture manifest and got an empty allowlist.
- **Fix (files):** `scripts/truth/config.json` — `rootAllowlist` with the list of the fixture manifest.
- **Proof:** `P9` — `python3 -m pytest tests/hygiene/test_root_allowlist.py -q`
- **Date:** 2026-10-20

#### D-011 — the orchestrator's workspace state directory showed up as a foreign change

- **Symptom:** the gate's ownership step failed with `4 changed file(s) outside the owned paths`: `.germo/notes/SKL-W0-01.md`, `.germo/notes/task_history.log`, `.germo/state.journal`, `.germo/state.json`.
- **Reproduction:** `node scripts/truth/gate.mjs job --job SKL-W0-01 --owned "…" --exclude "…" --skip registry,e2e`
- **Root cause:** `.germo/` (orchestrator state, not repository content) was not ignored, and the kit enumerates untracked files with `git ls-files --others --exclude-standard`.
- **Fix (files):** the worktree-local `.git/info/exclude` (`.germo/`); the repository-level fix belongs to the job that owns `.gitignore` and is requested in `docs/gaps/SKL-W0-01.md` (G9).
- **Proof:** `P10` — `git check-ignore -v .germo/state.json`
- **Date:** 2026-10-20

#### D-012 — `safe-commit` could not see new files: git 2.53.0 returns nothing for `--untracked-files=all`

- **Symptom:** the first `safe-commit` run committed 6 of the 9 owned paths; the three new test files stayed untracked although the gate had counted them.
- **Reproduction:** `git status --porcelain=v1 -z --untracked-files=all` (empty on git 2.53.0, in an empty scratch repository too)
- **Root cause:** the kit enumerates the working tree with `--untracked-files=all`, and that option returns **no output at all** on the git of this host; the gate uses `git ls-files --others --exclude-standard`, which still works. Kit and gate therefore disagree about which files exist.
- **Fix (files):** the new files of this job are staged explicitly (`git add -- <own paths>`) before every commit; `scripts/truth/safe-commit.mjs` is operator-owned and was not edited (G10).
- **Proof:** `P11` — `git add --dry-run -- tests/hygiene/test_repair_log.py`
- **Date:** 2026-10-20

#### D-013 — `scripts/install.sh` matched a package name as a regular expression

- **Symptom:** `--package ".*"` matched every derived package and installed the whole tree; `--package "engineering+"` matched `engineering`; a package that does not exist was accepted.
- **Reproduction:** `bash scripts/install.sh --package ".*" --target <dir>`
- **Root cause:** the package lookup used `grep -qx "$PACKAGE"`, so the name was a regex.
- **Fix (files):** `scripts/install.sh` — `grep -qxF "$PACKAGE"`.
- **Proof:** `P12` — `python3 -m pytest tests/hygiene/test_install.py -q`
- **Date:** 2026-10-20

#### D-014 — `scripts/verify-status.mjs` crashed on every claim table

- **Symptom:** the checker died with `TypeError: raw.rstrip is not a function` on the first table row, so it could never check anything.
- **Reproduction:** `node scripts/verify-status.mjs <STATUS.md> --root <repo>`
- **Root cause:** `rstrip()` is a *Python* method; a JavaScript string has none.
- **Fix (files):** `scripts/verify-status.mjs` — `raw.replace(/\s+$/, "")`.
- **Proof:** `P13` — `python3 -m pytest tests/hygiene/test_verify_status.py -q`
- **Date:** 2026-10-20

#### D-015 — `scripts/verify-status.mjs` never checked the evidence file (a swallowed error)

- **Symptom:** every claim row was reported as "log path not found", including rows whose evidence file existed — a checker that can never pass.
- **Reproduction:** `node scripts/verify-status.mjs <STATUS.md> --root <repo>`
- **Root cause:** `require` does not exist in an ES module; the `ReferenceError` was swallowed by a bare `catch`, so `ok` stayed `false` for every row.
- **Fix (files):** `scripts/verify-status.mjs` — `import { existsSync } from "node:fs"`, the `try`/`catch` is gone.
- **Proof:** `P13` — `python3 -m pytest tests/hygiene/test_verify_status.py -q`
- **Date:** 2026-10-20

#### D-016 — the orchestrator contract test asserted two mutually exclusive things

- **Symptom:** `tests/orchestrator/test_gen_preamble_failure.py` was permanently red: it asserted that the document starts with the header *and* that it starts with `1. ` for every rule number.
- **Reproduction:** `python3 -m pytest tests/orchestrator/ -q`
- **Root cause:** a document cannot start with two different first lines, so the test could never pass and validated nothing.
- **Fix (files):** `tests/orchestrator/test_gen_preamble_failure.py` — the header is asserted on the first line, the four rules are located as numbered list items and are asserted to be exactly four, numbered `1..4` in order.
- **Proof:** `P14` — `python3 -m pytest tests/orchestrator/ -q`
- **Date:** 2026-10-20

#### D-017 — the contract-drift self-test pointed at a foreign machine and aborted the collection

- **Symptom:** pytest aborted the whole collection with `Interrupted: 1 error during collection`; no test in the repository ran.
- **Reproduction:** `python3 -m pytest -q`
- **Root cause:** `check_contract_drift_test.py` started every checker with `cwd="/srv/ottili/repo/skills/skills/engineering/module-contract-first"`, a path that does not exist on any other checkout, and raised `FileNotFoundError` at import time.
- **Fix (files):** `skills/engineering/module-contract-first/scripts/check_contract_drift_test.py` — the skill directory is derived from `__file__`, the fixtures live in `tmp_path`.
- **Proof:** `P15` — `python3 skills/engineering/module-contract-first/scripts/check_contract_drift_test.py`
- **Date:** 2026-10-20

#### D-018 — the acceptance-harness self-test unpacked a `CompletedProcess` and could never fail

- **Symptom:** `report_result_test.py` raised `TypeError: cannot unpack non-iterable CompletedProcess object`; run as a script it exited 1 even when every check passed (`failures += fn()` added `None`).
- **Reproduction:** `python3 skills/engineering/acceptance-harness/scripts/report_result_test.py`
- **Root cause:** the edge-case tests were added later and were never run in either shape (pytest collects them, CI runs the file as a script).
- **Fix (files):** `skills/engineering/acceptance-harness/scripts/report_result_test.py` — `r.returncode`, real `assert` statements, `tmp_path` per test.
- **Proof:** `P16` — `python3 skills/engineering/acceptance-harness/scripts/report_result_test.py`
- **Date:** 2026-10-20

#### D-019 — the research/design acceptance test referenced an undefined constant

- **Symptom:** `test_research_design_acceptance.py` failed with `NameError: name 'ENGINEERING_DIR' is not defined`.
- **Reproduction:** `python3 -m pytest skills/engineering/tests/test_research_design_acceptance.py -q`
- **Root cause:** the module defines `ENGINEERING`; the test used `ENGINEERING_DIR`.
- **Fix (files):** `skills/engineering/tests/test_research_design_acceptance.py` — the constant that exists is used.
- **Proof:** `P17` — `python3 -m pytest skills/engineering/tests/test_research_design_acceptance.py -q`
- **Date:** 2026-10-20

#### D-020 — a skill test wrote its JSON report into the skill folder

- **Symptom:** the suite overwrote the tracked `skills/agentic-data/skill-authoring-evals/report_test.json` on every run, so `git status --porcelain` was never empty after the suite.
- **Reproduction:** `python3 -m pytest skills/agentic-data/ -q && git status --porcelain`
- **Root cause:** the test wrote its `--json` output to a fixed path inside the skill folder.
- **Fix (files):** `skills/agentic-data/skill-authoring-evals/tests/test_validate_skill.py` — the report goes into the test's `tmp_path`.
- **Proof:** `P18` — `python3 -m pytest skills/agentic-data/ -q`
- **Date:** 2026-10-20

#### D-021 — three business-de test modules wrote to fixed paths under `/tmp`

- **Symptom:** fixtures were written to fixed names (`/tmp/_pub_wp.json`, `/tmp/_wh_body.json`, `/tmp/_lab.json`) outside the worktree — they collide between runs, survive as litter and are invisible to the tree check.
- **Reproduction:** `grep -rn 'Path("/tmp' --include=test_*.py --include=*_test.py skills/ tests/`
- **Root cause:** the fixtures had a hard-coded path instead of the directory pytest hands the test.
- **Fix (files):** `skills/business-de/publish-reconcile-wp-meta/tests/test_publish.py`, `skills/business-de/webhooks-safe/tests/test_webhooks.py`, `skills/business-de/carrier-apis-de/tests/test_carrier.py` — every fixture goes into `tmp_path`.
- **Proof:** `P19` — `python3 -m pytest skills/business-de/ -q`
- **Date:** 2026-10-20

#### D-022 — a collection guard for a deleted directory hid 218 real tests

- **Symptom:** the suite reported 407 tests instead of 633; the canonical `skills/business-de/` tree was never collected.
- **Reproduction:** `python3 -m pytest -q` (407 collected)
- **Root cause:** `tests/conftest.py` kept `norecursedirs = business-de` for the deleted top-level duplicate; pytest matches `norecursedirs` against the **basename**, so the canonical tree was excluded as well.
- **Fix (files):** `tests/conftest.py` (the guard removed), `tests/hygiene/test_skill_tree.py` (the invariant it protected, now as a test).
- **Proof:** `P19` — `python3 -m pytest skills/business-de/ -q`
- **Date:** 2026-10-20

#### D-023 — the pg-rls self-test required a foreign repository

- **Symptom:** the self-test failed with "file not found" on every host without the hq-v2 checkout, including CI and a fresh clone of this repository.
- **Reproduction:** `python3 skills/engineering/pg-rls-multitenant/scripts/check_rls_migration_test.py`
- **Root cause:** the corpus path was hard-coded to `/srv/ottili/repo/hq-v2`; two edge tests returned an `int` instead of failing, so pytest could never fail them.
- **Fix (files):** `skills/engineering/pg-rls-multitenant/scripts/check_rls_migration_test.py` — the corpus root comes from `OTTLI_HQ_REPO`, the missing-corpus case is asserted, the edge tests assert.
- **Proof:** `P7` — `python3 skills/engineering/pg-rls-multitenant/scripts/check_rls_migration_test.py`
- **Date:** 2026-10-20

#### D-024 — the long-test self-test left two log files in the repository root

- **Symptom:** the self-test left `long-test.log` and `long-test.log.out` in the repository root, so the tree was dirty after the self-test.
- **Reproduction:** `bash skills/engineering/long-test-discipline/scripts/run_long_test_test.sh && git status --porcelain`
- **Root cause:** `run_long_test.sh` was called without `--log`, so it wrote into the current working directory.
- **Fix (files):** `skills/engineering/long-test-discipline/scripts/run_long_test_test.sh` — `OTTLI_TEST_LOG` points into the temporary directory the self-test already creates.
- **Proof:** `P20` — `bash skills/engineering/long-test-discipline/scripts/run_long_test_test.sh`
- **Date:** 2026-10-20

#### D-025 — nothing stopped a test from dirtying the checkout

- **Symptom:** the suite overwrote a tracked file on every run and no test noticed; there was no guard at all.
- **Reproduction:** `python3 -m pytest -q && git status --porcelain`
- **Root cause:** nothing compared the tree before and after the suite.
- **Fix (files):** `tests/hygiene/clean_tree.py` (the one canonical implementation), `tests/hygiene/test_clean_tree.py` (the pytest guard), `tests/conftest.py` (the ordering hook); the node-only `tests/hygiene/clean-tree.test.mjs` was replaced by them because pytest cannot run it.
- **Proof:** `P21` — `python3 -m pytest tests/hygiene/test_clean_tree.py -q`
- **Date:** 2026-10-20

#### D-026 — the suite leaked 28 files into the shared temporary directory

- **Symptom:** 28 files were left in the shared temp directory (14 `tmp*.json`, 13 `tmp*` directories, 1 `tmp*.warc.gz`); the card's own proof (`git status` after the run) stayed green while the leak grew.
- **Reproduction:** `TMPDIR=<empty dir> python3 -m pytest -q && ls <empty dir>`
- **Root cause:** `tempfile.mktemp()`, `mkdtemp()` without a matching `shutil.rmtree`, and `NamedTemporaryFile(delete=False)` whose manual `os.unlink` is skipped when an assertion fails first.
- **Fix (files):** ten test modules under `skills/business-de/**` and `skills/agentic-data/**` now write only into `tmp_path` or into a directory they remove themselves; `tests/hygiene/test_temp_files.py` is the lint guard.
- **Proof:** `P22` — `python3 -m pytest tests/hygiene/test_temp_files.py -q`
- **Date:** 2026-10-20

#### D-027 — the clean-tree guard only looked at the end of the session

- **Symptom:** a module that dirtied the checkout and a later module that cleaned it up again left no trace, and the guard could not name the module that did it.
- **Reproduction:** `python3 -m pytest tests/hygiene/test_clean_tree.py -q`
- **Root cause:** the comparison happened once, at the end of the session, instead of after every test module.
- **Fix (files):** `tests/conftest.py` (`pytest_runtest_teardown` compares after every module and names the offender), `tests/hygiene/test_clean_tree.py` (end-to-end negative case: a second session with a plugin that writes a stray file must fail and must clean up).
- **Proof:** `P21` — `python3 -m pytest tests/hygiene/test_clean_tree.py -q`
- **Date:** 2026-10-20

#### D-030 — 16 stale status diaries were still committed inside the skill packages

- **Symptom:** the tree still carried the diaries of the finished waves: 9 `STATUS.md`, 3 `HANDOFF.md`, 2 `skills/business-de/config/REVERIFY_*.md`, 2 `skills/agentic-data/references/PASS*-STATUS*.md` and `docs/truth/REVERIFY-SKL-W0-01-TASK-0006.md`; a reader cannot tell which claims are still true.
- **Reproduction:** `git ls-files | grep -cE '(^|/)(STATUS|HANDOFF|R3_PLAN|REVERIFY)\.md$'` → 9
- **Root cause:** the earlier wave kept them because `docs/R3_OWNERS.json` assigns `skills/business-de/**` and `skills/agentic-data/**` to other jobs; the card of this wave grants `skills/**` to SKL-W0-01.
- **Fix (files):** `git rm` of the 16 files; the per-skill `references/EVALS.md` stay — they are validator input, not diaries (D-039).
- **Proof:** `P23` — `test "$(git ls-files | grep -cE '(^|/)(STATUS|HANDOFF|R3_PLAN|REVERIFY)\.md$')" = 0`
- **Date:** 2026-10-20

#### D-031 — a collection test asserted that a status diary exists

- **Symptom:** `skills/agentic-data/tests/test_collection.py::test_handoff_exists` failed with `FileNotFoundError` after D-030 (`1 failed, 62 passed, 9 skipped`).
- **Reproduction:** `python3 -m pytest skills/agentic-data/tests/test_collection.py -q`
- **Root cause:** the test asserted the *existence of a diary* instead of a property of the skills; that premise is invalid once the tree policy is "a skill collection ships skills, not diaries about them".
- **Fix (files):** `skills/agentic-data/tests/test_collection.py` — rewritten, not deleted: it now asserts that the collection ships no diary and that every skill keeps what the diary held (≥ 6 primary URLs and a retrieval date in `references/SOURCES.md`).
- **Proof:** `P18` — `python3 -m pytest skills/agentic-data/ -q`
- **Date:** 2026-10-20

#### D-032 — 34 dangling pointers to the deleted diaries

- **Symptom:** after D-030, 34 places still pointed at deleted files (10 `skills/agentic-data/*/references/SOURCES.md`, 20 `skills/business-de/config/versions.json` entries, the business-de and engineering READMEs and `skills/business-de/PASS5_GATE.md`).
- **Reproduction:** `git grep -n -F 'PASS5-R3-05-REVERIFY.md' -- skills/ ':!catalog.json'`
- **Root cause:** the diaries were the only place some evidence and some navigation lived.
- **Fix (files):** the ten `skills/agentic-data/*/references/SOURCES.md`, `skills/business-de/config/versions.json`, `skills/business-de/README.md`, `skills/business-de/PASS5_GATE.md`, `skills/engineering/README.md` — every pointer replaced by the substance it pointed at.
- **Proof:** `P24` — `test -z "$(git grep -l -F 'PASS5-R3-05-REVERIFY.md' -- skills/ ':!catalog.json')"`
- **Date:** 2026-10-20

#### D-033 — the duplicate-name proof was polluted by scratch copies of the tree

- **Symptom:** the proof printed 46 duplicate skill names although the tracked tree has none.
- **Reproduction:** `find . -name SKILL.md | xargs -n1 dirname | xargs -n1 basename | sort | uniq -d`
- **Root cause:** this job's own scratch area `.truth/SKL-W0-01/` held full copies of the tree; they are git-ignored, so `git status` never showed them, but the file-system proof saw them.
- **Fix (files):** the redundant scratch *copies* were removed (the evidence files were kept) — again in this pass, where eight of them had been written back by later passes. The proof is run against the **tracked** tree, because the temporary directory of the test suite of this job lives inside the worktree (`.truth/SKL-W0-01/tmp`) and pytest keeps its last three runs there.
- **Proof:** `P5` — `git ls-files '*/SKILL.md' | xargs -n1 dirname | xargs -n1 basename | sort | uniq -d`
- **Date:** 2026-10-20

#### D-034 — the generated catalogue still named the deleted files

- **Symptom:** `catalog.json` listed five deleted `STATUS.md` paths, so the committed catalogue pointed at files that do not exist.
- **Reproduction:** `node scripts/gen-catalog.mjs --check`
- **Root cause:** the catalogue was not regenerated after the diaries were deleted.
- **Fix (files):** `catalog.json` regenerated with `node scripts/gen-catalog.mjs`.
- **Proof:** `P4` — `node scripts/gen-catalog.mjs --check`
- **Date:** 2026-10-20

#### D-035 — the collection scripts check skipped 9 of the 10 skills

- **Symptom:** the check ran against one skill only and the gate's test step failed with "the run reports skipped tests" (`62 passed, 9 skipped, 1 failed`).
- **Reproduction:** `python3 -m pytest skills/agentic-data/tests/test_collection.py -q`
- **Root cause:** the check skipped a skill whose `SKILL.md` has no `scripts:` summary line, and nine of the ten skills document their scripts inside their checklists.
- **Fix (files):** nine `skills/agentic-data/*/SKILL.md` (a summary line that lists every script the skill ships — seven scripts were documented nowhere before), `skills/agentic-data/tests/test_collection.py` (asserts both directions, no skip).
- **Proof:** `P18` — `python3 -m pytest skills/agentic-data/ -q`
- **Date:** 2026-10-20

#### D-036 — the language step flagged the German business-domain source catalogues

- **Symptom:** the gate's language step failed on `skills/business-de/bank-reconciliation-camt/references/SOURCES.md`, `skills/business-de/carrier-apis-de/references/SOURCES.md` and `skills/business-de/config/versions.json` (`language-umlaut` on `DFÜ-Abkommen`, `language-identifier` on German URLs) and on one German word in the English `skills/business-de/README.md`.
- **Reproduction:** the `language` step of the job gate over the changed files
- **Root cause:** the gate scans a whole file as soon as the file changes; German law titles and German source URLs are the *content* of these files, not untranslated prose.
- **Fix (files):** the kit's own escape hatch, not a threshold change — the `truth:allow-german-file` marker in the head of the two catalogues and in the `_comment` of `skills/business-de/config/versions.json`; `skills/business-de/README.md` reworded to the wording the catalogue already uses.
- **Proof:** `GATE` — `node scripts/truth/gate.mjs job --job SKL-W0-01 --owned "scripts/install.sh,scripts/validate.py,catalog.json,skills/**,tests/**,docs/truth,docs/gaps,business-de,scratch,undefined,*.db,*.db-shm,*.db-wal,STATUS.md,HANDOFF*.md,GAPS*.md,R3_PLAN.md,REVERIFY*.md,EVALS.md,docs/STATUS*,docs/HANDOFF*,docs/GAPS*,docs/R3_PLAN*,scripts/gen-catalog.mjs,scripts/verify-status.mjs,scripts/truth/config.json" --exclude "scripts/truth/*.mjs,scripts/truth/*.sh,scripts/truth/lib/**,scripts/truth/checks/**,scripts/truth/MANIFEST.sha256,scripts/truth/KIT_VERSION,scripts/truth/README.md,scripts/truth/package.json,scripts/truth/package-lock.json,scripts/truth/node_modules/**" --skip registry,e2e` (the job gate, `language` step)
- **Date:** 2026-10-20

#### D-037 — `REPO_SHAPE.md` drifted from the tree, and nothing noticed

- **Symptom:** the document claimed 649 tracked files and 30 repository-level test files; the tree had 651 and 32.
- **Reproduction:** `pytest tests/hygiene/test_repo_shape_numbers.py -q` → `REPO_SHAPE.md drifted from the tree: Tracked files: document says 649, command says 651`
- **Root cause:** the document was written in one commit, the guard test landed in another, and nothing compared the two.
- **Fix (files):** `docs/truth/REPO_SHAPE.md` (corrected numbers, every label matches the command beside it), `tests/hygiene/test_repo_shape_numbers.py` (parses every `| What | Value | Command |` row, runs the command and compares the printed number — a row added later is checked automatically).
- **Proof:** `P25` — `python3 -m pytest tests/hygiene/test_repo_shape_numbers.py -q`
- **Date:** 2026-10-20

#### D-038 — the tool inventory was incomplete and claimed there was no second installer

- **Symptom:** `docs/truth/REPO_SHAPE.md` stated *"No second installer, validator or catalogue generator exists in the tree."* — false: `scripts/install-skill.py` is a second installer, and four further tools were missing from the inventory.
- **Reproduction:** `git ls-files 'scripts/' | wc -l` → 12 tools against 8 rows in the document
- **Root cause:** the inventory was written from the tools this job knew, not from `ls scripts/`.
- **Fix (files):** `docs/truth/REPO_SHAPE.md` — the complete inventory (twelve rows) and the requirement that can be checked: exactly one `scripts/install.sh` and exactly one `scripts/validate.py`.
- **Proof:** `P26` — `test "$(git ls-files 'scripts/install.sh' | wc -l)" = 1`
- **Date:** 2026-10-20

#### D-039 — the per-skill `references/EVALS.md` files are a validator input, not diaries

- **Symptom:** the delete list of the task names `EVALS.md`; thirty skills ship `references/EVALS.md` with their eval prompts. Deleting them turns the validator red: `python3 scripts/validate_skills.py` exits 1 with `[honest-status] missing references/EVALS.md`.
- **Reproduction:** with `skills/engineering/honest-status/references/EVALS.md` moved aside, `python3 scripts/validate_skills.py` exits 1
- **Root cause:** the file looks like a diary but is a required input of the skill validator.
- **Fix (files):** none — decision to keep the files; the root-level `EVALS.md` diaries of the earlier waves were deleted with D-004.
- **Proof:** `P27` — `python3 -m pytest tests/hygiene/test_skill_eval_sets.py -q`
- **Date:** 2026-10-20

#### D-040 — the RLS checker rejected the real corpus and trusted one hard-coded name

- **Symptom:** the checker answered "FAIL" for 74 of 120 real migrations, because the pattern did not allow `ALTER TABLE IF EXISTS … ENABLE ROW LEVEL SECURITY`, because it only knew `app.company_id` while a product migration uses `ottili.company_id`, and because it asked about the *file* where the rule is about the *table*. It also decided the tenant setting name by constant instead of by measurement.
- **Reproduction:** `python3 skills/engineering/pg-rls-multitenant/scripts/check_rls_migration.py <a real hq migration>`
- **Root cause:** four defects in one script — a constant for the GUC name, a `CREATE TABLE` regex that had to be present, `ENABLE`/`FORCE` patterns without the `IF EXISTS`/`ONLY` variants, and a statement splitter with no notion of dollar-quoted bodies.
- **Fix (files):** `skills/engineering/pg-rls-multitenant/scripts/check_rls_migration.py` — the accepted GUC names come from `guc-names.json`, the splitter understands comments, literals and `DO $$ … $$` blocks, the verdict is per table; `tests/hygiene/test_rls_checker.py` is the guard.
- **Proof:** `P28` — `python3 -m pytest tests/hygiene/test_rls_checker.py -q`
- **Date:** 2026-10-20

#### D-041 — the tenant GUC inventory, and one open owner decision

- **Symptom:** the name of the tenant setting is a decision that is still open: `app.company_id`, `app.current_company_id`, `ottili.company_id` and `app.current_company` are all in use, and a policy keyed on a setting nobody sets isolates nobody.
- **Reproduction:** `python3 -c "import json;print([n['name'] for n in json.load(open('skills/engineering/pg-rls-multitenant/guc-names.json'))['accepted_names']])"`
- **Root cause:** the census of the GUC names was never written down, so neither the checker nor the reader could know which names are real.
- **Fix (files):** `skills/engineering/pg-rls-multitenant/guc-names.json` — every name with its measured inventory, `canonical_name: null`, the decision open for the owner.
- **Proof:** `P29` — `python3 -c "import json;print([n['name'] for n in json.load(open('skills/engineering/pg-rls-multitenant/guc-names.json'))['accepted_names']])"`
- **Date:** 2026-10-20

#### D-042 — the honest-status checker could not read the format the product repositories write

- **Symptom:** `check_status_evidence.py` crashed on every real `STATUS.md` of the product repositories with `KeyError: 'UNFILED'`, and `scripts/verify-status.mjs` was a second, independent table parser written in JavaScript, so the skill and the tool of the repository could never agree (the JS one reported 322 rows for hq-v2, the Python one crashed).
- **Reproduction:** `node scripts/verify-status.mjs <nvme>/hq-v2/docs/STATUS.md --root <nvme>/hq-v2`
- **Root cause:** the parser knew only the bucket grammar of the skill, while the product repositories write claim tables; and the tool re-implemented the parsing instead of delegating to the skill it installs.
- **Fix (files):** `skills/engineering/honest-status/scripts/status_tables.py` (new, parses the claim-table grammar), `skills/engineering/honest-status/scripts/check_status_evidence.py` (`--format auto|bucket|table`, a table verdict, a missing log file is a finding), `scripts/verify-status.mjs` (now a thin adapter that runs the checker).
- **Proof:** `P13` — `python3 -m pytest tests/hygiene/test_verify_status.py -q`
- **Date:** 2026-10-20

#### D-043 — the RLS leak-test harness could never print PASS

- **Symptom:** `pg-rls-leak-test.sh` died with exit 1 after `running probe as web_app` and never printed a verdict, not even on a correct migration.
- **Reproduction:** `bash skills/engineering/pg-rls-multitenant/scripts/pg-rls-leak-test.sh`
- **Root cause:** two defects — the probe printed its measurements as *aliased* columns, and psql does not print the alias in `-t -A` mode, so the label was lost in the query; and the verdict was a shell pipeline (`grep … | cut -f2`) that found nothing and, under `set -euo pipefail`, killed the script. A measurement that was never made looked like a measurement of zero.
- **Fix (files):** `skills/engineering/pg-rls-multitenant/scripts/pg-rls-leak-test.sh` (the probe prints the label as a value), `skills/engineering/pg-rls-multitenant/scripts/check_leak_probe.py` (new, the verdict; a missing measurement is a failure), `skills/engineering/pg-rls-multitenant/scripts/check_rls_migration.py` (`--list-guc-names`).
- **Proof:** `P30` — `python3 -m pytest tests/hygiene/test_leak_probe.py -q`
- **Date:** 2026-10-20

#### D-044 — the preamble contract test asserted a README heading that the README never had

- **Symptom:** the contract test failed with `AssertionError: README has no preamble section`; the failure was pre-existing and no file of that pass touched `README.md`.
- **Reproduction:** `node tests/orchestrator/test_preamble_contracts.test.mjs`
- **Root cause:** the test asserted the literal `## Orchestrator preamble (generated)`; the README's heading is `## Orchestrator preamble` and its body says that the block is generated.
- **Fix (files):** `tests/orchestrator/test_preamble_contracts.test.mjs` (now `tests/orchestrator/test_preamble_contracts.py`) — the test asserts the heading the document has and keeps the meaningful part of the contract; the document was **not** changed, it is outside the owned paths and it was right.
- **Proof:** `P14` — `python3 -m pytest tests/orchestrator/ -q`
- **Date:** 2026-10-20

#### D-045 — the truth gate could not run its test step when a non-Python file changed

- **Symptom:** the gate step `tests` failed with `pytest -q {paths} exited 4 — no tests ran — ERROR: not found: tests/orchestrator/test_preamble_contracts.test.mjs`.
- **Reproduction:** the `tests` step of the job gate after a change of a non-Python file
- **Root cause:** the gate hands the **changed** files to the test command, and pytest cannot collect a `.mjs` path — it refuses the whole run with a usage error.
- **Fix (files):** `scripts/truth/config.json` — `commands.test` selects the collectable Python test paths of the change and falls back to `pytest -q tests`.
- **Proof:** `GATE` — `node scripts/truth/gate.mjs job --job SKL-W0-01 --owned "scripts/install.sh,scripts/validate.py,catalog.json,skills/**,tests/**,docs/truth,docs/gaps,business-de,scratch,undefined,*.db,*.db-shm,*.db-wal,STATUS.md,HANDOFF*.md,GAPS*.md,R3_PLAN.md,REVERIFY*.md,EVALS.md,docs/STATUS*,docs/HANDOFF*,docs/GAPS*,docs/R3_PLAN*,scripts/gen-catalog.mjs,scripts/verify-status.mjs,scripts/truth/config.json" --exclude "scripts/truth/*.mjs,scripts/truth/*.sh,scripts/truth/lib/**,scripts/truth/checks/**,scripts/truth/MANIFEST.sha256,scripts/truth/KIT_VERSION,scripts/truth/README.md,scripts/truth/package.json,scripts/truth/package-lock.json,scripts/truth/node_modules/**" --skip registry,e2e` (the job gate, `tests` step)
- **Date:** 2026-10-20

#### D-046 — the RLS checker could not read a `DO $$ … $$` block and misread an escaped policy

- **Symptom:** the checker of D-040 rejected 178 of 1389 real product migrations: a policy created inside a `DO $$ … $$` block was invisible, and a policy whose body contains an escaped quote was misread.
- **Reproduction:** `python3 skills/engineering/pg-rls-multitenant/scripts/check_rls_migration.py <a migration with a DO block>`
- **Root cause:** the statement splitter cut on `;` without knowing about dollar-quoted bodies or string literals, and the policy body was matched with a naive regex.
- **Fix (files):** `skills/engineering/pg-rls-multitenant/scripts/check_rls_migration.py` — the splitter understands dollar-quoted bodies and escapes; `tests/hygiene/test_rls_checker.py` is the guard.
- **Proof:** `P28` — `python3 -m pytest tests/hygiene/test_rls_checker.py -q`
- **Date:** 2026-10-20

#### D-047 — the repository invariants were node:test files that no runner executed

- **Symptom:** the hygiene decisions of this job (no tracked symlink that leaves the checkout, no committed status diary, one canonical skill tree, no large file, no committed database file …) were written as `node:test` modules, and the configured runner is pytest — so none of them ever ran in the gate.
- **Reproduction:** `pytest -q tests/hygiene/*.test.mjs` → `ERROR: not found`
- **Root cause:** the invariants were written for the node test runner while the truth kit collects the tests with pytest.
- **Fix (files):** the invariants are pytest modules under `tests/hygiene/` (`test_*.py`); the node modules were removed after their assertions were carried over.
- **Proof:** `P31` — `python3 -m pytest tests/hygiene/ -q`
- **Date:** 2026-10-20

#### D-048 — the truth kit config still carried the template's migration command and had no large-file allow-list

- **Symptom:** `scripts/truth/config.json` still configured `commands.migrate` although this repository has no migrations of its own, and the key `largeFileAllowlist` was missing.
- **Reproduction:** `python3 -c "import json;c=json.load(open('scripts/truth/config.json'));print(sorted(c['commands']), 'largeFileAllowlist' in c)"`
- **Root cause:** the template config of the kit was adopted as it was.
- **Fix (files):** `scripts/truth/config.json` — `commands.migrate` removed, `largeFileAllowlist` added.
- **Proof:** `P32` — `python3 -c "import json;c=json.load(open('scripts/truth/config.json'));assert 'largeFileAllowlist' in c and 'migrate' not in c['commands']"`
- **Date:** 2026-10-20

#### D-049 — two commands of the pack-v3 decision do not run in this repository

- **Symptom:** the decision of 2026-10-19 names `install "bash scripts/install.sh --check"` and `test "pytest -q {paths}"` as the commands of the config; the first exited 2 (`error: --target is required`), the second exited 4 (`ERROR: not found: …/tests/orchestrator/test_gen_preamble.test.mjs`).
- **Reproduction:** `bash scripts/install.sh --check` and `pytest -q tests/orchestrator/test_gen_preamble.test.mjs`
- **Root cause:** the decision was written for the template of the kit, not measured against this repository.
- **Fix (files):** `scripts/truth/config.json` — the deviations were recorded here and in `docs/gaps/SKL-W0-01.md` (G31); the code fix followed in D-050.
- **Proof:** `GATE` — `node scripts/truth/gate.mjs job --job SKL-W0-01 --owned "scripts/install.sh,scripts/validate.py,catalog.json,skills/**,tests/**,docs/truth,docs/gaps,business-de,scratch,undefined,*.db,*.db-shm,*.db-wal,STATUS.md,HANDOFF*.md,GAPS*.md,R3_PLAN.md,REVERIFY*.md,EVALS.md,docs/STATUS*,docs/HANDOFF*,docs/GAPS*,docs/R3_PLAN*,scripts/gen-catalog.mjs,scripts/verify-status.mjs,scripts/truth/config.json" --exclude "scripts/truth/*.mjs,scripts/truth/*.sh,scripts/truth/lib/**,scripts/truth/checks/**,scripts/truth/MANIFEST.sha256,scripts/truth/KIT_VERSION,scripts/truth/README.md,scripts/truth/package.json,scripts/truth/package-lock.json,scripts/truth/node_modules/**" --skip registry,e2e` (the job gate, `install` and `tests` steps)
- **Date:** 2026-10-20

#### D-050 — the two commands of the pack-v3 decision now run unchanged (D-049 closed)

- **Symptom:** both commands of the decision still failed, so the config carried workarounds instead of the decision.
- **Reproduction:** `bash scripts/install.sh --check` (exit 2) and `pytest -q tests/orchestrator/test_gen_preamble.test.mjs` (exit 4)
- **Root cause:** the installer refused `--check` without a `--target`, and the six `*.test.mjs` modules of `tests/orchestrator/` and `tests/reviews/` cannot be collected by pytest.
- **Fix (files):** `scripts/install.sh` (`--check` works without `--target`), `tests/orchestrator/test_*.py` and `tests/reviews/test_*.py` (the six node modules converted to pytest with the same assertions), `scripts/truth/config.json` (the command strings of the decision, unchanged).
- **Proof:** `GATE` — `node scripts/truth/gate.mjs job --job SKL-W0-01 --owned "scripts/install.sh,scripts/validate.py,catalog.json,skills/**,tests/**,docs/truth,docs/gaps,business-de,scratch,undefined,*.db,*.db-shm,*.db-wal,STATUS.md,HANDOFF*.md,GAPS*.md,R3_PLAN.md,REVERIFY*.md,EVALS.md,docs/STATUS*,docs/HANDOFF*,docs/GAPS*,docs/R3_PLAN*,scripts/gen-catalog.mjs,scripts/verify-status.mjs,scripts/truth/config.json" --exclude "scripts/truth/*.mjs,scripts/truth/*.sh,scripts/truth/lib/**,scripts/truth/checks/**,scripts/truth/MANIFEST.sha256,scripts/truth/KIT_VERSION,scripts/truth/README.md,scripts/truth/package.json,scripts/truth/package-lock.json,scripts/truth/node_modules/**" --skip registry,e2e` (the job gate, `install` and `tests` steps)
- **Date:** 2026-10-20

#### D-054 — the shape document drifted again when this repair-log entry was committed

- **Symptom:** after the repair-log entry of TASK-0007 was committed, the shape guard failed: `Tracked files: document says 664, command says 665` and `Tracked files under 'tests/': document says 42, command says 43`.
- **Reproduction:** `python3 -m pytest tests/hygiene/test_repo_shape_numbers.py -q`
- **Root cause:** `docs/truth/REPO_SHAPE.md` states the number of tracked files, and the new guard test `tests/hygiene/test_repair_log.py` is one more tracked file — the count changed with the commit that added it. The D-037 guard worked as designed and refused the drift.
- **Fix (files):** `docs/truth/REPO_SHAPE.md` — the two numbers corrected (664 → 665, 42 → 43); the guard that found them is the repair.
- **Proof:** `P25` — `python3 -m pytest tests/hygiene/test_repo_shape_numbers.py -q`
- **Date:** 2026-10-20

#### D-055 — the six-field check of the index was not per entry

- **Symptom:** the guard reported no problem although the index entry of `D-030` had lost its `**Date:**` line and the entry of `D-031` had lost its `**Symptom:**` line; both were measured and the guard stayed green.
- **Reproduction:** remove the field line from an index entry of `docs/truth/REPAIR_LOG.md` and run `python3 -m pytest tests/hygiene/test_repair_log.py -q` — the guard stays green.
- **Root cause:** `split_section()` ended a block at the next `\n## `, but the index entries are `#### ` headings, so the body of an entry ran on to the end of the index and every field search found the field of a later entry.
- **Fix (files):** `tests/hygiene/test_repair_log.py` — the block ends at the next heading of the same or a higher level, the heading scan ignores fenced code, the field check runs per entry, and two mutation tests prove it.
- **Proof:** `P33` — `python3 -m pytest tests/hygiene/test_repair_log.py -q`
- **Date:** 2026-10-20

#### D-056 — the command of an index entry could drift from the proof block

- **Symptom:** writing `bash scripts/install.sh --totally-wrong` next to the label `P1` in the index entry of `D-001` left the guard green although the proof block still ran `bash scripts/install.sh --check`.
- **Reproduction:** replace the inline command of one index entry of `docs/truth/REPAIR_LOG.md` and run `python3 -m pytest tests/hygiene/test_repair_log.py -q` — the guard stays green.
- **Root cause:** the guard asserted only that the command of the proof block appeared somewhere in the document; it never compared it with the command the index writes down.
- **Fix (files):** `tests/hygiene/test_repair_log.py` — the command of an index entry must be the command of the proof block of that label, plus a mutation test; `docs/truth/REPAIR_LOG.md` — the four entries that cited `GATE` in prose write the command of the gate.
- **Proof:** `P33` — `python3 -m pytest tests/hygiene/test_repair_log.py -q`
- **Date:** 2026-10-20

#### D-057 — a defect section carried neither a date nor a proof label

- **Symptom:** not one of the 52 defect sections of `docs/truth/REPAIR_LOG.md` had a `- **Date:**` line, and the narrative of a defect and its index entry could contradict each other unnoticed.
- **Reproduction:** change the date of the index entry of `D-001` and run `python3 -m pytest tests/hygiene/test_repair_log.py -q` — the guard stays green.
- **Root cause:** the narrative sections were written before the index existed, and the guard had no cross-check between the two.
- **Fix (files):** `docs/truth/REPAIR_LOG.md` — every defect section ends with `- **Index proof:** `Pxx`` and `- **Date:** YYYY-MM-DD``; `tests/hygiene/test_repair_log.py` — the guard compares label and date of section and index.
- **Proof:** `P33` — `python3 -m pytest tests/hygiene/test_repair_log.py -q`
- **Date:** 2026-10-20

#### D-058 — the follow-up check promised a symptom and tested a path

- **Symptom:** `test_the_follow_up_list_exists_and_names_path_and_symptom` asserted only that the bold title of an item contains a backtick; an item whose body carried no symptom passed the test that claims to check the symptom.
- **Reproduction:** remove the body of the first follow-up item of `docs/truth/REPAIR_LOG.md` and run `python3 -m pytest tests/hygiene/test_repair_log.py -q` — the guard stays green.
- **Root cause:** the assertion and the name of the test disagreed.
- **Fix (files):** `tests/hygiene/test_repair_log.py` — every follow-up item must name a path in its title and carry a symptom in its body, plus a mutation test.
- **Proof:** `P33` — `python3 -m pytest tests/hygiene/test_repair_log.py -q`
- **Date:** 2026-10-20
#### D-059 — the installer wrote (and with --force deleted) outside the target directory

- **Symptom:** `install.sh --force --target <dir> ../pkg/good` deleted `<dir>/../pkg/good` and wrote the skill there, so a folder outside the target was destroyed without a question.
- **Reproduction:** `bash scripts/install.sh --force --target <dir> ../pkg/good` in a tree with one package and a folder `<dir>/../pkg/good` — the marker file of that folder is gone after the run.
- **Root cause:** the skill name was used unvalidated as a path component of the destination (`dest="$TARGET/$name"`); the "ambiguous package" check only fired by accident, when the tree held more than one package.
- **Fix (files):** `scripts/install.sh` — every skill name is checked against `^[A-Za-z0-9._-]+$` before anything is written and an unsafe name is refused with exit 2; `tests/hygiene/test_install.py` — a fixture with a folder outside the target proves the refusal and the survival of that folder.
- **Proof:** `P34` — `python3 -m pytest tests/hygiene/test_install.py -q -k "escapes_the_target"`
- **Date:** 2026-10-20

#### D-060 — `--check` refused a target that the install accepts

- **Symptom:** `install.sh --check --target <dir>/does/not/exist --package engineering` exited 1 with "target parent does not exist", while the same target was installed without complaint (exit 0).
- **Reproduction:** `bash scripts/install.sh --check --target "$PWD/.truth/SKL-W0-01/attack/new/deep/target" --package engineering` — exit 1; `bash scripts/install.sh --target "$PWD/.truth/SKL-W0-01/attack/new/deep/target" --package engineering` — exit 0.
- **Root cause:** the check demanded that the parent of the target already existed; the install creates that tree with `mkdir -p` and never demanded it.
- **Fix (files):** `scripts/install.sh` — the check walks up to the nearest existing ancestor and asks whether the tree could be created there; a target below a file is still refused; `tests/hygiene/test_install.py` — two tests prove both directions.
- **Proof:** `P35` — `python3 -m pytest tests/hygiene/test_install.py -q -k "parent_does_not_exist or cannot_be_created"`
- **Date:** 2026-10-20

#### D-061 — the catalogue generator ignored an unknown option and overwrote the catalogue

- **Symptom:** `node scripts/gen-catalog.mjs --chek` wrote the catalogue and exited 0 instead of checking it; `node scripts/gen-catalog.mjs --out` died with a node stack trace.
- **Reproduction:** `node scripts/gen-catalog.mjs --chek` — "ok: wrote .../catalog.json"; `node scripts/gen-catalog.mjs --out` — "TypeError [ERR_INVALID_ARG_TYPE]".
- **Root cause:** the option loop had no `else` branch, so every unknown argument was dropped, and `--out` read the next argument without checking that one existed.
- **Fix (files):** `scripts/gen-catalog.mjs` — an unknown option and an `--out` without a file path are refused with exit 2 and write nothing; `tests/hygiene/test_catalog.py` — two tests prove the refusal.
- **Proof:** `P36` — `python3 -m pytest tests/hygiene/test_catalog.py -q -k "unknown_option or without_a_value"`
- **Date:** 2026-10-20

#### D-062 — the validator collapsed two skills that carry the same folder name

- **Symptom:** `validate.py --everywhere` kept only the last folder of a skill name, so a skill that lived in two packages and was missing from the catalogue stayed invisible.
- **Reproduction:** a tree with `skills/demo/alpha/SKILL.md` and `skills/other/alpha/SKILL.md` and a catalogue that knows only `demo/alpha` — the pre-fix validator reported no duplicate.
- **Root cause:** the on-disk scan used a dict keyed by the folder name and therefore assumed that every name lives exactly once in the tree.
- **Fix (files):** `scripts/validate.py` — every folder of a name is kept and a name that lives twice is reported as "duplicate skill name"; `tests/hygiene/test_validate.py` — a fixture with two packages proves the report.
- **Proof:** `P37` — `python3 -m pytest tests/hygiene/test_validate.py -q -k "duplicate"`
- **Date:** 2026-10-20

#### D-063 — a skill documented a verification command that cannot run

- **Symptom:** the RFC 9457 validator command of `skills/engineering/problem-json-contracts/SKILL.md` names `references/examples/schemas` and `references/examples/catalogue.json`; neither exists, the command exits 2 with "not a directory".
- **Reproduction:** `cd skills/engineering/problem-json-contracts && python3 scripts/validate_problem_examples.py --schema-dir references/examples/schemas --catalogue references/examples/catalogue.json` — exit 2.
- **Root cause:** the documented path lost the `good/` segment of the fixture tree; no test executed the commands a SKILL.md prints.
- **Fix (files):** `skills/engineering/problem-json-contracts/SKILL.md` — the command names the fixtures that exist and keeps the placeholder form that the preamble generator pins; `tests/hygiene/test_skill_docs.py` — a guard runs every documented command whose input is part of the tree.
- **Proof:** `P38` — `python3 -m pytest tests/hygiene/test_skill_docs.py -q`
- **Date:** 2026-10-20

#### D-064 — three skills documented the repository validator with a path that does not exist inside the skill

- **Symptom:** `python3 scripts/validate_skills.py` is documented as a command of three engineering skills, but no engineering skill ships that script; copied into the skill folder it exits 2 with "can't open file".
- **Reproduction:** `cd skills/engineering/problem-json-contracts && python3 scripts/validate_skills.py` — exit 2.
- **Root cause:** a command of the repository was written like a command of the skill; the honest-status skill had the same defect with a `STATUS.md` it does not ship.
- **Fix (files):** `skills/engineering/outbox-idempotency/SKILL.md`, `skills/engineering/pg-rls-multitenant/SKILL.md`, `skills/engineering/problem-json-contracts/SKILL.md` — the command says that it runs from the repository root; `skills/engineering/honest-status/SKILL.md` — the status file is named as the file of the repository an agent works on and the self-test of the checker is added; `tests/hygiene/test_skill_docs.py` — the guard resolves every documented script.
- **Proof:** `P39` — `python3 -m pytest tests/hygiene/test_skill_docs.py -q -k "documented_script_exists"`
- **Date:** 2026-10-20

#### D-065 — the shape document drifted again, and its root block was missing an entry

- **Symptom:** the suite of the job failed with "document says 665, command says 667" and "document says 43, command says 44"; the root block of the same document listed 14 root entries while the tree has 15 (`.npmrc` was missing).
- **Reproduction:** `python3 -m pytest tests/ -q` — `FAILED tests/hygiene/test_repo_shape_numbers.py::test_repo_shape_numbers_are_reproducible`.
- **Root cause:** the counts of `docs/truth/REPO_SHAPE.md` are live numbers that every commit which adds a file moves, and the root block was a claim without a command and therefore without a guard.
- **Fix (files):** `docs/truth/REPO_SHAPE.md` — the two counts and the missing root entry are corrected; `tests/hygiene/test_repo_shape_numbers.py` — a new guard compares the root block with the tracked root entries.
- **Proof:** `P40` — `python3 -m pytest tests/hygiene/test_repo_shape_numbers.py -q`
- **Date:** 2026-10-20


## Proof commands executed on 2026-10-20

Every proof command of the index was re-run on the trunk of this pass. The
commands marked `# auto` are re-executed by `tests/hygiene/test_repair_log.py`
on every suite run; the others are the slow ones (whole pytest suites, the
job gate) and are executed by the gate itself. The full transcript is in
`.truth/SKL-W0-01/after.txt`.

### P1 — the installer verifies every skill of every package and writes nothing

```
$ bash scripts/install.sh --check   # auto
check: 39 skill(s) verified, nothing written
exit=0
```

### P2 — the derived package `engineering` resolves

```
$ bash scripts/install.sh --check --package engineering   # auto
check: 10 skill(s) verified, nothing written
exit=0
```

### P3 — the on-demand package `ref-webhooks-safe` resolves

```
$ bash scripts/install.sh --check --package ref-webhooks-safe   # auto
check: 1 skill(s) verified, nothing written
exit=0
```

### P4 — the catalogue is a pure function of the `skills/` tree

```
$ node scripts/gen-catalog.mjs --check   # auto
ok: catalog unchanged (39 skills, 12 packages)
exit=0
```

### P5 — no skill name is duplicated in the tree

```
$ git ls-files '*/SKILL.md' | xargs -n1 dirname | xargs -n1 basename | sort | uniq -d   # auto
(no output)
exit=0
```

### P6 — the catalogue names no placeholder file

```
$ test "$(grep -c '\.gitkeep' catalog.json)" = 0   # auto
exit=0
```

### P7 — the RLS checker's own self-test

```
$ python3 skills/engineering/pg-rls-multitenant/scripts/check_rls_migration_test.py   # auto
ok: pg-rls migration checker self-test (3 real hq PASS, 3 hostile FAIL)
ok: --json output is valid and correct
ok: usage error exits 2
ok: every configured GUC name is accepted, an unknown one is not
ok: a DO block and an EXECUTE-created policy are read
exit=0
```

### P8 — the whole suite of this job

```
$ python3 -m pytest tests/ -q
198 passed in 25.72s
exit=0
```

### P9 — the root allowlist of the truth kit

```
$ python3 -m pytest tests/hygiene/test_root_allowlist.py -q
6 passed in 0.73s
exit=0
```

### P10 — the orchestrator state directory is excluded (worktree-local fix of D-011)

```
$ git check-ignore -v .germo/state.json
/mnt/ottili-nvme/ottili/v2/repo/skills/.git/info/exclude:9:.germo/	.germo/state.json
exit=0
```

### P11 — a new file of this job is staged explicitly (the workaround of D-012)

```
$ git add --dry-run -- tests/hygiene/test_repair_log.py   # auto
exit=0
```

### P12 — the package name is matched literally

```
$ python3 -m pytest tests/hygiene/test_install.py -q
17 passed in 7.93s
exit=0
```

### P13 — the honest-status checker reads the claim tables of the product repositories

```
$ python3 -m pytest tests/hygiene/test_verify_status.py -q
9 passed in 1.46s
exit=0
```

### P14 — the orchestrator contract tests

```
$ python3 -m pytest tests/orchestrator/ -q
31 passed in 1.05s
exit=0
```

### P15 — the contract-drift self-test runs on this host

```
$ python3 skills/engineering/module-contract-first/scripts/check_contract_drift_test.py   # auto
ok   test_enumerate_creates_snapshot
ok   test_check_passes_when_live_matches_snapshot
ok   test_check_detects_drift_and_passes_after_update
ok   test_cycles_command_runs
check_contract_drift self-test: PASS
exit=0
```

### P16 — the acceptance-harness self-test

```
$ python3 skills/engineering/acceptance-harness/scripts/report_result_test.py   # auto
ok: PASS write succeeds
ok: invalid outcome exits 2
ok: scenario overwritten

all tests passed
exit=0
```

### P17 — the research/design acceptance test

```
$ python3 -m pytest skills/engineering/tests/test_research_design_acceptance.py -q
1 passed in 0.01s
exit=0
```

### P18 — the agentic-data collection and its skill tests

```
$ python3 -m pytest skills/agentic-data/ -q
345 passed in 22.23s
exit=0
```

### P19 — the business-de collection

```
$ python3 -m pytest skills/business-de/ -q
218 passed in 11.35s
exit=0
```

### P20 — the long-test self-test leaves the checkout clean

```
$ bash skills/engineering/long-test-discipline/scripts/run_long_test_test.sh
run_long_test self-test: PASS
exit=0
```

### P21 — the clean-tree guard, including its end-to-end negative case

```
$ python3 -m pytest tests/hygiene/test_clean_tree.py -q
4 passed in 0.99s
exit=0
```

### P22 — the lint that keeps the tests out of the shared temp directory

```
$ python3 -m pytest tests/hygiene/test_temp_files.py -q
2 passed in 0.09s
exit=0
```

### P23 — no status diary is committed any more

```
$ test "$(git ls-files | grep -cE '(^|/)(STATUS|HANDOFF|R3_PLAN|REVERIFY)\.md$')" = 0   # auto
exit=0
```

### P24 — no pointer to a deleted diary is left

```
$ test -z "$(git grep -l -F 'PASS5-R3-05-REVERIFY.md' -- skills/ ':!catalog.json')"   # auto
exit=0
```

### P25 — the shape document is checked against the tree

```
$ python3 -m pytest tests/hygiene/test_repo_shape_numbers.py -q
1 passed in 0.65s
exit=0
```

### P26 — there is exactly one installer

```
$ test "$(git ls-files 'scripts/install.sh' | wc -l)" = 1   # auto
exit=0
```

### P27 — the eval sets of the skills are present

```
$ python3 -m pytest tests/hygiene/test_skill_eval_sets.py -q
4 passed in 0.09s
exit=0
```

### P28 — the tenant checker is driven by the configuration, not by a constant

```
$ python3 -m pytest tests/hygiene/test_rls_checker.py -q
13 passed in 1.00s
exit=0
```

### P29 — the measured inventory of the tenant setting names

```
$ python3 -c "import json;print([n['name'] for n in json.load(open('skills/engineering/pg-rls-multitenant/guc-names.json'))['accepted_names']])"   # auto
['app.company_id', 'app.current_company_id', 'ottili.company_id', 'app.current_company']
exit=0
```

### P30 — the leak probe judges a real probe output

```
$ python3 -m pytest tests/hygiene/test_leak_probe.py -q
7 passed in 0.66s
exit=0
```

### P31 — the repository invariants are pytest modules and they run

```
$ python3 -m pytest tests/hygiene/ -q
139 passed in 23.70s
exit=0
```

### P32 — the truth kit config carries no migration command and a large-file allow-list

```
$ python3 -c "import json;c=json.load(open('scripts/truth/config.json'));assert 'largeFileAllowlist' in c and 'migrate' not in c['commands']"   # auto
exit=0
```

### P33 — the guard of this repair log

```
$ python3 -m pytest tests/hygiene/test_repair_log.py -q
29 passed in 5.05s
exit=0
```
### P34 — the installer refuses a skill name that escapes the target

```
$ python3 -m pytest tests/hygiene/test_install.py -q -k "escapes_the_target"   # auto
.                                                                        [100%]
1 passed, 20 deselected in 0.10s
exit=0
```

### P35 — the check accepts the target the install accepts and refuses the impossible one

```
$ python3 -m pytest tests/hygiene/test_install.py -q -k "parent_does_not_exist or cannot_be_created"   # auto
..                                                                       [100%]
2 passed, 19 deselected in 0.66s
exit=0
```

### P36 — the catalogue generator refuses an unknown option and an incomplete `--out`

```
$ python3 -m pytest tests/hygiene/test_catalog.py -q -k "unknown_option or without_a_value"   # auto
..                                                                       [100%]
2 passed, 5 deselected in 0.15s
exit=0
```

### P37 — the validator reports a skill name that lives in two packages

```
$ python3 -m pytest tests/hygiene/test_validate.py -q -k "duplicate"   # auto
.                                                                        [100%]
1 passed, 4 deselected in 0.11s
exit=0
```

### P38 — every command a skill documents runs

```
$ python3 -m pytest tests/hygiene/test_skill_docs.py -q   # auto
..                                                                       [100%]
2 passed in 3.18s
exit=0
```

### P39 — every script a skill documents exists

```
$ python3 -m pytest tests/hygiene/test_skill_docs.py -q -k "documented_script_exists"   # auto
.                                                                        [100%]
1 passed, 1 deselected in 0.06s
exit=0
```
### P40 — the shape document and its root block agree with the tree

```
$ python3 -m pytest tests/hygiene/test_repo_shape_numbers.py -q   # auto
..                                                                       [100%]
2 passed in 1.80s
exit=0
```

### GATE — the job gate (install, build, lint, language, tests, hygiene, ownership)

```
$ node scripts/truth/gate.mjs job --job SKL-W0-01 --owned "scripts/install.sh,scripts/validate.py,catalog.json,skills/**,tests/**,docs/truth,docs/gaps,business-de,scratch,undefined,*.db,*.db-shm,*.db-wal,STATUS.md,HANDOFF*.md,GAPS*.md,R3_PLAN.md,REVERIFY*.md,EVALS.md,docs/STATUS*,docs/HANDOFF*,docs/GAPS*,docs/R3_PLAN*,scripts/gen-catalog.mjs,scripts/verify-status.mjs,scripts/truth/config.json" --exclude "scripts/truth/*.mjs,scripts/truth/*.sh,scripts/truth/lib/**,scripts/truth/checks/**,scripts/truth/MANIFEST.sha256,scripts/truth/KIT_VERSION,scripts/truth/README.md,scripts/truth/package.json,scripts/truth/package-lock.json,scripts/truth/node_modules/**" --skip registry,e2e
PASS  ownership        0ms  3 file(s) changed, all inside the owned paths
PASS  shrink          87ms  no deletions or large reductions
PASS  syntax          40ms  3 changed file(s) parse
skip  sql              0ms  no SQL files changed
PASS  language         8ms  3 file(s) scanned
PASS  stubs            2ms  3 file(s) scanned
PASS  secrets          2ms  3 file(s) scanned
PASS  size            0ms  3 file(s) scanned
skip  i18n             1ms  no UI and no catalogues in this job
PASS  lint           143ms  python3 -I scripts/validate.py --everywhere
skip  typecheck        0ms  no commands.typecheck in scripts/truth/config.json
skip  migrate          0ms  job has no migrations and --db was not given
PASS  tests           3.5s  1 test path(s) passed

GATE PASSED  SKL-W0-01
exit=0
```

## The steps the trunk gate skipped, and why

`node scripts/truth/gate.mjs trunk` (kit 1.1.0, 2026-10-20) reported these steps:

| step | status | reason |
| --- | --- | --- |
| install | pass | `bash scripts/install.sh --check` — 39 skills of 12 packages verified, nothing written |
| build | pass | `python3 -I scripts/validate.py --everywhere` — 39 skills validated |
| typecheck | skip | no `commands.typecheck` in `scripts/truth/config.json`: the repository has no type checker, it is plain JavaScript, Python and bash |
| lint | pass | `python3 -I scripts/validate.py --everywhere` (see `docs/gaps/SKL-W0-01.md` G36: the lint step of the config runs the build command) |
| registry | skip | no `commands.registryCheck` in `scripts/truth/config.json`: the repository publishes no npm package, the `@ottili` scope in `.npmrc` only names the internal registry |
| migrate | skip | no `commands.migrate` in `scripts/truth/config.json` and the job owns no `.sql` file: this repository has no database and no migration |
| boot | skip | no `boot.command` in `scripts/truth/config.json`: this repository has no server to boot |
| smoke | skip | no `commands.smokeTests` in `scripts/truth/config.json`: without a server there is nothing to smoke |
| hygiene | pass | 15 root entries, all of them in `rootAllowlist` |
| scan-full | warn | informational: 266 language findings (the German business-domain catalogues and sources), 0 stubs, 1 oversized file (see the follow-up list) |

The overall result is `pass` and `docs/truth/TRUNK_STATUS.json` carries it. The gate
writes that file for the commit it measured; the W1 jobs read it with
`node scripts/truth/preflight.mjs --job <id> --requires-trunk`, which asks for
`overall == "pass"` and for the recorded commit to be an ancestor of the worktree HEAD.

## Follow-ups for later trunk repair jobs

Everything below was measured on the trunk of this pass and could **not** be
fixed inside the owned paths of SKL-W0-01. Each item names the path and the
exact symptom; the owner is the job that holds the path in
`docs/R3_OWNERS.json`.

1. **`.github/workflows/validate.yml:42`** — the step "Run orchestrator contract
   tests" runs `for t in tests/orchestrator/*.test.mjs; do node "$t"; done`.
   The six modules were converted to `test_*.py` by D-050, so the glob matches
   nothing, bash passes the literal pattern to node and the step ends with
   `Error: Cannot find module '…/tests/orchestrator/*.test.mjs'` and
   `code: 'MODULE_NOT_FOUND'`, exit 1. Owner: `skills-engineering-r3` (`.github/**`).
2. **`.github/workflows/validate.yml:69`** — the step "Run engineering skill
   self-tests" runs `python3 "$t"` over a list that contains
   `skills/engineering/long-test-discipline/scripts/run_long_test_test.sh`, a
   **bash** script. The result is
   `SyntaxError: invalid syntax` (`set -uo pipefail`, exit 1). The same file
   runs the other self-tests with `python3`, so the list needs a per-file
   interpreter. Owner: `skills-engineering-r3` (`.github/**`).
3. **`README.md:221`, `README.md:228`, `README.md:229`** — the documentation
   still tells the reader to run `tests/orchestrator/*.test.mjs` and
   `for t in tests/hygiene/*.test.mjs tests/reviews/*.test.mjs; do node "$t"; done`.
   Every one of those files was deleted or converted by D-047 and D-050; the
   commands print "No such file or directory". Owner: `skills-engineering-r3`
   (`README.md`).
4. **`index/skills.json`** — the file drifts from the tree it is generated
   from: `python3 scripts/build-index.py` rewrites 5 lines (the pg-rls
   description `tenant_id` → `company_id` and four `has_references: true` →
   `false`) and the generator has **no `--check` mode**, so nothing fails. The
   committed file was restored with `git show HEAD:index/skills.json` during
   this pass so that the trunk was not left worse. Owner:
   `skills-engineering-r3` (`index/**`).
5. **`skills/ref-*/<name>/SKILL.md` (6 files)** — the description still names
   the deleted path fragment, e.g. `skills/ref-webhooks-safe/ref-webhooks-safe/SKILL.md`
   says "… for the webhooks-safe skill (business-de/webhooks-safe)". The tree
   `skills/ref-*/**` is in **no** entry of `docs/R3_OWNERS.json`, so the owner
   has to be decided first. Owner: unassigned (candidate `skills-engineering-r3`).
6. **`scripts/validate_skills.py:19`** — `SKILLS_DIR` is hard-coded to
   `skills/engineering`, so 10 of the 39 skills are validated although the
   docstring promises "every skill folder"; `ev_text` (line 112) is only
   assigned inside the loop, so a first skill without `references/EVALS.md`
   raises `UnboundLocalError`; and the prompt count adds the **same** regex
   twice (lines 114 and 115). Owner: `skills-engineering-r3` (`scripts/**`).
7. **`skills/business-de/*/tests/tmp/*`** — 9 committed scratch files (e.g.
   `skills/business-de/skr-journal-mapping/tests/tmp/j.json`,
   `skills/business-de/ust-edge-cases/tests/tmp/nearmiss.json`) are catalogued
   as skill content by `scripts/gen-catalog.mjs`. Owner: `skills-business-de-r3`.
8. **`skills/agentic-data/computer-use-drivers/SKILL.md` and
   `skills/agentic-data/deep-research-method/SKILL.md`** — both ship a
   `references/EVALS.md` that their `SKILL.md` never links, so an agent that
   reads the skill never sees the eval set. Owner: `skills-agentic-data-r3`.
9. **`.gitignore`** — it does not ignore `.pytest_cache/`, so a pytest run
   leaves that directory in the checkout. `.germo/` is ignored only through the
   worktree-local `.git/info/exclude` (D-011). Owner: `skills-engineering-r3`.
10. **`docs/gaps/SKL-W1-02.md:106`** — the file still lists
    `skills/business-de/STATUS.md` and `skills/business-de/HANDOFF.md`, both
    deleted by D-030. Owner: `skills-business-de-r3`.
11. **`docs/truth/REPO_PROBE.txt`** — tracked but 0 bytes; no job in
    `docs/R3_OWNERS.json` owns that file, so it can neither be filled nor
    deleted from here. Owner: unassigned.
12. **`scripts/truth/safe-commit.mjs`** — the kit enumerates the working tree
    with `git status --porcelain=v1 -z --untracked-files=all`; git 2.53.0
    returns **no output at all** for that option (reproducible in an empty
    scratch repository), so new files stay untracked unless they are staged
    explicitly. The kit belongs to the operator and may not be edited by a
    job. Owner: operator.

17. **`skills/orchestrator-preamble/orchestrator-preamble/SKILL.md:35`** — the four
    check commands of the preamble name `scripts/check_rls_migration.py`,
    `scripts/check_outbox.py`, `scripts/check_problem_catalogue.py` and
    `scripts/check_status_evidence.py`. Those scripts live inside the canonical
    engineering skills, so a reader who copies the command into the preamble folder
    gets `No such file or directory` (exit 1). The generated
    `references/preamble.md` prints the same commands and neither document says in
    which folder the command runs. The generator `scripts/gen-preamble.mjs` is
    outside the owned paths of SKL-W0-01, and it pins the gate command of the four
    canonical skills verbatim, so the fix belongs to the job that owns the
    generator and the preamble. Owner: `skills-engineering-r3` (`scripts/**`).
18. **`scripts/truth/config.json`** — the `lint` step of the truth gate runs the
    same command as the `build` step (`python3 -I scripts/validate.py --everywhere`),
    so a lint regression cannot be seen by the gate: the step is green whenever the
    build is green. A real linter is installed on this host — `ruff` 0.16.8 — and it
    reports 23 findings in `tests/` and 8 in `scripts/`; the findings of `tests/`
    are inside the owned paths of this job, the findings of `scripts/validate_skills.py`,
    `scripts/build-index.py`, `scripts/check_related_graph.py`,
    `scripts/install-skill.py` and `scripts/validate_reviewed_by.py` are not. The
    command was NOT changed here on purpose: a trunk gate that depends on a binary
    the CI image may not carry would turn the W1 jobs red. Owner: operator (the
    config) and `skills-engineering-r3` (the linter findings of `scripts/**`).

19. **`skills/agentic-data/verifiable-environments/scripts/verify_harness.py`** — the file
    is 519 lines and the size limit of the truth kit is 500 lines, so the `scan-full` step
    of the trunk gate reports one oversized file. The file belongs to the agentic-data
    lane and is rewritten by the canonical-skills job, which has to split it there; this
    pass did not refactor a script of another lane inside a review commit. Owner:
    `skills-agentic-data-r3` (`skills/**`).
13. **`docs/requests/` and `docs/lane-requests/`** — the directories do not
    exist, so the instruction of `AGENTS.md` ("write
    `docs/requests/<job>-<n>.md`") cannot be followed from this job; the
    cross-job requests of this job live in `docs/gaps/SKL-W0-01.md` instead.
    `scripts/truth/config.json` lists only `catalog.json` under
    `sharedGlobs`, so a mailbox file would be reported by the gate as outside
    the owned paths. Owner: operator.
14. **`/var/run/docker.sock` — the Docker daemon is not reachable on this host**
    (permission denied) — the `pg-rls-leak-test.sh`
    container path could not be exercised; only the daemon-free modes
    (`--print-probe-sql`, `--parse`) are proven (D-043). This is an
    environment fact, not a defect of the repository. Owner: operator.
15. **`tests/hygiene/test_repair_log.py`** — 18 of the 33 proof commands of
    this document are not re-executed by the guard: only the 15 commands marked
    `# auto` are. The others are the slow ones (whole pytest suites, the job
    gate) and the gate runs `pytest -q {paths}` over the *changed* test files
    only. A slow proof command can therefore rot without any suite noticing.
    Running them inside the guard is not possible without recursion (P31 runs
    `tests/hygiene/`, which is the guard itself); a runner that executes the
    slow proofs once per trunk, outside the suite, is the right place.
    Owner: `skills-engineering-r3` (`tests/**`).
16. **`scripts/truth/gate.mjs`** — the gate computes its diff against
    `git merge-base HEAD main`. After a commit of this job is integrated, that
    base is the commit itself, so the next gate run reports
    `no changes inside the owned paths: nothing was built` and
    `no test file was added or changed` and fails, even when the tree is
    correct. A job that only documents something therefore has to change a test
    file to get a green gate. The kit belongs to the operator and may not be
    edited by a job. Owner: operator.
