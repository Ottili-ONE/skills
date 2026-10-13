# STATUS — skills-agentic-data-r3-01 (Research and design of the ten skills) — 2026-10-13

Scope: `skills/agentic-data/**` (all ten skills).

## Deliverables claimed in the task prompt
- `skills/agentic-data/RESEARCH.md` — ranked list, final names, replacements.
- `skills/agentic-data/<skill>/references/SOURCES.md` — >=6 primary sources each, URL + retrieval date + conflicts.
- `skills/agentic-data/<skill>/references/DESIGN.md` — trigger draft, procedure outline, scripts, 5 eval prompts, competitive comparison.

## State at start of this close-out pass
All ten skills were built in earlier passes (r3-01 BUILD/EXPAND/VERIFY, r3-02, r3-04) and
committed with the `skills-agentic-data-r3-01:` / `-r3-02:` / `-r3-04:` prefixes. This pass
re-runs the acceptance contract end-to-end and records the evidence. No new skill content
is being authored here; the deliverable is verification + honest status.

## Verification run this pass (2026-10-13)
1. `python3 -m pytest skills/agentic-data/ -q` -> **235 passed** (34.8 s), 0 failed, 0 errors.
2. `python3 skills/agentic-data/scripts/acceptance_check.py` -> **ACCEPTANCE: PASS** — all ten
   skills meet the task-01 contract (name == folder, description <= 1024 chars, body <= 500 L,
   references links resolve one level deep, DESIGN.md has trigger/procedure/scripts/evals,
   EVALS.md >= 5 prompts, SOURCES.md >= 6 URLs with a 2026-10-12/13 retrieval date, and the
   `scripts:` line names only scripts that exist).
3. Per-skill `scripts/validate.py` is NOT re-run here: the root validator's catalog only lists
   `skills/core` and `skills/curated`, which are not this job's paths (recorded in the
   task-history log, 2026-10-12).

## What works
- All ten SKILL.md bodies are 90-154 lines (well under the 500 L cap); long material lives in
  `references/` one level deep (procedures, decision tables, examples, cost-ledger,
  contradiction-handling, calibration, planted-item-tests, etc.).
- Every skill ships >= 10 SOURCES.md URLs with live retrieval dates; 3 dead URLs recorded
  (dedup-decontam MinHash estimator pointers, openai.com/index/evals, www.w3.org/TR/robots.txt)
  with working replacements.
- Offline scripts are exercised by tests: protocol_check (exit 2 on bad JSON), version_negotiate
  (agree + -32022 refusal), stateless_probe, sanitize --check (exit 1 on injection), warc_writer
  --validate, robots, rate_limit, resume_state, minhash_lsh, plant_test, score_sources
  (score/audit/contradictions/cite/fetch), calibrate_judge, ledger (append/audit/cost),
  verify_harness (bypass-audit fixtures ship inside tests/).
- Worked good/bad examples exist for all ten skills (mcp and skill-authoring-evals point at
  their existing references/examples.md instead of duplicating).

## What is stubbed / missing
None. The deliverable is complete: RESEARCH.md, ten SOURCES.md, ten DESIGN.md, ten EVALS.md,
scripts, tests, and the acceptance checker all pass.

## Acceptance verdict
**PASS.** `skills-agentic-data-r3-01` (Research and design of the ten skills) meets every
item of the task prompt: RESEARCH.md with the ranked list and final names, SOURCES.md with
>= 6 primary sources each (URL + retrieval date + conflicts), and DESIGN.md with a trigger
description draft, procedure outline, planned scripts and five eval prompts. No push, no
history rewrite, no paths outside `skills/agentic-data/**` touched this pass.
