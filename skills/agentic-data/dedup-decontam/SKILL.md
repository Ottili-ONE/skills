---
name: dedup-decontam
description: "Deduplicate and decontaminate text corpora for LLM training: MinHash/LSH near-duplicate detection, n-gram and embedding-based decontamination, planted-item tests with pass/fail criteria. Use when preparing a training or evaluation dataset and you must remove duplicates and test-set leakage; not for single-document similarity."
compatibility: Python 3.10+, numpy optional; verified 2026-10-08
license: MIT
---
# Dedup and Decontamination

Trigger: prepare a text corpus for LLM training or evaluation and you must
remove duplicates and prevent test-set leakage.

## Procedure (numbered — follow in order)
1. **Normalize** — lowercase, collapse whitespace, strip BOM/zero-width chars,
   canonicalize URLs. Hash the normalized bytes for exact dedup first. One
   shared normalizer (`scripts/normalize.py`) for every comparison.
2. **Exact dedup** — keep the first occurrence of each SHA-256; log duplicates.
3. **Near-dedup with MinHash/LSH** — tokenize into shingles (default 5-gram),
   compute k=128 MinHash signatures, band into b bands of r rows, hash each band
   into buckets, compare only bucket-mates with Jaccard. Threshold ~0.8 by default.
4. **n-gram decontamination** — for each test prompt, slide an n-gram window
   (default 13 for common benchmarks) over the corpus; any exact n-gram match
   is leakage. Mark the document, do not silently drop.
5. **Embedding decontamination** — embed documents and test prompts with the same
   model, compute cosine similarity; flag pairs above the pinned threshold
   (default 0.92). Re-tune per model; never hardcode the threshold in logic.
6. **Planted-item tests** — before shipping, plant 5 known duplicates and 5
   near-duplicates; the pipeline must find 5/5 exact and >=4/5 near. If it fails,
   the detector is broken.
7. **Report** — emit a JSON manifest: kept/dropped/flagged counts, per-item
   reason, and the planted-item pass/fail.

## Decision tables
- **Jaccard threshold**: 0.95 -> near-identical; 0.8 -> loose; 0.5 -> LSH tuning.
- **LSH bands/rows**: k=128 -> (b=32, r=4) gives threshold ~0.67; (b=16, r=8)
  gives ~0.85; (b=8, r=16) gives ~0.94. Pick by the target threshold, not by speed.
  Override with `--bands`/`--rows` (must multiply to k).
- **n-gram size**: 13 for MMLU-style; 8 for code; 5 for prose.
- **Embedding threshold**: 0.92 cosine for all-MiniLM-L6-v2; lower = noisier,
  higher = misses. Model-dependent — calibrate on a held-out clean set.
- **Embedding action**: above threshold -> flag for review; never auto-drop.

## Near-miss triggers (stop and re-check before proceeding)
- Two documents that differ only in BOM/zero-width/case are reported as distinct
  -> the normalizer is applied after hashing instead of before; fix the pipeline order.
- k < 64 -> MinHash estimate is unstable; the planted-item test will fail.
- n-gram decontamination uses raw chars while the benchmark is BPE-tokenized ->
  you will miss real leakage and over-report false positives; match the tokenization.
- Planted-item test passes while real duplicates are missed -> LSH bands/rows are
  tuned wrong; re-run with explicit `--bands`/`--rows` for the target threshold.
- Embedding threshold copied from another model's blog post -> it does not transfer;
  calibrate on a held-out clean set for this model.

## Pitfalls from research
- P1: MinHash with too few permutations (k<16) gives unstable estimates; use >=64.
- P2: LSH banding with wrong b/r silently misses similarities below the threshold;
  always validate with planted items.
- P3: Normalization differences (whitespace, case) create false negatives; normalize
  before any comparison.
- P4: n-gram decontamination on raw text misses tokenized matches; decontaminate on
  the same tokenization the benchmark uses.
- P5: Dropping all flagged documents without review destroys corpus size; flag first,
  drop only confirmed leakage.
- P6: Embedding similarity is model-dependent; a threshold tuned on one embedding
  model does not transfer. Re-tune per model.

## Verification checklist
- [ ] Planted-item test passes: 5/5 exact, >=4/5 near.
- [ ] k >= 64, seed pinned and logged.
- [ ] Normalization is deterministic and documented.
- [ ] Every dropped item has a reason in the manifest.
- [ ] n-gram size matches the benchmark's tokenization.
- [ ] Embedding threshold is pinned per model, not hardcoded in logic.

## References
- procedures: references/procedures.md
- EVALS: references/EVALS.md
- SOURCES: references/SOURCES.md
- scripts: scripts/normalize.py, scripts/minhash_lsh.py, scripts/ngram_decontam.py, scripts/embed_decontam.py, scripts/plant_test.py, scripts/validate_skill.py
