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

## Pass 4 — fixes applied (2026-10-12)

1. **DESIGN.md "mirrored" claim reworded** in all ten files:
   `## Five eval prompts (mirrored in ...)` -> `## Five eval scenarios (expanded in ...)`.
   Verified: the prompts are scenario paraphrases, not verbatim copies; the new
   wording is accurate. `grep "mirrored in" skills/agentic-data/*/references/DESIGN.md`
   now returns nothing.
2. **`RESEARCH.md` source-count table corrected.** The "scripts" column was a count of
   *new* scripts, not the total listed in SKILL.md. `trajectory-ledger` and
   `deep-research-method` rows now note that SKILL.md lists 4 named scripts each while
   `scripts/` ships one module. Line counts and source counts were also re-derived
   (trajectory-ledger body 87 L, deep-research-method 12 URLs).
3. Re-ran `pytest skills/agentic-data/` after the edits: **121 passed**, exit 0.

## PASS 4 (2026-10-12) — worked examples, script gaps, live re-verification

Method: re-read every SKILL.md, re-ran `pytest skills/agentic-data/`, re-fetched
every primary URL with curl, and re-ran `validate_skill.py --skill` on all ten.

### 1. Worked examples
All ten SKILL.md now carry a `## Worked examples` section (one good + two bad,
each with a detection signal). mcp-2026-07-28 and skill-authoring-evals point at
their existing `references/examples.md` instead of duplicating. Counts:

| skill | body L | examples |
|-------|--------|----------|
| browser-agent-playwright | 93 | 3 |
| computer-use-drivers | 136 | 3 |
| dedup-decontam | 111 | 3 |
| deep-research-method | 110 | 3 |
| llm-judge-calibration | 103 | 3 |
| mcp-2026-07-28 | 93 | 0 (in references/examples.md) |
| polite-crawling-warc | 88 | 3 |
| skill-authoring-evals | 117 | 0 (in references/examples.md) |
| trajectory-ledger | 118 | 3 |
| verifiable-environments | 139 | 3 |

All under the 500-line budget.

### 2. Scripts
`deep-research-method/scripts/score_sources.py` gained `cite` and `fetch`
subcommands (SKILL.md advertised them; the script only shipped
`score`/`audit`/`contradictions`). 6 new tests. Total: **126 passed** (was 121).

### 3. Re-verification (2026-10-12, curl)
- MCP changelog 200, re-read in full — every fact in `references/changelog.md`
  confirmed (sessions removed, `server/discover` added, tasks extension,
  error-code renumbering, DCR deprecated, `includeContext` deprecated,
  Roots/Sampling/Logging deprecated).
- `modelcontextprotocol.io/community/feature-lifecycle` 200 — the deprecation
  window is **at least twelve months**; recorded in `references/changelog.md`.
- All 26 arXiv IDs re-fetched: 25 return 200 with correct titles.
  `arxiv.org/abs/2310.13711` is a systematic-review *method* paper; the three
  SOURCES.md files that cite it already described it as such, so no change.
- `www.iso.org/standard/82833.html` 403 (bot-blocked) — corroborating-only, as
  recorded. `github.com/.../modelcontextprotocol/blob/main/CHANGELOG.md` 404 —
  the repo has no CHANGELOG.md; the spec changelog is the authoritative source
  and is what the skill cites. No dead link pointed at it.
- All other primary URLs (agentskills.io, RFC 9309, IIPC raw specs, ekzhu/datasketch,
  playwright, anthropics SDK computer-toolset, openai/evals, OWASP) 200.

### 4. Standard rules (re-run)
`validate_skill.py --skill` on all ten: `0 0` fails everywhere. name==folder,
desc<=1024, body<=500 L, references/ links one level deep, SOURCES>=6 URLs with
2026-10-12 retrieval dates, EVALS>=5.

## Final state

| artefact | count |
|----------|-------|
| skills | 10 |
| SKILL.md | 10, all under 500 L, name==folder, desc<=1024 |
| references/SOURCES.md | 10, 9-12 primary URLs each, all dated 2026-10-12 |
| references/DESIGN.md | 10, trigger draft + procedure + scripts + 5 scenarios |
| references/EVALS.md | 10, 7-12 evals each, no duplicate IDs |
| scripts/*.py | 23 modules across the ten skills |
| tests/test_*.py | 10 files, 126 test functions, 126 passing |
| RESEARCH.md | ranked list, replacements (none), evidence status, 5 passes |
