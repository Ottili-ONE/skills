# AUDIT — skills-agentic-data-r3 (2026-10-12, independent re-check)

Method: fresh `find`/`grep` inventory (not reading prior claims), `pytest`, and a
front-matter checker written for this pass. Everything below is re-derived from the
files on disk.

## Pass 1 — structural (all ten skills)

| skill | name==folder | desc<=1024 | body<=500L | urls>=6 | retrieval date | evals>=5 | refs/ links |
|-------|--------------|------------|------------|---------|----------------|----------|-------------|
| browser-agent-playwright | yes | 363 | 58 | 10 | 2026-10-12 | 8 | 7 |
| computer-use-drivers | yes | 388 | 101 | 9 | 2026-10-12 | 8 | 5 |
| dedup-decontam | yes | 327 | 80 | 10 | 2026-10-12 | 10 | 5 |
| deep-research-method | yes | 283 | 75 | 12 | 2026-10-12 | 10 | 5 |
| llm-judge-calibration | yes | 261 | 74 | 9 | 2026-10-12 | 9 | 5 |
| mcp-2026-07-28 | yes | 455 | 83 | 9 | 2026-10-12 | 9 | 9 |
| polite-crawling-warc | yes | 335 | 54 | 12 | 2026-10-12 | 9 | 7 |
| skill-authoring-evals | yes | 407 | 112 | 10 | 2026-10-12 | 12 | 7 |
| trajectory-ledger | yes | 300 | 87 | 10 | 2026-10-12 | 7 | 6 |
| verifiable-environments | yes | 322 | 106 | 10 | 2026-10-12 | 10 | 9 |

All ten pass the Agent Skills standard's hard rules. `scripts/validate.py` -> `ok:
2 skills validated` (it validates the repo's own two skills, not this collection).

## Pass 2 — tests

`pytest skills/agentic-data/` -> **121 passed** (10 test files, 122 test functions
collected; one collection-time skip is counted in the file list). Exit 0.

## Pass 3 — findings that still need work

1. **DESIGN.md "mirrored" claim is not literal.** Every DESIGN.md says its five eval
   prompts are "mirrored in `references/EVALS.md`", but the prompts are *short
   paraphrases* of the EVALS.md prompts, not copies. Only `computer-use-drivers`,
   `skill-authoring-evals` and `trajectory-ledger` share verbatim prompt text.
   The claim is true in spirit (same scenario, same expected behaviour) but would
   fail a strict "verbatim mirror" check. **Action: reword the DESIGN.md headers to
   "five eval scenarios, expanded in `references/EVALS.md`".**
2. **`skill-authoring-evals/report_test.json` is stale in the index.** It records
   `skill: skill-authoring-evals, oks: 19` while the working tree holds
   `skill: mcp-2026-07-28, oks: 22` (the last validation run). The working-tree copy
   is correct; the committed copy is one validation run behind.
3. **`RESEARCH.md` table undercounts scripts.** It lists 1 script for
   `trajectory-ledger` and `deep-research-method`; both ship 4 (`append`, `replay`,
   `cost`, `audit` / `score_sources`, `audit`, `cite`, `fetch`). The "offline
   scripts" column is a count of *new* scripts, not total.
4. **`deep-research-method/references/SOURCES.md` lists 12 URLs** (one is a control
   entry), so the "10 primary sources" headline rounds up.

## Verdict

Acceptance bar (RESEARCH.md + SOURCES.md + DESIGN.md per skill, >=6 sources each,
>=5 evals each, standard rules green): **MET**. Findings 1-4 are documentation
accuracy issues, not missing artefacts.
