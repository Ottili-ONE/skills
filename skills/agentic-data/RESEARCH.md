# RESEARCH.md — skills-agentic-data-r3 (R3 JOB 'skills-agentic-data-r3')

Ranked list of the ten agentic-data skills, final names, replacements made, and the
evidence base for each. Last updated: 2026-10-12.

## Ranking and final names

| # | Final name | Seed topic | Status | One-line value for Ottili agents |
|---|-----------|-----------|--------|----------------------------------|
| 1 | `mcp-2026-07-28` | MCP 2026-07-28 | kept, pinned | Build and consume stateless MCP servers/clients on the current revision |
| 2 | `skill-authoring-evals` | skill authoring + evals | kept, merged | Write, validate and evaluate Agent Skills against the standard |
| 3 | `computer-use-drivers` | computer use drivers | kept | Drive desktop apps via accessibility trees with safety layers |
| 4 | `browser-agent-playwright` | browser agent (Playwright) | kept | Grounded, robust browser automation with prompt-injection defense |
| 5 | `polite-crawling-warc` | polite crawling / WARC | kept | Respectful, resumable web crawling with WARC output |
| 6 | `dedup-decontam` | dedup + decontam | kept | MinHash/LSH dedup and n-gram/embedding decontamination |
| 7 | `verifiable-environments` | verifiable environments | kept | Design verifiers that resist reward hacking and calibrate pass rates |
| 8 | `llm-judge-calibration` | LLM judge calibration | kept | Rubrics, calibration sets, agreement and drift control for judges |
| 9 | `trajectory-ledger` | trajectory ledger | kept | Schemas, grounding rules, outcome status and cost ledgers |
| 10 | `deep-research-method` | deep research method | kept | Source-quality scoring, citation discipline, contradiction handling |

No seed topic was replaced: all ten map 1:1 to the job's list. The ordering is by
dependency (protocol -> authoring -> interaction -> data -> evaluation), which is also
the order in which Ottili agents will need them.

## Replacements and renames

None. Each skill keeps its seed name so that cross-references, the catalog and the
index generator stay stable.

## Evidence status (verified 2026-10-12)

Every skill now carries `references/SOURCES.md` with real primary sources fetched live
on 2026-10-12. The first research pass seeded several SOURCES.md files with unrelated
arXiv "control" papers and invented titles; those have been replaced with verified
titles confirmed against the live arXiv API on 2026-10-12. Dead URLs found this pass
and their replacements are recorded in each skill's `Conflicts` section:

- `www.cs.cmu.edu/~dgc/papers/MinHash/MinHash.pdf`, `www.cs.princeton.edu/~chazelle/pubs/...`,
  `github.com/carpuat/leakage_report`, `github.com/IAAR-AI/decontamination-benchmarks`
  (dedup-decontam) -> arXiv-verified MinHash estimator papers + live `ekzhu/datasketch`.
- `openai.com/index/evals/` (bot-blocked 403) -> `github.com/openai/evals` (verifiable-environments, llm-judge-calibration, deep-research-method).
- `internetarchive/heritrix` (404, repo moved) -> `internetarchive/heritrix3`.
- `www.library.ucdavis.edu/guide/evaluate-sources` (404) -> CRAAP test article.
- `owasp.org/www-project-top-10-for-llm/` (404) -> `genai.owasp.org/llm-top-10/`.
- `www.w3.org/TR/robots.txt/` (404) -> `datatracker.ietf.org/doc/html/rfc9309`.
- `arxiv.org/help/search/api` (404) -> the live arXiv API itself.

## Source counts per skill (acceptance bar: >= 6 primary sources)

| Skill | Primary sources | SKILL.md | EVALS prompts | Offline scripts |
|-------|----------------|----------|---------------|-----------------|
| mcp-2026-07-28 | 9 | 82 L | 6 | 3 (protocol_check, version_negotiate, stateless_probe) |
| skill-authoring-evals | 10 | 89 L | 7 | 1 (validate_skill) |
| computer-use-drivers | 9 | 85 L | 6 | 0 (contract is in the SDK) |
| browser-agent-playwright | 10 | 55 L | 8 | 2 (sanitize, validate_skill) |
| polite-crawling-warc | 10 | 57 L | 9 | 6 (rate_limit, resume_state, robots, validate_warc, warc_writer, validate_skill) |
| dedup-decontam | 10 | 83 L | 10 | 6 (normalize, validate_skill, ngram_decontam, embed_decontam, plant_test, minhash_lsh) |
| verifiable-environments | 10 | 103 L | 10 | 1 (verify_harness) |
| llm-judge-calibration | 9 | 78 L | 9 | 1 (calibrate_judge) |
| trajectory-ledger | 10 | 86 L | 7 | 1 (audit) |
| deep-research-method | 10 | 79 L | 9 | 1 (score_sources) |

All ten skills pass `scripts/validate_skill.py` (exit 0) and every SKILL.md is under the
500-line budget. The MCP scripts were exercised live: `version_negotiate.py` correctly
refuses a 2025-06-18 client against a 2026-07-28-only server (exit 1, `-32022` semantics)
and agrees when versions overlap.

## What makes each skill better than a generic agent

A generic agent knows the *idea* of each topic; these skills ship the *decision
procedure*: pass/fail checklists, version-pinned facts, copy-paste-safe commands,
worked good/bad examples, and a verification section. The difference is documented per
skill in `references/DESIGN.md`.

## Sources

Every skill carries `references/SOURCES.md` with at least six primary sources, each
recorded with URL, retrieval date, what was used from it, and any conflict between
sources. Version-sensitive facts are marked with the version they were verified for
and a re-verification note.
