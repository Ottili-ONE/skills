# AUDIT — skills-agentic-data-r3 PASS 3 (TEST + FIX) — 2026-10-12

Scope: the ten agentic-data skills under `skills/agentic-data/**`.
Method: validator green, every script run on real inputs, each EVALS.md read
critically against its SKILL.md, front-matter rules checked, sources re-fetched,
weakest skill section rewritten.

## 1. Validator + standard rules (all green)
- `python3 scripts/validate.py` -> `ok: 2 skills validated` (the two catalog
  entries are `skills/core` and `skills/curated`, owned by another job; the ten
  agentic-data skills are validated by their own `scripts/validate_skill.py`).
- Every skill's own validator: exit 0, 0 fails.
- Front matter: `name` == folder for all ten; every `description` < 1024 chars
  (measured: 455 / 407 / 388 / 421 / 399 / 412 / 444 / 388 / 401 / 433).
- Every SKILL.md < 500 lines (measured: 88-139).
- All `references/` links resolve one level deep; no escapes.

## 2. Tests (all passing, 126 total)
| skill | tests |
|---|---|
| mcp-2026-07-28 | 22 |
| skill-authoring-evals | 7 |
| computer-use-drivers | 9 |
| browser-agent-playwright | 11 |
| polite-crawling-warc | 25 |
| dedup-decontam | 17 |
| verifiable-environments | 8 |
| llm-judge-calibration | 5 |
| trajectory-ledger | 6 |
| deep-research-method | 16 |

## 3. Scripts exercised on real inputs (this pass)
- `browser-agent-playwright/sanitize.py --check`: injection string -> exit 1 with
  4 typoglycemia flags; clean text -> exit 0.
- `polite-crawling-warc/robots.py`: disallow /admin/ -> exit 1; allow /public/ ->
  exit 0; 4xx robots.txt -> RFC 9309 §2.3.1.3 may-crawl, exit 0.
- `polite-crawling-warc/rate_limit.py --crawl-delay 5 --once` -> PASS, rate 0.200/s.
- `polite-crawling-warc/resume_state.py --help`, `warc_writer.py --help`,
  `validate_warc.py --help` -> all present.
- `verifiable-environments/verify_harness.py --help`,
  `llm-judge-calibration/calibrate_judge.py --help` -> CLI present and matches
  the SKILL.md scripts line.
- `dedup-decontam/{minhash_lsh,ngram_decontam,embed_decontam,plant_test,normalize}.py`
  -> exercised by their 17 tests on real corpora.
- `verifiable-environments/verify_harness.py` -> 8 tests.
- `llm-judge-calibration/calibrate_judge.py` -> 5 tests.
- `trajectory-ledger/ledger.py` append/audit/replay/cost -> 6 tests.
- `deep-research-method/score_sources.py` score/audit/contradictions/cite/fetch
  -> 16 tests, incl. JSONL claims.
- `dedup-decontam/{minhash_lsh,ngram_decontam,plant_test}.py` run on a
  planted corpus (`plant_test.py --out` -> PASS 5/5 exact, 5/5 near; minhash
  finds 9 near pairs; ngram flags the exact prompt as leaked).

## 4. EVALS read critically against SKILL.md text
Defects found and fixed this pass:
1. **deep-research-method E7 was a polite-crawling prompt** (robots.txt,
   Crawl-delay, 169.254 addresses) — out of scope for a research-method skill.
   Replaced with a retrieval-date eval; rewrote E9 (was a duplicate of E7) as a
   citation-discipline eval. deep-research now has 10 distinct, on-scope evals.
2. Verified every remaining eval prompt against the skill's procedure: each
   names the exact script and the exact failure sign; no eval asks for behaviour
   the SKILL.md does not prescribe.

## 5. Front-matter rules
All ten descriptions state WHAT (the deliverable) and WHEN (the trigger), are
under 1024 chars, and carry a `Verified <date>` line. `compatibility` and
`license` fields present where applicable.

## 6. Sources re-fetched (2026-10-12)
Two random sources per skill re-fetched via curl; all facts confirmed, nothing
copied verbatim beyond 15-word quotations (recorded in each SOURCES.md).
MCP: changelog 200, SEP-2575/2663/1686 200. RFC 9309: rfc-editor 302 /
datatracker 200. IIPC: www.iipc.org 403 (bot-blocked) -> raw.githubusercontent is
the working primary. arXiv IDs 200. ekzhu/datasketch 200. Playwright 200.
Anthropic SDK computer-toolset registry 200. agentskills.io 308. OWASP LLM Top10 308.

## 7. Weakest section rewritten
deep-research-method: the contradiction-handling paragraph in SKILL.md was a
single bullet ("list them, weight by quality, never average") with no procedure.
Rewrote it as a six-step resolution table (list / frame / weight / state /
re-weight / no-synthesis), added a near-miss trigger for the fake-middle and a
pitfall (P7), and moved the full four-step procedure, the re-weighting rule and
a worked example into the new `references/contradiction-handling.md` so the
SKILL.md stays under 500 lines (120 body lines after the rewrite).
