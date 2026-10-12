# DESIGN: dedup-decontam

## Trigger description (SKILL.md description draft, <=1024 chars)
"Deduplicate and decontaminate text corpora for LLM training: MinHash/LSH near-duplicate
detection, n-gram and embedding-based decontamination, planted-item tests with
pass/fail criteria. Use when preparing a training or evaluation dataset and you must
remove duplicates and test-set leakage; not for single-document similarity."

## Procedure outline
1. Normalize ONCE via `scripts/normalize.py` (the single function every comparison runs
   on): strip BOM/zero-width chars, drop `\r`, lowercase (skip for code), collapse
   whitespace, canonicalize URLs, SHA-256 the bytes for exact dedup.
2. MinHash/LSH near-dedup: char-level shingles of size w (5 prose, 8 code); k=128
   min-hash values (never below 64); Jaccard ≈ matching/k with 95% interval ±12%.
   Band with b bands of r rows (k=b*r); threshold t ≈ (1/b)^(1/r). b=32,r=4 -> 0.67;
   b=16,r=8 -> 0.85; b=8,r=16 -> 0.94. Compare candidate pairs exactly and keep those
   above the target.
3. n-gram decontamination: build the test-prompt n-gram set (n=13 MMLU/GSM8K-style,
   n=8 code, n=5 prose) and slide the same window over the corpus. Tokenization must
   match the benchmark's (GPT-2 BPE vs raw char n-grams differ). Flag, do not silently
   drop; record the matched n-gram and position.
4. Embedding decontamination: embed with one model, cosine-similarity against prompts,
   flag above the pinned threshold (default 0.92 for all-MiniLM-L6-v2). Threshold is
   model-dependent and a CLI argument, never baked into logic. Calibrate on a held-out
   clean set.
5. Planted-item test before shipping: plant 5 exact duplicates and 5 near-duplicates
   (Jaccard ~0.85). Expected 5/5 exact found, >=4/5 near. If it fails, the detector is
   broken.

## Scripts planned
- `scripts/normalize.py`, `scripts/minhash_lsh.py`, `scripts/ngram_decontam.py`,
  `scripts/embed_decontam.py`, `scripts/plant_test.py`, `scripts/validate_skill.py`.

## Five eval prompts (mirrored in `references/EVALS.md`)
1. "I decontaminated using character n-grams but the benchmark uses GPT-2 BPE. Is my
   result valid?" -> No: tokenization mismatch misses matches and over-reports.
2. "My MinHash uses num_perm=8. What's wrong?" -> Unstable estimate, not reproducible;
   use k>=64, 128 default, with a fixed seed.
3. "I found a duplicate and silently removed it. Is that OK?" -> No: flag it, record the
   matched n-gram and position, and let a human decide.
4. "The embedding threshold is 0.92 for all-MiniLM-L6-v2. Can I use it with another
   model?" -> No: thresholds are model-dependent; re-tune on a held-out clean set.
5. "The planted-item test found 3 of 5 near-duplicates. What do I do?" -> The detector
   is broken; fix before trusting any real result.

## What this skill does better than a generic agent
A generic agent removes obvious duplicates and calls it done. This skill pins the
normalization contract, the MinHash/LSH math with its threshold table, the
tokenization-matching rule for n-gram decontamination, the model-dependent embedding
threshold, and a planted-item test with explicit pass/fail criteria. It prevents the
common incident of a "decontaminated" dataset that still leaks test-set n-grams
because the tokenization did not match the benchmark's.
