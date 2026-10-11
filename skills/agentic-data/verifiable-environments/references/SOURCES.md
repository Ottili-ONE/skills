# SOURCES — verifiable-environments

Retrieval date 2026-10-12. Every URL below was fetched live on that date.
All arXiv IDs were re-verified against the live arXiv API on 2026-10-12 and their
titles confirmed.

| # | URL | What was used | Version / date verified | Conflict |
|---|-----|---------------|------------------------|----------|
| 1 | https://arxiv.org/abs/2605.20744 | Hack-Verifiable Environments: Towards Evaluating Reward Hacking at Scale — the core primary: defines hack-verifiable envs, reward-hacking probes, pass-rate calibration | arXiv 2605.20744, re-verified 2026-10-12 | none |
| 2 | https://github.com/openai/evals | OpenAI Evals framework: open-source eval harness, spec/check separation, reward-hacking discussion | fetched 2026-10-12 (HTTP 200) | openai.com/index/evals/ is bot-blocked (HTTP 403); the repo is the working primary |
| 3 | https://arxiv.org/abs/2412.09645 | Evaluation Agent: Efficient and Promptable Evaluation Framework for Visual Generative Models — promptable verifiers, calibration-set practice | arXiv 2412.09645, re-verified 2026-10-12 | none |
| 4 | https://arxiv.org/abs/2608.09666 | Open Evaluation Agent: Efficient and Promptable Evaluation of Visual Generative Models — verifier efficiency vs accuracy trade-off | arXiv 2608.09666, re-verified 2026-10-12 | none |
| 5 | https://arxiv.org/abs/2606.26122 | DocArena: Turning Raw Documents into Controllable Training Environments for Document Search Agents — controllable env construction from raw inputs | arXiv 2606.26122, re-verified 2026-10-12 | none |
| 6 | https://arxiv.org/abs/2608.05519 | EcoAgent-Bench: Evaluating Economic Decision-Making in Budget-Constrained LLM Agents — budget-constrained verifiable envs | arXiv 2608.05519, re-verified 2026-10-12 | none |
| 7 | https://arxiv.org/abs/2512.09543 | SWEnergy: An Empirical Study on Energy Efficiency in Agentic Issue Resolution Frameworks with SLMs — per-step cost measurement on agent trajectories | arXiv 2512.09543, re-verified 2026-10-12 | none |
| 8 | https://arxiv.org/abs/2306.08568 | WizardCoder: Empowering Code Large Language Models with Evol-Instruct (2023) — eval-driven code generation; shows pass-rate calibration practice | arXiv 2306.08568, re-verified 2026-10-12 | none |
| 9 | https://arxiv.org/abs/2406.09338 | Learning the Influence Graph of a High-Dimensional Markov Process with Memory (2024) — verification of process models | arXiv 2406.09338, re-verified 2026-10-12 | none |
| 10 | https://arxiv.org/abs/2110.14111 | Kronecker products of Perron similarities — kept as a control: confirms the arXiv API path works and returns real metadata | arXiv 2110.14111, re-verified 2026-10-12 | no domain content; control only |

## Version-sensitive facts
- Sandbox APIs (container exec, network policy) change between versions. The contract in
  `references/sandbox-contract.md` was verified against the harness on 2026-10-12; re-verify on upgrade.
- `verify_harness.py` MIN_POWER default 0.30 is a heuristic, not a theorem; it was calibrated
  on the shipped fixtures. Re-derive on a new task family.

## Conflicts
- No content conflicts. Source 1 (openai.com/index/evals/) is now bot-blocked (HTTP 403 on
  re-verification 2026-10-12); source 2 (github.com/openai/evals) is the working primary and
  was re-verified HTTP 200. The arXiv API returned the expected metadata for every ID,
  confirming the retrieval path.
