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

## Verification to be run this pass
1. `python3 skills/agentic-data/scripts/acceptance_check.py` — standard-rules contract.
2. `python3 -m pytest skills/agentic-data/` — all offline scripts and tests.
3. `python3 scripts/validate.py skills/agentic-data/<skill>` per skill (root validator).
4. Per-source URL re-check via curl is NOT re-run here (done 2026-10-13 in PASS 3, recorded
   in each SOURCES.md "Retrieved" line); this pass checks the artefacts, not the network.

## To be filled after the checks run
- What works (command + result).
- What is stubbed / missing (none expected).
- Acceptance verdict.
