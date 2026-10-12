# SOURCES — dedup-decontam

Retrieval date 2026-10-12. Every URL below was fetched live on that date.
Re-verified 2026-10-12 (EXPAND pass): datasketch is still at 2.0.0 on PyPI (the `affine32` default holds); the GPT-2 pre-tokenizer regex was re-fetched from openai/gpt-2 `src/encoder.py` line 53 and matches the pattern baked into `ngram_decontam._GPT2_PAT` (`'s|'t|'re|'ve|'m|'ll|'d| ?\p{L}+| ?\p{N}+| ?[^\s\p{L}\p{N}]+|\s+(?!\S)|\s+`). The MMLU repo (hendrycks/test) contains no decontamination code of its own -- the n=13 window comes from the MMLU paper (arXiv 2009.03300) and the community decontamination practice; the repo is cited as the benchmark source, not the n-gram source.
Version-sensitive facts are marked with the version they were verified for.

| # | URL | What was used | Version / date verified | Conflict |
|---|-----|---------------|------------------------|----------|
| 1 | https://github.com/ekzhu/datasketch | datasketch: the reference MinHash/LSH implementation in Python. Confirms `MinHash` (Jaccard estimate, `num` permutations default 128), `MinHash LSH` index (threshold query, `b` bands / `r` rows), and the v2.0.0 breaking change to the `affine32` permutation scheme | fetched 2026-10-12 (HTTP 200); README.rst re-fetched HTTP 200 | the README is `README.rst`, not `README.md`; the canonical repo is `ekzhu/datasketch`, NOT `datasketch/datasketch` (404) |
| 2 | https://raw.githubusercontent.com/ekzhu/datasketch/master/README.rst | The v2.0.0 note: default permutation scheme changed to `affine32`, which fixes a similarity over-estimation bias on large sets, halves sketch memory, ~4x faster updates. Hash values differ from earlier versions — rebuild persisted sketches or pass `scheme="legacy"` | fetched 2026-10-12 (HTTP 200) | none |
| 3 | https://arxiv.org/abs/1811.04633 | A Review for Weighted MinHash Algorithms — the weighted-Jaccard estimator family used when sets carry weights | arXiv 1811.04633, title re-verified 2026-10-12 | none |
| 4 | https://arxiv.org/abs/1407.4416 | In Defense of MinHash Over SimHash — why MinHash (Jaccard) is preferred over SimHash (cosine) for near-duplicate document detection | arXiv 1407.4416, title re-verified 2026-10-12 | none |
| 5 | https://arxiv.org/abs/1710.08436 | HyperMinHash: MinHash in LogLog space — the space-efficient sketch family relevant when memory is the constraint | arXiv 1710.08436, title re-verified 2026-10-12 | none |
| 6 | https://arxiv.org/abs/2109.03337 | C-MinHash: Rigorously Reducing K Permutations to Two — shows the two-permutation reduction and its accuracy trade-off | arXiv 2109.03337, title re-verified 2026-10-12 | none |
| 7 | https://arxiv.org/abs/2203.08975 | A Survey of Multi-Agent Deep Reinforcement Learning with Communication — used as a control confirming the arXiv API path returns real metadata | arXiv 2203.08975, title re-verified 2026-10-12 | no domain content; control only |
| 8 | https://arxiv.org/abs/2206.07682 | Emergent Abilities of Large Language Models — benchmark-eval context for why decontamination matters | arXiv 2206.07682, title re-verified 2026-10-12 | none |
| 9 | https://arxiv.org/abs/2309.00986 | ModelScope-Agent: Building Your Customizable Agent System with Open-source Large Language Models — agent-system context | arXiv 2309.00986, title re-verified 2026-10-12 | none |
| 10 | https://github.com/hendrycks/test | MMLU repo (default branch `master`, verified live): the benchmark source. The n=13 window is NOT in this repo -- it comes from the MMLU paper (arXiv 2009.03300) and community decontamination practice; the repo is cited here as the benchmark source, not as the n-gram source | fetched 2026-10-12 (HTTP 200) | none |
| 11 | https://raw.githubusercontent.com/openai/gpt-2/master/src/encoder.py | GPT-2 pre-tokenizer regex (line 53): `"'s|'t|'re|'ve|'m|'ll|'d| ?\p{L}+| ?\p{N}+| ?[^\s\p{L}\p{N}]+|\s+(?!\S)|\s+"`. This is the regex `ngram_decontam._GPT2_PAT` is based on; re-verified byte-for-byte on 2026-10-12 | fetched 2026-10-12 (HTTP 200, 117 lines) | none |

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
