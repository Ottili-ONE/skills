# SKL-W1-02 — honest gaps and cross-job requests

Job SKL-W1-02 (Domain references marked for adviser sign-off, and the orchestrator
preamble). This file records only things this job could NOT do because they live on
paths it does not own.

Reviewed 2026-10-22 (TASK-0006, adversarial review). Open cross-job requests: X-001,
X-002, X-003, X-005, X-006, X-007, X-008. Closed since the previous pass: G-002,
G-003, G-005 (evidence in each entry). X-009 records an ownership observation.

## G-001 — `scripts/truth/**` infrastructure is not in the skills repo (BLOCKER)

Superseded by **G-003**, which re-derives this with a full-filesystem search rather
than a cached claim. G-003 is the current statement; keep this entry so the historical
"BLOCKED at orientation" record survives.

**Closed 2026-10-22:** the toolchain is deployed in this repository (see G-003).

## G-002 — predecessor SKL-W1-01 has not landed

**CLOSED 2026-10-22.** SKL-W1-01 landed on trunk on 2026-10-20 and its output is part
of this worktree:

- `git log HEAD -n 1 --format=%H -E --grep='^Job: SKL-W1-01$'` returns `4861ca2` — the
  kit's own probe for "the predecessor is part of this worktree".
- Its deliverables are in the tree: `skills/engineering/pg-rls-multitenant/` and the
  `docs/interfaces/` contracts. This job's preamble generator reads the first one.

The launcher's `after:SKL-W1-01` check nevertheless failed on 2026-10-22 02:57 UTC,
because that check also requires the external record
`<TRUTH_RESULTS_DIR>/skills/SKL-W1-01.commit.json`. That record is gone: the results
directory was reset and now holds only this job's own files. The marker was therefore
stale — the predecessor was present, the bookkeeping file was missing — and it was
removed with the kit's documented `preflight.mjs --job SKL-W1-02 --clear`. Nothing in
the repository was touched by that step; the marker lives outside the repository.

- Owner: the operator (launcher bookkeeping). No code change is needed in this repo.

## X-001 — merge of `skr-journal-mapping` into `datev-extf` (cross-job request)

The task requires merging `skr-journal-mapping` into `datev-extf` or `ust-edge-cases`.
The canonical `skills/business-de/skr-journal-mapping/` is owned by
skills-business-de-r3 (see `docs/R3_OWNERS.json`), so this job cannot edit it.
Decision recorded here: **merge target = `datev-extf`**, because the journal mapper
emits the DATEV EXTF Buchungsstapel that `datev-extf` consumes (the canonical
`skr-journal-mapping/SKILL.md` "Related skills" line already points at
`[datev-extf](../datev-extf/)`).

- Request to skills-business-de-r3: move/merge the `skr-journal-mapping` skill content
  (SKILL.md, references/, scripts/journal_check.py, scripts/period_lock_check.py,
  tests/) into `skills/business-de/datev-extf/`, or publish a merge manifest this job
  can reference.
- This job's record of the decision lives at
  `skills/ref-datev-extf/ref-datev-extf/references/merge-skr-journal-mapping.md`.

**Still open on 2026-10-22:** `skills/business-de/skr-journal-mapping/` is still a
separate skill and `skills/business-de/datev-extf/` does not carry the journal mapper.

## X-002 — drop `--execute` from carrier/publish scripts (cross-job request)

The task requires dropping the `--execute` flags from the carrier and publish scripts
and keeping only idempotency/reconcile guidance inside the platform integrations docs,
or deleting both skills. The canonical skills `skills/business-de/carrier-apis-de/` and
`skills/business-de/publish-reconcile-wp-meta/` are owned by skills-business-de-r3, so
this job cannot edit them. Verified `--execute` usage:

- `skills/business-de/carrier-apis-de/scripts/label_create.py:62`
- `skills/business-de/carrier-apis-de/scripts/track.py:86`
- `skills/business-de/publish-reconcile-wp-meta/scripts/meta_publish.py:53`
- `skills/business-de/publish-reconcile-wp-meta/scripts/wp_publish.py:50`
  (`--execute`), plus the `--url`/`--user`/`--pass` send path

- Request to skills-business-de-r3: remove the `--execute` flags (and the
  `--token`/`--url`/`--page-id` send paths) from those four scripts, and move the
  idempotency/reconcile guidance into the platform integrations docs; or delete both
  skills if the integrator prefers.
