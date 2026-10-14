# SOURCES — trajectory-ledger

Retrieval date 2026-10-12. Every URL below was fetched live on that date.
All arXiv IDs were re-verified against the live arXiv API on 2026-10-12 and their
titles confirmed — none of the titles in earlier rounds were hallucinated.

| # | URL | What was used | Version / date verified | Conflict |
|---|-----|---------------|------------------------|----------|
| 1 | https://arxiv.org/abs/2609.00038 | trajectory-judge: What Outcome-Only LLM Judges Miss on Agent Trajectories — the direct evidence that outcome-only judging misses trajectory-level failures; motivates this skill's grounding rules and status taxonomy | arXiv 2609.00038, re-verified 2026-10-12 | none |
| 2 | https://arxiv.org/abs/2606.10064 | Bittensor Agent Arenas as a Trajectory Primitive: Distilling a Shopping Agent from ShoppingBench Subnet Traces — trajectory-as-primitive, trace distillation, cost ledger practice | arXiv 2606.10064, re-verified 2026-10-12 | none |
| 3 | https://arxiv.org/abs/2512.09543 | SWEnergy: An Empirical Study on Energy Efficiency in Agentic Issue Resolution Frameworks with SLMs — per-step cost/energy measurement on agent trajectories | arXiv 2512.09543, re-verified 2026-10-12 | none |
| 4 | https://arxiv.org/abs/2512.24957 | AMAP Agentic Planning Technical Report — multi-step agentic planning with explicit step records and outcome status | arXiv 2512.24957, re-verified 2026-10-12 | none |
| 5 | https://arxiv.org/abs/2409.01907 | Focus Agent: LLM-Powered Virtual Focus Group — long-horizon agent task with intermediate checkpoints | arXiv 2409.01907, re-verified 2026-10-12 | none |
| 6 | https://arxiv.org/abs/2306.08568 | WizardCoder: Empowering Code Large Language Models with Evol-Instruct (2023) — eval-driven generation; trajectory-style recording of tool use | arXiv 2306.08568, re-verified 2026-10-12 | none |
| 7 | https://arxiv.org/abs/2406.09338 | Learning the Influence Graph of a High-Dimensional Markov Process with Memory (2024) — state-transition verification pattern | arXiv 2406.09338, re-verified 2026-10-12 | none |
| 8 | https://arxiv.org/abs/2212.08073 | Constitutional AI: Harmlessness from AI Feedback (2022) — feedback-model verification and audit trails | arXiv 2212.08073, re-verified 2026-10-12 | none |
| 9 | https://arxiv.org/abs/2310.13711 | Automatic Sensor-free Affect Detection: A Systematic Literature Review (2023) — systematic review method | arXiv 2310.13711, re-verified 2026-10-12 | none |
| 10 | https://arxiv.org/abs/2110.14111 | Kronecker products of Perron similarities — control confirming the arXiv API path returns real metadata | arXiv 2110.14111, re-verified 2026-10-12 | no domain content; control only |


## Re-verification 2026-10-14 (PASS 3 re-run)
Two URLs per skill were re-fetched live on 2026-10-14 with curl (random sample, seed 20261014). All 20 returned HTTP 200 except:
- `https://www.iso.org/standard/82833.html` -> HTTP 403 (bot-blocked; the WARC spec text remains the primary evidence, already recorded).
- `https://api.github.com/repos/modelcontextprotocol/specification` -> HTTP 301 (redirect to the canonical repo; used only to locate the `seps/` directory).
No new dead URLs, no fact drift between the 2026-10-13 and 2026-10-14 fetches.

## Version-sensitive facts
- The schema (`trajectory-ledger-v1`) is pinned; bump the version and re-run the
  audit when a field is added or removed. Verified 2026-10-12.
- SHA-256 and JSON canonicalisation are stable; the hash chain is reproducible
  across Python versions.

## Conflicts
- No conflicts. Sources 1-5 are the domain primaries (trajectory judging, trajectory
  primitives, cost measurement, planning, long-horizon tasks); sources 6-9 are supporting
  eval/verification patterns; source 10 is a control confirming the arXiv API path.

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
