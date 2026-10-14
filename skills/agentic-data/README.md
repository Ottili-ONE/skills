# agentic-data — Data-plane agent skills

Ten skills for agents that work in the data plane: browsers, desktops, crawls,
research pipelines, judges, MCP servers, environments, trajectories, evals and
dedup/decontamination. Each skill is a folder with `SKILL.md`, `references/`,
`scripts/` and `tests/`. Install by copying the folder into the agent's skills
directory (see the root `README.md` for per-agent conventions).

## Skills

| Skill | One-line value | Install hint |
|-------|----------------|--------------|
| `browser-agent-playwright` | Drive a browser safely: grounded locators, web-first waits, injection defense, clean hand-off. | Needs `npx playwright install`; 1.49+. |
| `computer-use-drivers` | Operate a desktop/remote app with no API via accessibility trees and background input. | macOS AX / Windows UIA / Linux AT-SPI. |
| `dedup-decontam` | Detect near-duplicates and test-set leakage in corpora before any scoring. | Deterministic, offline. |
| `deep-research-method` | Multi-source research with scored sources, citations, confidence and contradiction handling. | Offline; `scripts/score_sources.py`. |
| `llm-judge-calibration` | Calibrate an LLM judge so its scores separate good from broken agents. | Needs a gold set + rubric. |
| `mcp-2026-07-28` | Build/consume MCP servers and clients with a statelessness proof. | Reference impl in `scripts/`. |
| `polite-crawling-warc` | Crawl politely into a WARC with rate limits, retries and dedup. | Needs `curl`/`warc` tooling. |
| `skill-authoring-evals` | Write evals that prove a skill changed the outcome (with_skill vs without_skill). | Offline; `scripts/`. |
| `trajectory-ledger` | Record multi-step agent runs as replayable, auditable trajectories. | JSON ledger only. |
| `verifiable-environments` | Build environments whose checks separate good from broken agents. | Needs a spec + bypass register. |

## Validation

```sh
python3 scripts/validate_skills.py skills/agentic-data/*
```

## Status files

Each skill folder may carry a `STATUS.md` (per-skill status, last verified date).
