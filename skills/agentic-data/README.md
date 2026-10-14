# Agentic Data Skills

Ten researched Agent Skills (agentskills.io standard) for coding and operations
agents working on the Ottili platform. Each skill is a folder `name/` with
`SKILL.md` (YAML front matter + body under 500 lines), optional `scripts/`,
`references/` and `tests/`. Long material lives in `references/` one level deep;
SKILL.md links it by name (progressive disclosure).

## The ten skills

| Skill | One-line value |
| --- | --- |
| `mcp-2026-07-28` | Build and audit MCP servers/clients against the 2026-07-28 spec: tools, resources, prompts, tasks, elicitation, structured output, OAuth 2.1, SDK version negotiation. |
| `skill-authoring-evals` | Author, validate and evaluate Agent Skills: description design that triggers reliably, front-matter validation, with_skill/without_skill baselines, precision/recall targets (>=0.9). |
| `computer-use-drivers` | Drive desktop/remote apps through accessibility trees and background input: coordinate scaling, confirm() gates, macOS AX / Windows UIA / X11-Wayland quirks. |
| `browser-agent-playwright` | Drive a browser with Playwright: DOM/ARIA grounding, robust locators, web-first waits, prompt-injection defense, safe hand-off to code. |
| `polite-crawling-warc` | Crawl a site and archive it to WARC 1.1: robots.txt first, token-bucket rate limiting, sitemaps, resume state, hostile-input sanitization. |
| `dedup-decontam` | Deduplicate and decontaminate text corpora for LLM training: MinHash/LSH near-dedup, n-gram and embedding decontamination, planted-item tests. |
| `verifiable-environments` | Design verifiers that resist reward hacking: spec-derived checks, oracle-free tests, pass-rate calibration, sandboxing, bypass-audit. |
| `llm-judge-calibration` | Calibrate LLM-as-judge graders: inter-annotator agreement, rubric tightness, cost/latency ledger, contradiction resolution, planted-item tests. |
| `trajectory-ledger` | Schema, grounding rules, outcome status and cost ledgers for agent trajectories so runs are reproducible and auditable. |
| `deep-research-method` | Evidence-backed research: score sources 0-10, cite every claim (URL + retrieval date + pinned version), resolve contradictions by weight, state confidence. |

## Install hints

- **Single skill:** copy the folder into your client's skill directory
  (`~/.codex/skills/`, `~/.claude/skills/`, etc.). The client discovers skills by
  folder name; the `name:` field in `SKILL.md` must match the folder name.
- **All ten:** `bash scripts/install.sh <target-dir>` (writes each skill folder,
  skips existing ones, prints a manifest).
- **Validate before shipping:** `python3 <skill>/scripts/validate_skill.py [--json report.json]`
  (exit 0 = pass). Run it on every skill after editing.
- **Run the acceptance contract:** `python3 scripts/acceptance_check.py` from the
  repository root (exit 0 only if all ten meet the contract).
- **Run the test suite:** `python3 -m pytest skills/agentic-data/ -q` from the
  repository root.

## Related skills

- `skills/core/**` and `skills/curated/**` — the platform's curated skill set;
  this job's skills are complementary, not replacements.
- `skills/engineering/**` — the ten engineering playbook skills (a sibling job).

## Sources

Every skill's `references/SOURCES.md` lists the primary sources (official
documentation, standards, source repositories, postmortems) with URL and retrieval
date. Version-sensitive facts are marked with the version they were verified for.
