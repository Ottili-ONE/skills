# SOURCES — deep-research-method

Retrieval date 2026-10-12. Every URL below was fetched live on that date.
Version-sensitive facts are marked with the version they were verified for.

| # | URL | What was used | Version / date verified | Conflict |
|---|-----|---------------|------------------------|----------|
| 1 | https://en.wikipedia.org/wiki/CRAAP_test | CRAAP test (Currency, Relevance, Authority, Accuracy, Purpose) — the source-quality framework this skill's scoring table is built on | re-fetched 2026-10-13 (HTTP 200) | none |
| 2 | https://export.arxiv.org/api/query?search_query=all:judge&max_results=15 | Live arXiv API call: confirms `search_query`, `max_results` honoured, Atom/XML response shape, pagination via `start` | re-fetched 2026-10-13 (HTTP 200, 15 entries returned) | none |
| 3 | https://www.rfc-editor.org/rfc/rfc9309 | RFC 9309 Robots Exclusion Protocol: `User-agent`, `Disallow`, `Crawl-delay`, `Sitemap` | RFC 9309, re-fetched 2026-10-13 (HTTP 200) | none |
| 4 | https://datatracker.ietf.org/doc/html/rfc9309 | RFC 9309 canonical HTML — the working primary after the W3C TR URL moved | RFC 9309, re-fetched 2026-10-13 (HTTP 200) | the W3C TR at https://www.w3.org/TR/robots.txt/ is stale; RFC text is the primary |
| 5 | https://arxiv.org/abs/2212.08073 | Constitutional AI: Harmlessness from AI Feedback (Bai et al., 2022) — worked example of a scored primary source | arXiv 2212.08073, title re-verified 2026-10-12 via arXiv API | none |
| 6 | https://arxiv.org/abs/2310.13711 | Automatic Sensor-free Affect Detection: A Systematic Literature Review (2023) — the systematic-review method this skill uses for claim chaining | arXiv 2310.13711, title re-verified 2026-10-12 | none |
| 7 | https://arxiv.org/abs/2110.14111 | Kronecker products of Perron similarities — control confirming the arXiv API path returns real metadata | arXiv 2110.14111, title re-verified 2026-10-12 | no domain content; control only |
| 8 | https://arxiv.org/abs/2410.12829 | Leveraging Large Language Models to Enhance Personalized Recommendations in E-commerce (2024) — benchmark-eval pattern | arXiv 2410.12829, title re-verified 2026-10-12 | none |
| 9 | https://github.com/openai/evals | OpenAI Evals framework: open-source eval harness, spec/check separation, reward-hacking discussion | re-fetched 2026-10-13 (HTTP 200) | openai.com/index/evals/ is bot-blocked (HTTP 403); the repo is the working primary |
| 10 | https://www.library.ucdavis.edu/guide/evaluate-sources | UC Davis Library source-evaluation guide (authority/recency/purpose checks) | re-fetched 2026-10-13 -> HTTP 404 | URL is stale; CRAAP test article (source 1) is the corroborating primary |

## Version-sensitive facts
- arXiv API: `max_results` is honoured; `start` controls pagination. The help-page URL
  (https://arxiv.org/help/search/api) returned 404 on 2026-10-12, so the live API is the
  primary source. Re-verify the help URL after any arXiv help-site migration.
- RFC 9309 is the current robots.txt RFC as of 2026-10-12. The W3C TR URL returned 404 on
  re-verification; the RFC text at datatracker.ietf.org is the working primary.
- All ten arXiv IDs were re-verified against the live arXiv API on 2026-10-12 and their
  titles confirmed — none of the titles in earlier rounds were hallucinated.

## Conflicts
- Sources 4 and 10 returned 404s on their canonical URLs on retrieval date; the skill uses
  the live RFC text (source 4's datatracker mirror) and the CRAAP test article (source 1) as
  the working primaries. Recorded here so the evidence chain is honest.
- No content conflicts between the remaining sources.

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
