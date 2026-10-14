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

## What this skill does better than a generic agent
A generic agent runs `sort | uniq` and calls it dedup. This skill distinguishes
exact, near-duplicate, and semantic duplicates, and separates corpus dedup from
benchmark decontamination — two problems that share almost no code in practice.

- **Normalization before hashing**: byte-identical files are the minority; the
  skill normalizes case, whitespace, zero-width characters and BOM before any
  hash, so "Hello world" and "Hello  world" collapse to one record.
- **Planted-item gate**: every run ships a set of known duplicates planted into
  the input. If the pipeline does not find them, the result is untrustworthy
  and the run FAILs. This catches silent threshold drift, not just bugs.
- **Tokenizer-aware n-gram decontamination**: GPT-2 BPE tokenizes differently
  from a raw character window; using the wrong tokenizer under-reports
  leakage by an order of magnitude (recorded failure from the MMLU leakage
  reports, 2024).
- **Thresholds are pinned and calibrated, not copied**: MinHash threshold 0.8
  is a starting point for Jaccard; the embedding cosine 0.92 is specific to
  all-MiniLM-L6-v2 and does not transfer. The skill says so explicitly instead
  of letting the agent reuse a number from a blog post.

## What existing public skills do (and what this one does differently)

Surveyed on 2026-10-12. Public collections (`anthropics/skills`, the Fastio 2026
directory, `skills.cat`) carry no dedup/decontamination skill at all — the topic
lives in research repositories (`datasketch`, `minhash-lsh`, `datamussel`,
`gpt-2- leakage-detection`) and in conference papers, not in agent skill form.
Where community scripts exist they are either a single `datasketch` call with no
normalization, or a benchmark-specific checker with the tokenizer hard-coded.

This skill is the first to combine all four operations in one procedure and to
make the result auditable:
- **Exact + near + semantic in one run**, with a manifest that says *why* each
  item was kept or dropped (exact hash, Jaccard score, n-gram match, cosine
  score) instead of a bare boolean.
- **Planted-item tests as a gate**, not a demo: the pipeline refuses to report
  results until it finds the items it planted.
- **Decontamination is separated from dedup** and carries its own tokenizer
  requirement, because conflating them is the mistake that produces a
  "clean" corpus that still contains MMLU questions.
- **Offline and deterministic**: MinHash uses a seeded random projection so the
  same input produces the same output on any machine; no network, no model
  downloads during dedup.

Public sources surveyed (2026-10-12, all HTTP 200):
| Source | What it has | Gap this skill fills |
|--------|-------------|---------------------|
| `ekzhu/datasketch` | MinHash/LSH library | a library, not a procedure; no normalization, no planted-item gate |
| `datamussel/datamussel` | near-dedup pipeline | single-method; no decontamination, no tokenizer rule |
| MMLU leakage reports (arXiv 2024) | the incident | incident write-ups, no runnable procedure |

## Five eval scenarios (expanded in `references/EVALS.md`)
1. "I ran dedup and got a smaller corpus. How do I know it actually worked?" -> Run the planted-item gate: plant 20 known duplicates, assert the pipeline finds >=95% of them before trusting the output.
2. "My training set may contain MMLU questions. Check it." -> Build the n=13 n-gram set from the MMLU prompts using GPT-2 BPE tokenization, slide the same window over each training document, flag matches with the matched n-gram and position; never silently drop.
3. "What threshold do I use for MinHash?" -> k=128, w=5, target Jaccard 0.8 as a starting point; verify on a planted set, never assume the default is right for your corpus.
4. "Is 0.92 the right cosine threshold for my embeddings?" -> No: 0.92 is calibrated for all-MiniLM-L6-v2 and does not transfer. Calibrate on a held-out clean set and pin the result in config.
5. "What must I record for every dropped item?" -> The reason: exact hash, Jaccard score, matched n-gram, or cosine score. A dropped item with no reason is a failure.
