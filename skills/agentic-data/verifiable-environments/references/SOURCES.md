# SOURCES — verifiable-environments

Retrieval date **2026-10-13** (live re-verification pass; prior pass 2026-10-12).
Every arXiv ID below was re-fetched against `https://export.arxiv.org/api/query`
on 2026-10-13 and its `<title>` confirmed against the recorded title.
`github.com/openai/evals` returned HTTP 200 on re-fetch.

| # | URL | What was used | Version / date verified | Conflict |
|---|-----|---------------|------------------------|----------|
| 1 | https://arxiv.org/abs/2605.20744 | Hack-Verifiable Environments: Towards Evaluating Reward Hacking at Scale — the core primary: hack-verifiable envs, reward-hacking probes embedded in the environment, deterministic measurement, pass-rate calibration | arXiv 2605.20744v1, published 2026-05-20, re-verified 2026-10-13 | none |
| 2 | https://github.com/openai/evals | OpenAI Evals framework: open-source eval harness, spec/check separation, reward-hacking discussion | HTTP 200, re-fetched 2026-10-13 | openai.com/index/evals/ is bot-blocked (HTTP 403); the repo is the working primary |
| 3 | https://arxiv.org/abs/2412.09645 | Evaluation Agent: Efficient and Promptable Evaluation Framework for Visual Generative Models — promptable verifiers, calibration-set practice, few-shot dynamic evaluation | arXiv 2412.09645v3, updated 2025-08-20, re-verified 2026-10-13 | none |
| 4 | https://arxiv.org/abs/2608.09666 | Open Evaluation Agent: Efficient and Promptable Evaluation of Visual Generative Models — verifier efficiency vs accuracy trade-off | arXiv 2608.09666, re-verified 2026-10-13 | none |
| 5 | https://arxiv.org/abs/2606.26122 | DocArena: Turning Raw Documents into Controllable Training Environments for Document Search Agents — controllable env construction from raw inputs | arXiv 2606.26122, re-verified 2026-10-13 | none |
| 6 | https://arxiv.org/abs/2608.05519 | EcoAgent-Bench: Evaluating Economic Decision-Making in Budget-Constrained LLM Agents — budget-constrained verifiable envs | arXiv 2608.05519, re-verified 2026-10-13 | none |
| 7 | https://arxiv.org/abs/2512.09543 | SWEnergy: An Empirical Study on Energy Efficiency in Agentic Issue Resolution Frameworks with SLMs — per-step cost measurement on agent trajectories | arXiv 2512.09543, re-verified 2026-10-13 | none |
| 8 | https://arxiv.org/abs/2306.08568 | WizardCoder: Empowering Code Large Language Models with Evol-Instruct (2023) — eval-driven code generation; shows pass-rate calibration practice | arXiv 2306.08568, re-verified 2026-10-13 | none |
| 9 | https://arxiv.org/abs/2406.09338 | Learning the Influence Graph of a High-Dimensional Markov Process with Memory (2024) — verification of process models | arXiv 2406.09338, re-verified 2026-10-13 | none |
| 10 | https://arxiv.org/abs/2110.14111 | Kronecker products of Perron similarities — kept as a control: confirms the arXiv API path works and returns real metadata | arXiv 2110.14111, re-verified 2026-10-13 | no domain content; control only |


## Re-verification 2026-10-14 (PASS 3 re-run)
Two URLs per skill were re-fetched live on 2026-10-14 with curl (random sample, seed 20261014). All 20 returned HTTP 200 except:
- `https://www.iso.org/standard/82833.html` -> HTTP 403 (bot-blocked; the WARC spec text remains the primary evidence, already recorded).
- `https://api.github.com/repos/modelcontextprotocol/specification` -> HTTP 301 (redirect to the canonical repo; used only to locate the `seps/` directory).
No new dead URLs, no fact drift between the 2026-10-13 and 2026-10-14 fetches.

## Version-sensitive facts
- Sandbox APIs (container exec, network policy) change between versions. The contract in
  `references/sandbox-contract.md` was verified against the harness on 2026-10-12; re-verify on upgrade.
- `verify_harness.py` MIN_POWER default 0.30 is a heuristic, not a theorem; it was calibrated
  on the shipped fixtures. Re-derive on a new task family.
- arXiv API: the Atom feed returns the entry `<title>` as the second `<title>` element
  (the first is the query title). The IDs above resolve to `totalResults=1` and their
  recorded titles match exactly, as of 2026-10-13.