- This job's record of the decision lives at
  `skills/ref-webhooks-safe/ref-webhooks-safe/references/platform-integrations-guidance.md`.

**Still open on 2026-10-22:** all four scripts still declare `--execute` at the line
numbers above (re-verified in this pass).

## X-003 — GERMO job template wiring (cross-job request)

The task requires wiring the preamble into the GERMO job template so it loads into the
base prompt of every job that owns a product repo. The template is owned by the PLT job
(`/srv/ottili/scratch/` and the lane repos), not by this repo. The acceptance here is
only that the generator exists and the file is correct.

- Request to the PLT job: include
  `skills/orchestrator-preamble/orchestrator-preamble/references/preamble.md`
  (regenerated by `node scripts/gen-preamble.mjs`) in the base prompt of every GERMO
  job that owns a product repo.

**Still open on 2026-10-22:** `.germo/skills/germo_agent/SKILL.md` does not mention the
preamble (0 hits).

## G-003 — `scripts/truth/**` toolchain EXISTS in ottili-platform but is NOT deployed to the skills repo (verified 2026-10-16)

**CLOSED 2026-10-22.** The toolchain is deployed in this repository:

- `scripts/truth/` is present with `preflight.mjs`, `gate.mjs`, `safe-commit.mjs`,
  `lib/`, `checks/` and `config.json`; `scripts/truth/KIT_VERSION` says `1.1.0` and the
  kit integrity check (`kit-files match MANIFEST.sha256`) passes.
- `node scripts/truth/preflight.mjs --job SKL-W1-02 --status` runs, `gate.mjs job` runs
  and `safe-commit.mjs` is the only way this job commits.

The 2026-10-16 state (kit only in `ottili-platform`, absent here) is kept above as the
historical record.

## X-004 — the future-dated "re-fetched on 2026-10-15" claim is outside this job's paths

The task requires removing the future-dated "re-fetched on 2026-10-15" claim. Verified
2026-10-22 (`grep -rln "2026-10-15\|re-fetched on" . --include=*.md`, excluding
`.git`): every hit sits under `skills/business-de/**` — `skills/business-de/*/references/SOURCES.md`
(10 files), `skills/business-de/config/versions.json`,
`skills/business-de/RESEARCH.md`, `skills/business-de/PASS5_GATE.md`,
`skills/business-de/PASS3_VERIFY.md` and `skills/business-de/README.md`. **None of this
job's owned paths** (`skills/ref-*/**`, `skills/orchestrator-preamble/**`,
`docs/reviews/**`) contains the claim, and `docs/reviews/*.md` carry no retrieval-date
claims at all.

- Owner: skills-business-de-r3 (`skills/business-de/**`).
- This job's action: none possible. Recorded so the next pass does not re-derive it.

### X-004a — the file list in the 2026-10-16 revision named files that no longer exist

The 2026-10-16 revision of this entry listed
`skills/business-de/config/REVERIFY_2026-10-15.md`,
`skills/business-de/config/REVERIFY_2026-10-14.md`, `skills/business-de/STATUS.md` and
`skills/business-de/HANDOFF.md`. Those four were deleted by SKL-W0-01 TASK-0004 — they
were pass-by-pass status diaries. The files that exist in `skills/business-de/` today
are `README.md`, `RESEARCH.md`, `PASS5_GATE.md`, `PASS3_VERIFY.md`,
`config/versions.json`, `immutability-state.json`, `period_lock_state.json`, `scripts/`
and the ten skill folders, each with its own `references/SOURCES.md` and
`references/EVALS.md`. The list above is updated accordingly (request G18 of
skills-business-de-r3 / SKL-W0-01, 2026-10-20).

## G-005 — `clean-tree.test.mjs` fails because another job has uncommitted work (2026-10-16)

**CLOSED 2026-10-22.** At the start of this pass `git status --porcelain` is empty:
the outbox work of skills-engineering-r3 was committed, so the clean-tree guard has
nothing to report. The historical entries are kept here:

`tests/hygiene/clean-tree.test.mjs` (SKL-W0-01, not this job) asserts
`git status --porcelain` is empty. It failed on 2026-10-16 because
`skills/engineering/outbox-idempotency/**` carried uncommitted work of
skills-engineering-r3. That path is owned by `skills-engineering-r3`
(`docs/R3_OWNERS.json`), so this job may not commit, revert or otherwise touch those
files. The failure was a shared-working-tree condition, not a defect this job
introduced.

