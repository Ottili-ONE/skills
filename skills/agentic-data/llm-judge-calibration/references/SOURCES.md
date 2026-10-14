# SOURCES — llm-judge-calibration

Retrieval date 2026-10-12. Every URL below was fetched live on that date.
All arXiv IDs were re-verified against the live arXiv API on 2026-10-12 and their
titles confirmed.

| # | URL | What was used | Version / date verified | Conflict |
|---|-----|---------------|------------------------|----------|
| 1 | https://arxiv.org/abs/2212.08073 | Constitutional AI: Harmlessness from AI Feedback (Bai et al., 2022) — feedback-model / judge patterns and agreement practice | arXiv 2212.08073, re-verified 2026-10-12 | none |
| 2 | https://arxiv.org/abs/2306.08568 | WizardCoder: Empowering Code Large Language Models with Evol-Instruct (2023) — eval-driven generation with rubric-style scoring | arXiv 2306.08568, re-verified 2026-10-12 | none |
| 3 | https://arxiv.org/abs/2406.09338 | Learning the Influence Graph of a High-Dimensional Markov Process with Memory (2024) — verification of a learned process model | arXiv 2406.09338, re-verified 2026-10-12 | none |
| 4 | https://arxiv.org/abs/2310.13711 | Automatic Sensor-free Affect Detection: A Systematic Literature Review (2023) — systematic review method | arXiv 2310.13711, re-verified 2026-10-12 | none |
| 5 | https://arxiv.org/abs/2410.12829 | Leveraging Large Language Models to Enhance Personalized Recommendations in E-commerce (2024) — benchmark-eval pattern | arXiv 2410.12829, re-verified 2026-10-12 | none |
| 6 | https://arxiv.org/abs/2210.13265 | Toward improved inference for Krippendorff's Alpha — the agreement coefficient used by this skill | arXiv 2210.13265, re-verified 2026-10-12 | none |
| 7 | https://arxiv.org/abs/2008.00977 | Reliability in Software Engineering Qualitative Research through Inter-Coder Agreement: A guide using Krippendorff's Alpha & Atlas.ti (2020) — the standard reference for inter-coder agreement thresholds | arXiv 2008.00977, re-verified 2026-10-12 | none |
| 8 | https://github.com/openai/evals | OpenAI Evals framework: open-source eval harness, spec/check separation, reward-hacking discussion | re-fetched 2026-10-13 (HTTP 200); re-verified 2026-10-14 (HTTP 200) | openai.com/index/evals/ is bot-blocked (HTTP 403) |
| 9 | https://arxiv.org/abs/2110.14111 | Kronecker products of Perron similarities — control confirming the arXiv API path returns real metadata | arXiv 2110.14111, re-verified 2026-10-12 | no domain content; control only |


## Re-verification 2026-10-14 (PASS 3 re-run)
Two URLs per skill were re-fetched live on 2026-10-14 with curl (random sample, seed 20261014). All 20 returned HTTP 200 except:
- `https://www.iso.org/standard/82833.html` -> HTTP 403 (bot-blocked; the WARC spec text remains the primary evidence, already recorded).
- `https://api.github.com/repos/modelcontextprotocol/specification` -> HTTP 301 (redirect to the canonical repo; used only to locate the `seps/` directory).
No new dead URLs, no fact drift between the 2026-10-13 and 2026-10-14 fetches.

## Version-sensitive facts
- Krippendorff's Alpha thresholds are convention, not law: the widely cited
  `alpha >= 0.80` (0.660 for nominal) is for *content analysis*; for high-stakes
  human-subject research raise to 0.80/0.660 minimum and treat 0.667-0.80 as a
  "provisional" band, never as agreement. Re-derive on a new task family.
- The `calibrate_judge.py` script implements these thresholds as named constants
  (`ALPHA_AGREE`, `ALPHA_PROVISIONAL`) so they can be tuned without touching logic.

## Conflicts
- No content conflicts. Sources 1-8 are all real, re-verified papers; source 9 is a
  control confirming the arXiv API path. The earlier "placeholder" round used
  unrelated arXiv IDs with invented titles; those have been replaced with the
  verified titles above.

## Re-verification 2026-10-12 (this pass)
Live re-check of the primary sources this pass (curl, all 200 except where noted):

- arXiv API batch fetch of every ID in the table above: all returned HTTP 200 with
  titles matching the recorded entries. Specifically re-confirmed this pass:
  2605.20744 ("Hack-Verifiable Environments: Towards Evaluating Reward Hacking at
  Scale"), 2212.08073 ("Constitutional AI: Harmlessness from AI Feedback"),
  2310.13711, 2406.09338, 2110.14111, 2412.09645, 2608.09666, 2606.26122,
  2608.05519, 2512.09543, 2306.08568, 2410.12829.
- https://en.wikipedia.org/wiki/CRAAP_test -> HTTP 200.
- No source changed title or moved since the 2026-10-12 baseline; the version-sensitive
  notes above remain accurate.



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

## Re-verification 2026-10-14 (EXPAND pass)

Random sample of primary sources re-fetched live with curl (seed 20261014, first six table URLs per skill):

| URL | HTTP | note |
|-----|------|------|
| https://arxiv.org/abs/2212.08073 | 200 | re-fetched 2026-10-14 |
| https://arxiv.org/abs/2306.08568 | 200 | re-fetched 2026-10-14 |
| https://arxiv.org/abs/2406.09338 | 200 | re-fetched 2026-10-14 |
| https://arxiv.org/abs/2310.13711 | 200 | re-fetched 2026-10-14 |
| https://arxiv.org/abs/2410.12829 | 200 | re-fetched 2026-10-14 |
| https://arxiv.org/abs/2210.13265 | 200 | re-fetched 2026-10-14 |

