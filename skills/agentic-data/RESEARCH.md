# RESEARCH.md — skills-agentic-data-r3 (R3 JOB 'skills-agentic-data-r3')

Ranked list of the ten agentic-data skills, final names, replacements made, and the
evidence base for each. Last updated: 2026-10-07.

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
