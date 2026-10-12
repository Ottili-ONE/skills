# STATUS — skills-agentic-data-r3-04 (Build skills 7-10) — 2026-10-12

Scope: `skills/agentic-data/verifiable-environments`,
`skills/agentic-data/llm-judge-calibration`,
`skills/agentic-data/trajectory-ledger`,
`skills/agentic-data/deep-research-method`.

## What works (proven by a command + result)

All four skills validate against the Agent Skills standard and the repository
validator, and every script runs offline and deterministically:

- `python scripts/validate.py` -> `ok: 2 skills validated` (exit 0).
- Front matter for all four: `name` == folder name; `description` 261-322 chars
  (limit 1024); SKILL.md 104-140 lines (limit 500); every `references/` link
  resolves one level deep, no escapes.
- Tests passing: verifiable-environments 12, llm-judge-calibration 8,
  trajectory-ledger 9, deep-research-method 19 (48 total, all offline).
- **verifiable-environments**: `scripts/gen_fixtures.py --out <dir>` writes
  SPEC.md, contract.json, contract_broken.json, checks.json,
  checks_neutered.json and good/broken/lazy agent dirs. `scripts/verify_harness.py
  ... --neutered-checks checks_neutered.json` exits 0 with
  `PASS: harness discriminates good, broken and lazy agents` and
  `INFO: neutering a check dropped power; verifier verified`. The neutered run
  drops power vs lazy to 0.00 (the lazy agent writes output.json but no
  summary, so the neutered summary check passes for it), proving the harness
  detects a dead check.
- **llm-judge-calibration**: `scripts/calibrate_judge.py calibrate --rows
  high.jsonl` -> `PASS: judge calibration within thresholds` (alpha 0.757).
  `scripts/calibrate_judge.py rubric rubric.yaml` lints definitions, examples,
  anti-examples, strictly-increasing scores and a scale starting at 1.
  `scripts/gen_rubric.py --spec spec.json --out rubric.yaml` emits a rubric that
  passes the lint from a compact JSON spec.
- **trajectory-ledger**: `scripts/ledger.py audit traj.jsonl` -> `PASS: audit
  clean (3 events)`; `normalize` re-serialises to canonical JSON and recomputes
  `state_hash`; `record-non-det <ledger> <step> "<reason>"` appends an `observe`
  event with `non_determinism: true` and a recomputed hash, and the appended
  event audits clean.
- **deep-research-method**: `scripts/score_sources.py score good.jsonl` ->
  `PASS: 3/3 sources kept at >= 6`; `staleness --question-date 2026-10-12`
  flags sources older than the window; `cite`/`fetch` emit the citation block
  and the re-fetch URL list.

## What is stubbed / missing
- None for the four skills. Every script, test, EVALS entry and reference page
  shipped in this pass runs. The `ap.error`/`raise SystemExit` paths in the
  scripts are covered by tests (missing files exit 2, malformed input exits 1).
- No new online research was required this pass: every fact was already fetched
  2026-10-12 and recorded in the per-skill `references/SOURCES.md` (10 entries
  each, >= 6 required). The primary arXiv IDs were re-verified live this pass
  (all HTTP 200 with titles matching the recorded entries) and the re-verification
  is recorded in each SOURCES.md.

## Defect found and fixed this pass
- **verifiable-environments had no verify-the-verifier step.** The DESIGN.md and
  SKILL.md described flipping a check to always-pass but shipped no command or
  fixture for it. Added `scripts/gen_fixtures.py`, a `--neutered-checks` flag on
  `verify_harness.py`, `references/neutering.md`, E11, and a bypass-register
  entry for the neutered check. The fixture's neutered set keeps the same check
  count as the live set so power is compared on equal totals.
- **llm-judge-calibration had no rubric lint.** A rubric without per-level
  examples cannot be calibrated, but nothing rejected one. Added the `rubric`
  subcommand on `calibrate_judge.py`, `scripts/rubric_lint.py`,
  `scripts/gen_rubric.py`, `references/rubric-lint.md` and E11.
- **trajectory-ledger had no normalise or divergence-record command.** Hand-written
  trajectories fail audit because their stored `state_hash` does not recompute,
  and the replay procedure said "record the divergence" with no tool to do it.
  Added `normalize` and `record-non-det`, `references/normalisation.md`, E8 and E9.
- **deep-research-method had no staleness check.** The skill required re-fetching
  stale sources but left it to memory. Added the `staleness` subcommand,
  `references/staleness.md` and E11.
