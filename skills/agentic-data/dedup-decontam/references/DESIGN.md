# DESIGN: dedup-decontam

## Why this skill exists
A training corpus that is not deduplicated trains on itself; a corpus that is not
decontaminated trains on its evaluation set. Both failures are silent: the
metrics still look fine, and the damage only shows up months later when the
model fails on a held-out task it was effectively trained on. This skill turns
deduplication and decontamination into a repeatable pipeline with a
pass/fail gate.

## Trigger description (SKILL.md description draft, <=1024 chars)
"Deduplicate and decontaminate text corpora for LLM training: MinHash/LSH
near-duplicate detection, n-gram and embedding-based decontamination, planted-item
tests with pass/fail criteria. Use when preparing a training or evaluation dataset
and you must remove duplicates and test-set leakage; not for single-document
similarity."

## The three hard decisions

### 1. One normalizer, everywhere
Every comparison in the pipeline runs on the output of `scripts/normalize.py`.
Two documents that differ only in a BOM, a zero-width character, a `\r`, case or
whitespace collapse to the same SHA-256 and are exact duplicates. If two
components normalize differently, they will disagree about what is a duplicate —
and the disagreement is invisible because both report "clean". So the normalizer
is a single function, not a per-step convention.

### 2. Tokenization must match the benchmark
N-gram decontamination slides a window over the corpus and asks whether any
window appears in the benchmark's prompt set. The window is only meaningful if
the tokenization matches the benchmark's. GPT-2 BPE and raw character n-grams
produce different windows, so character n-grams against a BPE benchmark miss
matches and over-report. The GPT-2 BPE regex is baked into
`ngram_decontam._GPT2_PAT` so it cannot drift.

### 3. Thresholds are parameters, not constants
The embedding similarity threshold is model-dependent: 0.92 is correct for
all-MiniLM-L6-v2 and almost certainly wrong for any other model. It is a CLI
argument, calibrated on a held-out clean set, never baked into the logic.

## MinHash/LSH threshold table (verified by computation, 2026-10-13)
For k=128 min-hash values split into b bands of r rows (k = b*r), the LSH
threshold is `t ≈ (1/b)^(1/r)`:

| k | b | r | t |
|---|---|---|---|
| 128 | 32 | 4 | 0.420 |
| 128 | 16 | 8 | 0.707 |
| 128 | 8 | 16 | 0.878 |
| 128 | 4 | 32 | 0.958 |
| 256 | 8 | 32 | 0.937 |
| 512 | 8 | 64 | 0.968 |

**0.94 is not reachable with k=128** — the closest is 0.878. To target ~0.94
use k=256 (b=8, r=32 -> 0.937). `scripts/minhash_lsh.py:bands_for()` warns when
the target is unreachable for the chosen k.

## Scripts shipped
- `scripts/normalize.py` — the single normalizer (BOM/zero-width strip, `\r` drop,
  lowercase unless code, whitespace collapse, URL canonicalization, SHA-256).
- `scripts/minhash_lsh.py` — MinHash with a fixed seed, LSH banding, candidate
  comparison, and `bands_for()` threshold warnings.
- `scripts/ngram_decontam.py` — benchmark-matched tokenization, window slide,
  flag-with-position (never silently drop).
- `scripts/embed_decontam.py` — embedding cosine similarity with a CLI threshold.
- `scripts/plant_test.py` — plants 5 exact + 5 near-duplicates and reports the
  detection rate against the pass/fail criteria.
- `scripts/validate_skill.py` — standard compliance for the skill itself.

## Planted-item test (run before trusting any result)
Plant 5 exact duplicates and 5 near-duplicates (Jaccard ~0.85). Expected: 5/5
exact found, >=4/5 near found. A detector that finds 3/5 near-duplicates is
broken and no real result may be trusted until it is fixed.

## Near-miss triggers
- Two normalizations in the same pipeline -> duplicate sets disagree invisibly.
- Character n-grams against a BPE benchmark -> misses matches, over-reports.
- num_perm=8 -> unstable, non-reproducible estimate; use k>=64, 128 default.
- Silently dropping a flagged document -> the leak is gone but so is the audit trail.
- Baking the embedding threshold into logic -> wrong for a different model.
- Planted-item test not run -> the detector is unverified; treat every result as suspect.