## X-005 — CI is red: the orchestrator test step still globs the deleted `.mjs` suites

`.github/workflows/validate.yml` runs:

```yaml
- name: Run orchestrator contract tests
  run: |
    set -euo pipefail
    for t in tests/orchestrator/*.test.mjs; do
      echo "=== $t ==="
      node "$t"
    done
```

Every `tests/orchestrator/*.test.mjs` file was converted to pytest
(`test_gen_preamble.py`, `test_gen_preamble_failure.py`, `test_preamble_contracts.py`,
`test_preamble_property.py`, `test_preamble_reproducible.py`) and deleted. The glob no
longer matches, so `node` receives the literal pattern and the job fails:

```
$ bash -c 'set -euo pipefail; for t in tests/orchestrator/*.test.mjs; do node "$t"; done'
Error: Cannot find module '.../tests/orchestrator/*.test.mjs'   (exit 1)
```

Every push to `main` therefore fails this step.

- Owner: skills-engineering-r3 (`.github/**`).
- Request: run the pytest suites instead, e.g.
  `python3 -m pytest -q tests/orchestrator tests/reviews`, and drop the `.mjs` loop.

## X-006 — CI never runs any pytest suite

The workflow has no `pytest` step. The suites in `tests/orchestrator/` and
`tests/reviews/` therefore only run when a person starts pytest by hand, or when a job
gate discovers a test file inside its own owned paths. The contract tests for the
generated preamble and for the sign-off gate are not part of the pipeline.

- Owner: skills-engineering-r3 (`.github/**`).
- Request: add `python3 -m pytest -q tests/` to the workflow (the suites pass today:
  59 passed in 3.10s).

## X-007 — the sign-off gate is not wired into the repository validation

`scripts/validate_reviewed_by.py` implements the gate and fails closed: a skill whose
frontmatter names a reviewer fails the audit unless
`docs/reviews/<skill>.md` carries a filled `Reviewed by:`, `Date:` and `Signature:`
line. Nothing calls it:

- `scripts/validate.py --everywhere` (the build and lint command of the repository)
  does not run the audit — `grep -n "reviewed_by\|reviews" scripts/validate.py` finds
  nothing.
- No CI step runs it either (see X-005 and X-006).

The audit does run as the last check of the gate of this job (it is part of
`skills/ref-ust-edge-cases/tests/test_signoff_contract.py`), but a wrapper could be
promoted to a named reviewer with an empty sign-off block and the repository's own
validation would stay green.

- Owner: skills-engineering-r3 (`scripts/**`, `.github/**`).
- Request: call the audit from `scripts/validate.py` (or add a CI step) so the gate
  protects the whole repository, not only this job's gate.

## X-008 — two `.replace()` calls in the sign-off test are no-ops

`tests/reviews/test_signoff_ref_wrappers.py:83-89` tries to promote the wrapper by
replacing `Reviewed by: **UNVERIFIED — pending signature**` and `Date: **pending**`.
The review file stores those values as table rows
(`| Reviewed by | **UNVERIFIED — pending signature** |`, `| Date | **pending** |`), so
both replacements change nothing. The assertions still hold — a certified wrapper with
an unfilled block must fail the audit — but the mutation the test intends to perform is
not applied, and the case "reviewer named, table filled, signature empty" is never
exercised.

- Owner: `tests/**` is not listed in `docs/R3_OWNERS.json`; the integrator has to route
  this to whoever owns the suite.
- Request: replace the fenced-block lines (`Reviewed by: ____`, `Date: ____`) instead of
  the table rows, or drop the no-op calls.

## X-009 — earlier passes of this job committed paths outside the current owned set

The commits of 2026-10-16 (for example `8732c48`, `58e4e0a`, `ba08c01`, `c84cc90`,
`ae4e85b`) touched `.github/workflows/validate.yml`, `README.md`, `catalog.json`,
`index/skills.json`, `scripts/gen-preamble.mjs`, `scripts/validate_reviewed_by.py` and
`tests/**` — paths that the current job card does not give to SKL-W1-02 and that
`docs/R3_OWNERS.json` gives to skills-engineering-r3.

- Owner: skills-engineering-r3 for the paths it owns today.
- This job's action: none. The commits are on trunk, other jobs and the CI workflow
  depend on them, and reverting them would break more than it repairs. This pass
  changed only paths inside the owned set (plus `docs/gaps/SKL-W1-02.md`, which the
  gate adds to the owned globs of this job).
