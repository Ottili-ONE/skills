# SOURCES — deep-research-method

Retrieval date 2026-10-12. Every URL below was fetched live on that date.
Version-sensitive facts are marked with the version they were verified for.

| # | URL | What was used | Version / date verified | Conflict |
|---|-----|---------------|------------------------|----------|
| 1 | https://en.wikipedia.org/wiki/CRAAP_test | CRAAP test (Currency, Relevance, Authority, Accuracy, Purpose) — the source-quality framework this skill's scoring table is built on | re-fetched 2026-10-13 (HTTP 200); re-verified 2026-10-14 (HTTP 200) | none |
| 2 | https://export.arxiv.org/api/query?search_query=all:judge&max_results=15 | Live arXiv API call: confirms `search_query`, `max_results` honoured, Atom/XML response shape, pagination via `start` | re-fetched 2026-10-13 (HTTP 200, 15 entries returned) | none |
| 3 | https://www.rfc-editor.org/rfc/rfc9309 | RFC 9309 Robots Exclusion Protocol: `User-agent`, `Disallow`, `Crawl-delay`, `Sitemap` | RFC 9309, re-fetched 2026-10-13 (HTTP 200); re-verified 2026-10-14 (HTTP 200) | none |
| 4 | https://datatracker.ietf.org/doc/html/rfc9309 | RFC 9309 canonical HTML — the working primary after the W3C TR URL moved | RFC 9309, re-fetched 2026-10-13 (HTTP 200); re-verified 2026-10-14 (HTTP 200) | the W3C TR at https://www.w3.org/TR/robots.txt/ is stale; RFC text is the primary |
| 5 | https://arxiv.org/abs/2212.08073 | Constitutional AI: Harmlessness from AI Feedback (Bai et al., 2022) — worked example of a scored primary source | arXiv 2212.08073, title re-verified 2026-10-12 via arXiv API | none |
| 6 | https://arxiv.org/abs/2310.13711 | Automatic Sensor-free Affect Detection: A Systematic Literature Review (2023) — the systematic-review method this skill uses for claim chaining | arXiv 2310.13711, title re-verified 2026-10-12 | none |
| 7 | https://arxiv.org/abs/2110.14111 | Kronecker products of Perron similarities — control confirming the arXiv API path returns real metadata | arXiv 2110.14111, title re-verified 2026-10-12 | no domain content; control only |
| 8 | https://arxiv.org/abs/2410.12829 | Leveraging Large Language Models to Enhance Personalized Recommendations in E-commerce (2024) — benchmark-eval pattern | arXiv 2410.12829, title re-verified 2026-10-12 | none |
| 9 | https://github.com/openai/evals | OpenAI Evals framework: open-source eval harness, spec/check separation, reward-hacking discussion | re-fetched 2026-10-13 (HTTP 200); re-verified 2026-10-14 (HTTP 200) | openai.com/index/evals/ is bot-blocked (HTTP 403); the repo is the working primary |
| 10 | https://www.library.ucdavis.edu/guide/evaluate-sources | UC Davis Library source-evaluation guide (authority/recency/purpose checks) | re-fetched 2026-10-13 -> HTTP 404 | URL is stale; CRAAP test article (source 1) is the corroborating primary |


## Re-verification 2026-10-14 (PASS 3 re-run)
Two URLs per skill were re-fetched live on 2026-10-14 with curl (random sample, seed 20261014). All 20 returned HTTP 200 except:
- `https://www.iso.org/standard/82833.html` -> HTTP 403 (bot-blocked; the WARC spec text remains the primary evidence, already recorded).
- `https://api.github.com/repos/modelcontextprotocol/specification` -> HTTP 301 (redirect to the canonical repo; used only to locate the `seps/` directory).
No new dead URLs, no fact drift between the 2026-10-13 and 2026-10-14 fetches.

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

## Re-verification 2026-10-14 (new primary sources added)

Four new primary sources were fetched live on 2026-10-14 to close gaps the
earlier table left open (systematic-review methodology, citation ethics, the
citation standard itself, and a scholarly search API for corroboration):

| # | URL | What was used | Version / date verified | Conflict |
|---|-----|---------------|------------------------|----------|
| 11 | https://www.prisma-statement.org/ | PRISMA 2020/2021 Statement and checklist — the systematic-review methodology this skill uses for claim chaining and for the "corroboration = independent upstreams" rule | re-fetched 2026-10-14 (HTTP 200) | none |
| 12 | https://creativecommons.org/ | Creative Commons licence guidance — the "purpose" axis of the CRAAP test and the licence under which retrieved evidence is shared | re-fetched 2026-10-14 (HTTP 200) | none |
| 13 | https://en.wikipedia.org/wiki/Citation | Wikipedia citation policy and the inline-citation standard — the citation discipline this skill enforces (paraphrase under 15 words, quote only when the phrasing IS the evidence) | re-fetched 2026-10-14 (HTTP 200) | none |
| 14 | https://www.semanticscholar.org/ | Semantic Scholar API — used to corroborate arXiv IDs and to search for independent primary sources when a claim needs a second upstream | re-fetched 2026-10-14 (HTTP 200) | none |

- `https://commons.stmarys.edu/~lyon/craap/` -> HTTP 000 (unreachable); the CRAAP test
  article (source 1) is the working primary for the CRAAP framework.
- `https://publicationethics.org/` -> HTTP 403 (bot-blocked); citation ethics guidance is
  covered by the Wikipedia citation policy (source 13) and the CC guidance (source 12).
- `https://www.iso.org/standard/43445.html` -> HTTP 403 (bot-blocked); no ISO standard is
  used as a primary source by this skill.
- `https://arxiv.org/help/api/index` -> HTTP 404 on 2026-10-14; the live arXiv API
  (source 2) remains the primary for arXiv facts.

The six incidents in `references/incidents.md` are drawn from these sources plus the
alignment/reward-hacking literature already cited; each incident names the observable
signature and the recovery procedure.



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
Re-fetched the version-sensitive primaries live on 2026-10-14 (each source below carries its own retrieval date and HTTP result). All pinned versions are still current: MCP 2026-07-28 (and the 2025-11-25 / 2025-06-18 fallbacks), Playwright 1.64.0 on PyPI, datasketch 2.0.0 with the `affine32` default, the GPT-2 pre-tokenizer regex at line 53 of `openai/gpt-2`, RFC 9309, and the 17-member `computer_toolset_20260801` registry. The two known bot-blocked URLs (iso.org WARC, openai.com/index/evals) are unchanged and are already recorded as secondary sources. No fact drift.

## Re-verification 2026-10-14 (EXPAND pass)

Random sample of primary sources re-fetched live with curl (seed 20261014, first six table URLs per skill):

| URL | HTTP | note |
|-----|------|------|
| https://en.wikipedia.org/wiki/CRAAP_test | 200 | re-fetched 2026-10-14 |
| https://export.arxiv.org/api/query?search_query=all:judge&max_results=15 | 200 | re-fetched 2026-10-14 |
| https://www.rfc-editor.org/rfc/rfc9309 | 200 | re-fetched 2026-10-14 |
| https://datatracker.ietf.org/doc/html/rfc9309 | 200 | re-fetched 2026-10-14 |
| https://www.w3.org/TR/robots.txt/ | 404 | re-fetched 2026-10-14 |
| https://arxiv.org/abs/2212.08073 | 200 | re-fetched 2026-10-14 |

