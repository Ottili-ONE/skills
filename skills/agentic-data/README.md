# skills/agentic-data — ten Agent Skills for agentic data work

Each folder is a self-contained Agent Skill (agentskills.io standard): `SKILL.md`
with YAML frontmatter, plus `references/` (SOURCES, EVALS, procedures) and
`scripts/` (small, deterministic, runnable offline).

Install with the repo script:

```bash
./install.sh skills/agentic-data/browser-agent-playwright
# or install all ten:
./install.sh skills/agentic-data/*
```

Validate before shipping:

```bash
python3 scripts/validate_skill.py skills/agentic-data/<name>
python3 scripts/validate.py --json          # catalog consistency
```

## The ten skills

- **browser-agent-playwright** — Drive a browser with Playwright: DOM/ARIA
  grounding, robust locators, network waits, prompt-injection defense, safe
  hand-off. Use when an agent must scrape, test or automate a site.
- **computer-use-drivers** — Drive desktop/remote apps through accessibility
  trees and background input with coordinate scaling, confirm() gates and
  platform quirks. Use when the target app has no API.
- **dedup-decontam** — Deduplicate datasets and decontaminate them against
  eval/train corpora with MinHash/LSH and n-gram overlap. Use before training
  or before publishing a dataset.
- **deep-research-method** — Score, fetch, cite and reconcile web sources into
  an auditable evidence chain with a confidence ladder. Use for factual
  questions that depend on documents you must find and weigh.
- **llm-judge-calibration** — Build, lint and calibrate LLM-as-judge rubrics so
  that model scores are stable, auditable and cheap. Use when grading model
  output at scale.
- **mcp-2026-07-28** — Implement or audit an MCP server/client against the
  2026-07-28 model spec: tool discovery, resources, prompts, OAuth flow,
  error codes, version negotiation. Use when building or probing an MCP
  server.
- **polite-crawling-warc** — Crawl politely (robots.txt, rate limits, resume
  state) and write WARC files that validate against the WARC spec. Use for
  large, resumable web archives.
- **skill-authoring-evals** — Author Agent Skills and write evals for them:
  front-matter rules, trigger precision, eval schemas and metrics. Use when
  creating or reviewing a skill.
- **trajectory-ledger** — Record, replay and audit multi-step agent runs as a
  typed, hashed, costed JSONL ledger. Use when a result must be reproducible
  or auditable.
- **verifiable-environments** — Design verifiers that resist reward hacking:
  spec-derived checks, oracle-free tests, pass-rate calibration, sandboxing,
  failure-mode auditing. Use when building or auditing an eval harness.

## Cross-links

Related skills are named in each `SKILL.md`'s *Related* section. The graph is
acyclic; `skill-authoring-evals` is the meta-skill (it authors and evaluates
skills) and depends on nothing else in this set.

## Where to go next

- `HANDOFF.md` — what to re-verify and when, plus ideas for the next ten skills.
- Each skill's `references/EVALS.md` — realistic prompts, expected behaviour,
  failure signs and near-miss triggers.
- Each skill's `references/SOURCES.md` — primary sources with URLs and retrieval
  dates.
