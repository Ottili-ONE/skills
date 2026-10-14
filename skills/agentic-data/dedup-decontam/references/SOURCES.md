# SOURCES — dedup-decontam

Retrieval date 2026-10-12. Every URL below was fetched live on that date.
Re-verified 2026-10-13 (PASS 3): datasketch is still at 2.0.0 on PyPI (the `affine32` default holds); the GPT-2 pre-tokenizer regex was re-fetched from openai/gpt-2 `src/encoder.py` line 53 and matches the pattern baked into `ngram_decontam._GPT2_PAT` (`'s|'t|'re|'ve|'m|'ll|'d| ?\p{L}+| ?\p{N}+| ?[^\s\p{L}\p{N}]+|\s+(?!\S)|\s+`). The MMLU repo (hendrycks/test) contains no decontamination code of its own -- the n=13 window comes from the MMLU paper (arXiv 2009.03300) and the community decontamination practice; the repo is cited as the benchmark source, not the n-gram source.
Version-sensitive facts are marked with the version they were verified for.

| # | URL | What was used | Version / date verified | Conflict |
|---|-----|---------------|------------------------|----------|
| 1 | https://github.com/ekzhu/datasketch | datasketch: the reference MinHash/LSH implementation in Python. Confirms `MinHash` (Jaccard estimate, `num` permutations default 128), `MinHash LSH` index (threshold query, `b` bands / `r` rows), and the v2.0.0 breaking change to the `affine32` permutation scheme | re-fetched 2026-10-13 (HTTP 200); re-verified 2026-10-14 (HTTP 200); README.rst re-fetched HTTP 200 | the README is `README.rst`, not `README.md`; the canonical repo is `ekzhu/datasketch`, NOT `datasketch/datasketch` (404) |
| 2 | https://raw.githubusercontent.com/ekzhu/datasketch/master/README.rst | The v2.0.0 note: default permutation scheme changed to `affine32`, which fixes a similarity over-estimation bias on large sets, halves sketch memory, ~4x faster updates. Hash values differ from earlier versions — rebuild persisted sketches or pass `scheme="legacy"` | re-fetched 2026-10-13 (HTTP 200); re-verified 2026-10-14 (HTTP 200) | none |
| 3 | https://arxiv.org/abs/1811.04633 | A Review for Weighted MinHash Algorithms — the weighted-Jaccard estimator family used when sets carry weights | arXiv 1811.04633, title re-verified 2026-10-12 | none |
| 4 | https://arxiv.org/abs/1407.4416 | In Defense of MinHash Over SimHash — why MinHash (Jaccard) is preferred over SimHash (cosine) for near-duplicate document detection | arXiv 1407.4416, title re-verified 2026-10-12 | none |
| 5 | https://arxiv.org/abs/1710.08436 | HyperMinHash: MinHash in LogLog space — the space-efficient sketch family relevant when memory is the constraint | arXiv 1710.08436, title re-verified 2026-10-12 | none |
| 6 | https://arxiv.org/abs/2109.03337 | C-MinHash: Rigorously Reducing K Permutations to Two — shows the two-permutation reduction and its accuracy trade-off | arXiv 2109.03337, title re-verified 2026-10-12 | none |
| 7 | https://arxiv.org/abs/2203.08975 | A Survey of Multi-Agent Deep Reinforcement Learning with Communication — used as a control confirming the arXiv API path returns real metadata | arXiv 2203.08975, title re-verified 2026-10-12 | no domain content; control only |
| 8 | https://arxiv.org/abs/2206.07682 | Emergent Abilities of Large Language Models — benchmark-eval context for why decontamination matters | arXiv 2206.07682, title re-verified 2026-10-12 | none |
| 9 | https://arxiv.org/abs/2309.00986 | ModelScope-Agent: Building Your Customizable Agent System with Open-source Large Language Models — agent-system context | arXiv 2309.00986, title re-verified 2026-10-12 | none |
| 10 | https://github.com/hendrycks/test | MMLU repo (default branch `master`, verified live): the benchmark source. The n=13 window is NOT in this repo -- it comes from the MMLU paper (arXiv 2009.03300) and community decontamination practice; the repo is cited here as the benchmark source, not as the n-gram source | re-fetched 2026-10-13 (HTTP 200); re-verified 2026-10-14 (HTTP 200) | none |
| 11 | https://raw.githubusercontent.com/openai/gpt-2/master/src/encoder.py | GPT-2 pre-tokenizer regex (line 53): `"'s|'t|'re|'ve|'m|'ll|'d| ?\p{L}+| ?\p{N}+| ?[^\s\p{L}\p{N}]+|\s+(?!\S)|\s+"`. This is the regex `ngram_decontam._GPT2_PAT` is based on; re-verified byte-for-byte on 2026-10-12 | re-fetched 2026-10-13 (HTTP 200, 117 lines) | none |