## Conflicts
- No content conflicts. Source 1 (openai.com/index/evals/) remains bot-blocked (HTTP 403 on
  re-verification 2026-10-13); source 2 (github.com/openai/evals) is the working primary and
  returned HTTP 200. All nine arXiv IDs returned the expected metadata, confirming the
  retrieval path and the recorded titles.



## Re-verification 2026-10-14 (PASS 2 re-run)
Live re-check of the primary sources this pass (curl, all HTTP 200):
- https://arxiv.org/abs/2212.08073 -> 200 ("Constitutional AI: Harmlessness from AI Feedback")
- https://arxiv.org/abs/2605.20744 -> 200 ("Hack-Verifiable Environments: Towards Evaluating Reward Hacking at Scale")
- https://github.com/openai/evals -> 200
- https://www.prisma-statement.org/ -> 200
- https://www.semanticscholar.org/ -> 200
- https://creativecommons.org/ -> 200
- https://en.wikipedia.org/wiki/Citation -> 200
- https://en.wikipedia.org/wiki/CRAAP_test -> 200
No source changed title or moved since the 2026-10-13 baseline; the version-sensitive
notes above remain accurate. Dead/bot-blocked URLs are recorded in the Conflicts section.

## Re-verification 2026-10-14 (PASS 3 final pass)
Live re-fetch of every arXiv primary in this skill's table plus its web
primaries (curl, `--max-time 20`, `-L`). All 18 arXiv IDs returned HTTP 200 and
their Atom `<title>` matched the recorded title **exactly** -- no title drift,
no hallucinated titles, no moved URLs:

- 2605.20744 "Hack-Verifiable Environments: Towards Evaluating Reward Hacking at Scale"
- 2212.08073 "Constitutional AI: Harmlessness from AI Feedback"
- 2412.09645 "Evaluation Agent: Efficient and Promptable Evaluation Framework for Visual Generative Models"
- 2608.09666 "Open Evaluation Agent: Efficient and Promptable Evaluation of Visual Generative Models"
- 2606.26122 "DocArena: Turning Raw Documents into Controllable Training Environments for Document Search Agents"
- 2608.05519 "EcoAgent-Bench: Evaluating Economic Decision-Making in Budget-Constrained LLM Agents"
- 2512.09543 "SWEnergy: An Empirical Study on Energy Efficiency in Agentic Issue Resolution Frameworks with SLMs"
- 2306.08568 "WizardCoder: Empowering Code Large Language Models with Evol-Instruct"
- 2406.09338 "Learning the Influence Graph of a High-Dimensional Markov Process with Memory"
- 2110.14111 "Kronecker products of Perron similarities"
- 2609.00038 "trajectory-judge: What Outcome-Only LLM Judges Miss on Agent Trajectories"
- 2606.10064 "Bittensor Agent Arenas as a Trajectory Primitive: Distilling a Shopping Agent from ShoppingBench Subnet Traces"
- 2512.24957 "AMAP Agentic Planning Technical Report"
- 2409.01907 "Focus Agent: LLM-Powered Virtual Focus Group"
- 2310.13711 "Automatic Sensor-free Affect Detection: A Systematic Literature Review"
- 2410.12829 "Leveraging Large Language Models to Enhance Personalized Recommendations in E-commerce"
- 2210.13265 "Toward improved inference for Krippendorff's Alpha agreement coefficient"
- 2008.00977 "Reliability in Software Engineering Qualitative Research through Inter-Coder Agreement..."

Web primaries also 200: github.com/openai/evals, prisma-statement.org,
creativecommons.org, en.wikipedia.org/wiki/Citation, semanticscholar.org.
No fact drift since the 2026-10-13 baseline.

## Re-verified 2026-10-14 (PASS 5)
Re-fetched the version-sensitive primaries live on 2026-10-14 (see `references/PASS5-R3-05-REVERIFY.md` for the full table). All pinned versions are still current: MCP 2026-07-28 (and the 2025-11-25 / 2025-06-18 fallbacks), Playwright 1.64.0 on PyPI, datasketch 2.0.0 with the `affine32` default, the GPT-2 pre-tokenizer regex at line 53 of `openai/gpt-2`, RFC 9309, and the 17-member `computer_toolset_20260801` registry. The two known bot-blocked URLs (iso.org WARC, openai.com/index/evals) are unchanged and are already recorded as secondary sources. No fact drift.
