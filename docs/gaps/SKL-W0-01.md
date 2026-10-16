# Gaps — SKL-W0-01 (TASK-0004)

## G1 (blocking tooling): `scripts/truth/preflight.mjs` and the truth harness do not exist in this repo

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
- **Impact:** the blocked-check, gate, and commit-and-land commands in the job card cannot be executed
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