## Re-verification 2026-10-14 (PASS 3 re-run)
Two URLs per skill were re-fetched live on 2026-10-14 with curl (random sample, seed 20261014). All 20 returned HTTP 200 except:
- `https://www.iso.org/standard/82833.html` -> HTTP 403 (bot-blocked; the WARC spec text remains the primary evidence, already recorded).
- `https://api.github.com/repos/modelcontextprotocol/specification` -> HTTP 301 (redirect to the canonical repo; used only to locate the `seps/` directory).
No new dead URLs, no fact drift between the 2026-10-13 and 2026-10-14 fetches.

## Version-sensitive facts
- **datasketch v2.0.0** changed the default MinHash permutation scheme to `affine32`.
  This fixes a similarity over-estimation bias on large sets but means hash values
  differ from earlier versions — persisted sketches and LSH indexes must be rebuilt,
  or pass `scheme="legacy"` to interoperate. Pin the scheme explicitly in config.
- The MinHash error bound is `1/sqrt(k)` for `k` permutations; datasketch's default
  `num=128` gives ~0.088 error. LSH banding uses `b` bands of `r` rows with the
  threshold `t ~= (1/b)^(1/r)`.
- n-gram decontamination window is benchmark-specific: n=13 for MMLU-style. Tokenization
  must match the benchmark's, or the comparison is meaningless.

## Conflicts
- Earlier rounds cited URLs that 404 on 2026-10-12 (`www.cs.cmu.edu/~dgc/papers/MinHash/MinHash.pdf`,
  `www.cs.princeton.edu/~chazelle/pubs/...`, `github.com/carpuat/leakage_report`,
  `github.com/IAAR-AI/decontamination-benchmarks`). These have been replaced with the
  arXiv-verified MinHash estimator papers and the live datasketch repo. The dead URLs are
  recorded here so the evidence chain is honest.
- No content conflicts among the surviving sources.

## Re-verification 2026-10-14 (PASS 4 / r3-03 close-out)
Live re-fetch of every version-sensitive primary URL for this skill with curl
(2026-10-14); arXiv titles were re-parsed from the live abstract pages:

| URL | HTTP | Fact re-confirmed |
|-----|------|-------------------|
| https://github.com/ekzhu/datasketch | 200 | canonical repo is `ekzhu/datasketch`; `datasketch/datasketch` still 404s |
| https://raw.githubusercontent.com/ekzhu/datasketch/master/README.rst | 200 | v2.0.0 note present verbatim: default permutation scheme changed to `affine32`, fixes similarity over-estimation bias on large sets (issue #212), halves sketch memory, ~4x faster updates |
| https://raw.githubusercontent.com/openai/gpt-2/master/src/encoder.py | 200 | pre-tokenizer regex at line 53 is byte-identical to `ngram_decontam._GPT2_PAT`: `'s|'t|'re|'ve|'m|'ll|'d| ?\p{L}+| ?\p{N}+| ?[^\s\p{L}\p{N}]+|\s+(?!\S)|\s+` |
| https://github.com/hendrycks/test | 200 | MMLU repo (default branch `master`) is the benchmark source; it contains no decontamination code, so the n=13 window comes from the paper + community practice, not this repo |
| https://arxiv.org/abs/1811.04633 | 200 | "A Review for Weighted MinHash Algorithms" |
| https://arxiv.org/abs/1407.4416 | 200 | "In Defense of MinHash Over SimHash" |
| https://arxiv.org/abs/1710.08436 | 200 | "HyperMinHash: MinHash in LogLog space" |
| https://arxiv.org/abs/2109.03337 | 200 | "C-MinHash: Rigorously Reducing $K$ Permutations to Two" |
| https://arxiv.org/abs/2206.07682 | 200 | "Emergent Abilities of Large Language Models" |
| https://arxiv.org/abs/2309.00986 | 200 | "ModelScope-Agent: Building Your Customizable Agent System with Open-source Large Language Models" |
| https://arxiv.org/abs/2009.03300 | 200 | "Measuring Massive Multitask Language Understanding" (MMLU paper; the source of the n=13 window) |

**No new dead URLs and no fact drift** between the 2026-10-13 and 2026-10-14
fetches. The MinHash/LSH threshold table in `references/DESIGN.md` was recomputed
from first principles this pass and matches the shipped table exactly
(k=128: b=32/r=4 -> 0.420, b=16/r=8 -> 0.707, b=8/r=16 -> 0.878, b=4/r=32 ->
0.958; k=256 b=8 r=32 -> 0.937; k=512 b=8 r=64 -> 0.968). 0.94 is not reachable
with k=128 — the closest is 0.878 — so targeting ~0.94 requires k=256.

## Re-verified 2026-10-12 (PASS 3 / TEST+FIX)
Two random sources re-fetched live to confirm nothing had moved:
- https://raw.githubusercontent.com/ekzhu/datasketch/master/README.rst — HTTP 200, 7,635 B; the v2.0.0 `affine32` note is still present verbatim.
- https://arxiv.org/abs/1811.04633 — HTTP 200, title "A Review for Weighted MinHash Algorithms" confirmed.
PyPI confirms Playwright 1.63.0 is still latest; arXiv 2009.03300 title "Measuring Massive Multitask Language Understanding" confirmed.
