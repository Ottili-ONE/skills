# Agentic Data Skills (R3)

Ten researched Agent Skills for coding and operations agents working on the Ottili
platform. Each skill is a folder with `SKILL.md` (front-matter + body), optional
`scripts/`, `references/`, `assets/`, and `tests/`.

## Skills

| Skill | One-line value | Trigger |
|---|---|---|
| `mcp-2026-07-28` | Stateless MCP server/client on the 2026-07-28 revision with OAuth 2.1/PKCE and version negotiation | scaffold an MCP server, handshake fails, tasks/get |
| `browser-agent-playwright` | Grounded browser automation with web-first waits and prompt-injection defense | scrape, test, or automate a site with a real browser |
| `computer-use-drivers` | Drive desktop apps via accessibility trees with confirm() gates on destructive actions | click/type/scroll an app that has no API |
| `polite-crawling-warc` | Polite site crawling archived to WARC 1.1 with robots.txt (RFC 9309) enforcement | crawl a site and archive it to WARC |
| `dedup-decontam` | MinHash/LSH dedup + n-gram decontamination for training corpora | prepare a corpus for LLM training/eval |
| `deep-research-method` | Evidence-backed research: source scoring 0-10, citation, contradiction resolution | answer a question from the web, audit a source |
| `llm-judge-calibration` | Calibrate LLM judges: rubrics, calibration sets, agreement, drift detection | build/audit an LLM-as-judge scoring pipeline |
| `trajectory-ledger` | Durable, append-only ledger of agent trajectories with replay and audit | record/audit/replay an agent run |
| `verifiable-environments` | Reproducible sandboxes: pinned images, hashes, attestation, drift detection | run code in a reproducible environment |
| `skill-authoring-evals` | Author Agent Skills with evals: spec rules, validators, near-miss prompts | write or audit a skill |

## Install hints

- Single skill: `python3 ../../scripts/install-skill.py skills/agentic-data/<name>`
- All ten: `python3 ../../scripts/install-skill.py skills/agentic-data/*`
- Validate one: `python3 ../../scripts/validate_skill.py skills/agentic-data/<name>`
- Validate all: `python3 ../../scripts/validate_skill.py --all`
- Related-graph check (acyclic): `python3 ../../scripts/check_related_graph.py --skills skills/agentic-data`

## Layout

Each skill folder: `SKILL.md`, `references/EVALS.md`, `references/SOURCES.md`,
optional `scripts/`, `assets/`, `tests/`. Long material lives in `references/`
linked one level deep from `SKILL.md` (progressive disclosure).
