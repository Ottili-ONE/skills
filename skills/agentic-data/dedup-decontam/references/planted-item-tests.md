# Planted-item tests — dedup-decontam

A detector that has never been tested against known positives is not a detector.
This skill ships `scripts/plant_test.py` to run the test before any real corpus is
processed.

## The test (ordered)

1. **Build a fixture corpus** of 20-50 documents with realistic variety (news,
   code, prose, URLs, whitespace variants).
2. **Plant 5 exact duplicates** — byte-identical copies of 5 existing documents.
3. **Plant 5 near-duplicates** — 5 documents edited to Jaccard ≈ 0.85 on 5-gram
   shingles (a few sentences reordered, a paragraph paraphrased, a number changed).
4. **Run the pipeline** over the fixture corpus with the same settings you will use
   on the real corpus.
5. **Score**: exact-found / 5, near-found / 5 (near = Jaccard >= target threshold).
6. **Pass criteria**: 5/5 exact, >= 4/5 near. Fail the run if either is short.

## Thresholds

| Metric | Value | Note |
|--------|-------|------|
| Exact duplicates planted | 5 | fewer is not a test |
| Near-duplicates planted | 5 | target Jaccard 0.85 |
| Exact pass | 5/5 | anything less means the normalizer is bypassed somewhere |
| Near pass | >= 4/5 | 3/5 means LSH bands/rows are tuned wrong |
| k (MinHash perms) | >= 64 | below this the estimate is unstable and the test will flake |

## Decision table

| Observed | Diagnosis | Fix |
|----------|-----------|-----|
| 5/5 exact, 5/5 near | detector healthy | proceed |
| < 5/5 exact | normalization is applied after hashing, or hashing uses different input | fix pipeline order; re-run |
| 3-4/5 near | LSH threshold too high for the banding | lower the target or increase k (see procedures.md) |
| 0-2/5 near | b/r factorisation targets a much higher similarity | recompute `bands_for(target, k)` |
| Passes on fixture, misses on real | fixture is not representative | rebuild fixture from real corpus samples |

## Near-miss triggers

- Planting near-duplicates at Jaccard 0.99 tests nothing — the pipeline finds them
  trivially. Use 0.85.
- Planting near-duplicates at Jaccard 0.3 — the pipeline correctly ignores them,
  and you conclude the detector is broken. Use a value near your target threshold.
- Running the planted-item test **after** processing the real corpus — you have already
  shipped a broken detector. Run it before.
- Using the same random seed for planting and for the MinHash — the test is not
  independent. Seed the fixture from a different source.
