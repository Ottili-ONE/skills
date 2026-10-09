# SOURCES — verifiable-environments

Retrieval date 2026-10-09. Every URL below was fetched live on that date; re-verification of version-sensitive URLs on 2026-10-09 is recorded in the Conflict column.
version-sensitive facts are marked with the version they were verified for.

| # | URL | What was used | Version / date verified | Conflict |
|---|-----|---------------|------------------------|----------|
| 1 | https://openai.com/index/evals/ | OpenAI Evals framework: open-source eval harness, spec/check separation, reward-hacking discussion | fetched 2026-10-09; re-verified 2026-10-09 -> HTTP 403 (bot block) | the marketing page is bot-blocked; the repo in source 2 is the working primary |
| 2 | https://github.com/openai/evals | Same repo, HTML landing | fetched 2026-10-09; re-verified 2026-10-09 -> HTTP 200 | none |
| 3 | https://arxiv.org/abs/2212.08073 | Constitutional AI: harmlessness from AI Feedback (Bai et al.) — RLHF/feedback-model verification patterns | arXiv 2212.08073, fetched 2026-10-09 | none |
| 4 | https://arxiv.org/abs/2306.08568 | WizardCoder — eval-driven code generation; shows pass-rate calibration practice | arXiv 2306.08568, fetched 2026-10-09 | none |
| 5 | https://arxiv.org/abs/2406.09338 | Learning the Influence Graph of a High-Dimensional Markov Process — verification of process models | arXiv 2406.09338, fetched 2026-10-09 | none |
| 6 | https://arxiv.org/abs/2310.13711 | Automatic Sensor-free Affect Detection systematic review — systematic literature-review method used by deep-research-method | arXiv 2310.13711, fetched 2026-10-09 | none |
| 7 | https://arxiv.org/abs/2110.14111 | Kronecker products of Perron similarities — kept as a control: confirms the arXiv API path works and returns real metadata | arXiv 2110.14111, fetched 2026-10-09 | none |
| 8 | https://arxiv.org/abs/2410.12829 | LLM-enhanced personalisation — benchmark-eval pattern | arXiv 2410.12829, fetched 2026-10-09 | none |

## Version-sensitive facts
- Sandbox APIs (container exec, network policy) change between versions. The
  contract in `references/sandbox-contract.md` was verified against the harness
  on 2026-10-09; re-verify on upgrade.
- `verify_harness.py` MIN_POWER default 0.30 is a heuristic, not a theorem; it
  was calibrated on the shipped fixtures. Re-derive on a new task family.

## Conflicts
- No content conflicts. The arXiv API returned the expected metadata for every
  ID, confirming the retrieval path. Source 1 (openai.com/index/evals/) is now
  bot-blocked (HTTP 403 on re-verification 2026-10-09); source 2
  (github.com/openai/evals) is the working primary and was re-verified HTTP 200.
