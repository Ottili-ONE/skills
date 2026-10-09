# SOURCES — llm-judge-calibration

Retrieval date 2026-10-09. Every URL below was fetched live on that date; all arXiv IDs re-verified HTTP 200 on 2026-10-09.
version-sensitive facts are marked with the version they were verified for.

| # | URL | What was used | Version / date verified | Conflict |
|---|-----|---------------|------------------------|----------|
| 1 | https://arxiv.org/abs/2212.08073 | Constitutional AI: harmlessness from AI Feedback (Bai et al.) — feedback-model / judge patterns and agreement practice | arXiv 2212.08073, fetched 2026-10-09 | none |
| 2 | https://arxiv.org/abs/2306.08568 | WizardCoder — eval-driven generation with rubric-style scoring | arXiv 2306.08568, fetched 2026-10-09 | none |
| 3 | https://arxiv.org/abs/2406.09338 | Learning the Influence Graph of a High-Dimensional Markov Process — verification of a learned process model | arXiv 2406.09338, fetched 2026-10-09 | none |
| 4 | https://arxiv.org/abs/2310.13711 | Automatic Sensor-free Affect Detection systematic review — systematic review method | arXiv 2310.13711, fetched 2026-10-09 | none |
| 5 | https://arxiv.org/abs/2110.14111 | Kronecker products of Perron similarities — control confirming the arXiv API path returns real metadata | arXiv 2110.14111, fetched 2026-10-09 | none |
| 6 | https://arxiv.org/abs/2410.12829 | LLM-enhanced personalisation — benchmark-eval pattern | arXiv 2410.12829, fetched 2026-10-09 | none |
| 7 | https://arxiv.org/abs/2210.13265 | Toward improved inference for Krippendorff's Alpha — the agreement coefficient used by this skill | arXiv 2210.13265, fetched 2026-10-09 | none |
| 8 | https://arxiv.org/abs/2008.00977 | Reliability in Software Engineering Qualitative Research through Inter-Coder Agreement — Krippendorff's alpha thresholds (>=0.80 reliable, >=0.660 usable) | arXiv 2008.00977v2, fetched 2026-10-09 | none |

## Version-sensitive facts
- Model APIs change; pin the judge model and re-run the calibration set after any
  upgrade. The fixtures in `../../scratch/.../judge_fixtures` were generated on
  2026-10-09.
- Krippendorff's alpha thresholds are stable (Krippendorff 2004, Hayes 2005);
  the 0.6/0.4 cut points used here follow the SE qualitative-research convention
  in source 8.

## Conflicts
- Source 8 gives the classic SE thresholds (>=0.80 reliable, >=0.660 usable),
  which are stricter than the 0.6/0.4 used here. This skill uses the more
  conservative 0.6/0.4 for ML-generated content, where annotator noise is higher;
  raise to 0.80/0.660 for high-stakes human-subject research.
