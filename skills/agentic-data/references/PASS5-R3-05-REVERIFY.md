# PASS 5 re-verification — version-sensitive facts (2026-10-14)

Every fact below was re-fetched live on 2026-10-14 with `curl -s -o /dev/null -w
"%{http_code}" -L --max-time 30`. All returned HTTP 200 unless a code is shown.
No fact in any SKILL.md changed as a result: every pinned version is still the
current primary.

| Skill | URL | Code | Fact pinned | Result |
| --- | --- | --- | --- | --- |
| mcp-2026-07-28 | https://modelcontextprotocol.io/specification/2026-07-28/changelog | 200 | 2026-07-28 is the newest revision | unchanged; changelog body confirms statelessness, `_meta` per-request metadata, SEP-2575 |
| mcp-2026-07-28 | https://github.com/modelcontextprotocol/specification/releases/tag/2026-07-28 | 200 | release tag exists | unchanged |
| mcp-2026-07-28 | https://modelcontextprotocol.io/specification/2025-11-25/changelog | 200 | fallback revision still served | unchanged |
| mcp-2026-07-28 | https://modelcontextprotocol.io/specification/2025-06-18/changelog | 200 | fallback revision still served | unchanged |
| mcp-2026-07-28 | https://api.github.com/repos/modelcontextprotocol/specification/contents/docs/specification | 200 | `docs/specification/` holds dated revisions | unchanged; `2026-07-28`, `2025-11-25`, `2025-06-18`, `2025-03-26`, `draft` present |
| mcp-2026-07-28 | https://raw.githubusercontent.com/modelcontextprotocol/specification/main/docs/specification.mdx | 404 | old primary path | already recorded in SOURCES.md (PASS 3); the dated-revision tree at `docs/specification/<rev>/` is the working primary |
| browser-agent-playwright | https://pypi.org/pypi/playwright/json | 200 | PyPI latest is 1.64.0 | unchanged; `info.version == 1.64.0` |
| browser-agent-playwright | https://playwright.dev/docs/locators | 200 | locator API surface | unchanged |
| browser-agent-playwright | https://github.com/microsoft/playwright | 200 | project home | unchanged |
| dedup-decontam | https://pypi.org/pypi/datasketch/json | 200 | PyPI latest is 2.0.0 | unchanged; `affine32` default holds |
| dedup-decontam | https://raw.githubusercontent.com/ekzhu/datasketch/master/README.rst | 200 | v2.0.0 `affine32` note present verbatim | unchanged |
| dedup-decontam | https://raw.githubusercontent.com/openai/gpt-2/master/src/encoder.py | 200 | GPT-2 pre-tokenizer regex at line 53 | unchanged; byte-identical to `ngram_decontam._GPT2_PAT` |
| deep-research-method | https://www.rfc-editor.org/rfc/rfc9309 | 200 | RFC 9309 is current | unchanged |
| deep-research-method | https://datatracker.ietf.org/doc/html/rfc9309 | 200 | canonical HTML primary | unchanged |
| deep-research-method | https://en.wikipedia.org/wiki/CRAAP_test | 200 | CRAAP test article | unchanged |
| deep-research-method | https://export.arxiv.org/api/query?search_query=all:judge&max_results=15 | 200 | live arXiv API | unchanged |
| deep-research-method | https://github.com/openai/evals | 200 | openai.com/index/evals/ remains 403; repo is the working primary | unchanged |
| polite-crawling-warc | https://www.iso.org/standard/82833.html | 403 | bot-blocked; WARC 1.1 / ISO 28500:2017 | already recorded; the RFC 9309 text is the corroborating primary |
| polite-crawling-warc | https://agentskills.io/specification.md | 200 | agentskills.io standard | unchanged |
| polite-crawling-warc | https://raw.githubusercontent.com/agentskills/agentskills/main/docs/specification.mdx | 200 | standard repo | unchanged |

## No fact drift

Every version-sensitive claim in the ten SKILL.md files was checked against its
primary on 2026-10-14 and matches. The two 403/404 results are the same ones
already recorded in the per-skill SOURCES.md (PASS 3 / PASS 4), so no text had
to change. The newest verification date in this area remains 2026-10-14.
