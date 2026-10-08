# Procedures — dedup-decontam

Verified 2026-10-08. Version-sensitive: MinHash/LSH math is stable (Broder 1997,
Charikar 2000); embedding thresholds are model-dependent and must be re-tuned.

## 0. Shared normalizer
`scripts/normalize.py` defines the ONE normalization function every comparison
runs on. Two documents that differ only in BOM, zero-width chars, `\r`, case, or
whitespace collapse to the same SHA-256 and are exact duplicates.
- Strip BOM (`\ufeff`), zero-width chars (`\u200b`, `\u200c`, `\u200d`).
- Drop `\r`; drop control chars except `\n` and `\t`.
- Lowercase (skip with `--no-lowercase` for code).
- Collapse runs of whitespace to a single space.
- Canonicalize URLs: lowercase scheme/host, drop default ports, sort query params.
- Hash the normalized bytes with SHA-256 for exact dedup.

## 1. Normalization (do this before every comparison)
1. Strip BOM, zero-width characters, and control chars except `\n` and `\t`.
2. Lowercase (for text corpora; skip for code).
3. Collapse runs of whitespace to a single space.
4. Canonicalize URLs: lowercase scheme/host, drop default ports, sort query params.
5. Hash the normalized bytes with SHA-256 for exact dedup.

## 2. MinHash/LSH near-dedup
- **Shingling**: tokenize into shingles of size `w` (default 5 for prose, 8 for code).
  Use char-level shingles; they are robust to minor edits.
- **MinHash**: for each document, compute `k` independent min-hash values. Each
  value is `min(h_i(token) for token in set)` over `k` hash functions. `k=128` is
  the common default; never below 64.
- **Estimator**: Jaccard ≈ (number of matching min-hash values) / k. Error bound
  is roughly 1/sqrt(k); with k=128 the 95% interval is ±12%.
- **LSH banding**: split the k values into `b` bands of `r` rows each (k = b*r).
  For each band, hash the r values into a bucket. Two documents are candidate
  pairs if they share any bucket. The threshold the scheme targets is
  `t ≈ (1/b)^(1/r)`.
  - b=32, r=4 -> t≈0.67
  - b=16, r=8 -> t≈0.85
  - b=8, r=16 -> t≈0.94
- **Candidate comparison**: for each bucket-mate pair, compute the exact Jaccard
  and keep pairs above the target threshold.

Good (documented, seeded):
```python
mh = MinHash(num_perm=128, seed=1)
for tok in shingles(doc):
    mh.update(tok.encode())
```
Bad (unseeded, too few perms):
```python
mh = MinHash(num_perm=8)  # unstable estimate, not reproducible
```

## 3. n-gram decontamination
- Build a set of all n-grams from the test prompts (n=13 for MMLU/GSM8K-style,
  n=8 for code, n=5 for prose).
- Slide the same window over each corpus document; any n-gram present in the
  test set is a hit.
- **Tokenization matters**: decontaminate on the *same* tokenization the
  benchmark uses. If the benchmark is tokenized with GPT-2 BPE, do not compare
  raw character n-grams — you will miss matches and over-report.
- Flag the document; do not silently drop. Record the matched n-gram and position.

## 4. Embedding decontamination
- Embed each document and each test prompt with the same model.
- Compute cosine similarity between document and prompt embeddings.
- Flag pairs above the pinned threshold (default 0.92 for sentence-transformers
  all-MiniLM-L6-v2; re-tune per model).
- Embedding similarity is **model-dependent**: a threshold tuned on one model
  does not transfer. Always calibrate on a held-out clean set.
- The threshold is a CLI argument, never baked into logic.

## 5. Planted-item test (run before shipping)
- Plant 5 exact duplicates (copy of an existing document) and 5 near-duplicates
  (Jaccard ~0.85 on shingles).
- Run the pipeline. Expected: 5/5 exact found, >=4/5 near found.
- If it fails, the detector is broken — fix before trusting any real result.

## 6. Reporting
Emit a JSON manifest per document:
```json
{"doc_id": "...", "action": "kept|dropped|flagged", "reason": "exact_duplicate|near_duplicate|ngram_leak|embedding_sim|clean", "detail": "..."}
```
