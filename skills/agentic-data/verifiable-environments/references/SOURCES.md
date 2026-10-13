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
