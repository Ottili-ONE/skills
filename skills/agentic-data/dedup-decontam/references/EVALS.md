# EVALS — dedup-decontam

Each eval is a realistic prompt an agent might receive, the expected behaviour
per this skill, and failure signs to look for.

## E1 — remove duplicates from a web-scraped corpus
Prompt: "I scraped 50,000 forum posts into a folder. Remove exact and near
duplicates before training."
Expected: normalize every document (lowercase, collapse whitespace, strip
zero-width chars), SHA-256 exact dedup first, then MinHash/LSH with k=128,
w=5, target threshold 0.8, candidate pairs compared with exact Jaccard. Emit a
JSON manifest with action kept/dropped/flagged and a reason per item.
Failure signs: unseeded MinHash (non-reproducible); k < 64; no normalization
step so case/whitespace variants survive as "unique"; dropped items with no
reason in the manifest.

## E2 — detect MMLU test leakage in the training set
Prompt: "My training set may contain MMLU questions. Check it."
Expected: build the n=13 n-gram set from the MMLU prompts (tokenized the same
way MMLU is tokenized — GPT-2 BPE, not raw chars), slide the same window over
each training document, flag any document sharing an n-gram. Do not silently
drop; record the matched n-gram and position.
Failure signs: raw character n-grams used on BPE-tokenized benchmark (misses
matches, over-reports); documents dropped without a flag; no note about the
tokenization match.

## E3 — tune the embedding decontamination threshold
Prompt: "Flag training documents that are too similar to my eval prompts
using sentence-transformers/all-MiniLM-L6-v2."
Expected: embed corpus and prompts with the *same* model, compute cosine
similarity, flag pairs above the pinned threshold. Note that 0.92 is calibrated
for all-MiniLM-L6-v2 and **does not transfer** to another model; calibrate on a
held-out clean set before applying. Never hardcode the threshold in logic —
pass it in.
Failure signs: threshold copied from another model's blog post; no calibration
step; threshold baked into the script.

## E4 — verify the detector is not broken (planted items)
Prompt: "How do I know my dedup pipeline actually works?"
Expected: run `scripts/plant_test.py --out <dir>` which plants 5 exact
duplicates and 5 near-duplicates (Jaccard ~0.85) into a synthetic corpus and
runs the detectors. Acceptance: 5/5 exact found and >=4/5 near found. If it
fails, the detector is broken — fix before trusting any real result.
Failure signs: no planted-item test in the pipeline; test skipped or
weakened; test passing while real duplicates are missed.

## E5 — corpus with no duplicates should report zero
Prompt: "Dedup a corpus of 100 distinct documents."
Expected: exact dedup reports 0 duplicates; MinHash/LSH reports 0 candidate
pairs (or pairs below threshold); n-gram decontam reports 0 leaks; the manifest
marks everything `kept` with reason `clean`. Exit code 0.
Failure signs: false positives on distinct documents (normalization bug,
shingle width too small, threshold too low); non-zero exit on a clean corpus.

## E6 — hostile input: zero-width chars and BOM
Prompt: "Some files have \\ufeff BOMs, \\u200b zero-width spaces, and \\r\\n line
endings. Dedup them."
Expected: the normalizer strips BOM, zero-width chars (U+200B, U+200C,
U+200D), control chars except \n and \t, removes \r, lowercases, and collapses
whitespace. Two documents that differ only in those characters must hash to
the same SHA-256 and be treated as exact duplicates.
Failure signs: BOM/zero-width variants counted as distinct documents; the
normalizer is applied after hashing instead of before.

## E7 — embedding decontamination with a pinned threshold
Prompt: "Flag training documents that are too similar to my eval prompts using
sentence-transformers/all-MiniLM-L6-v2."
Expected: embed corpus and prompts with the *same* model, compute cosine
similarity, flag pairs above the pinned threshold. Note that 0.92 is calibrated
for all-MiniLM-L6-v2 and **does not transfer** to another model; calibrate on a
held-out clean set before applying. Never hardcode the threshold in logic — pass
it in via `--threshold`. `scripts/embed_decontam.py` runs offline on precomputed
embeddings (JSON or numpy).
Failure signs: threshold copied from another model's blog post; no calibration
step; threshold baked into the script.

## E8 — embedding decontam is clean when vectors are orthogonal
Prompt: "My corpus and prompts are unrelated; the embedding detector must not
false-positive."
Expected: with orthogonal or dissimilar vectors, `embed_decontam.py` reports
`flagged=0` and exits 0. A threshold of 0.92 must not flag cosine 0.0.
Failure signs: false positives on unrelated documents (normalization bug,
threshold too low, dimension mismatch).

## E9 — embedding detector rejects an out-of-range threshold
Prompt: "Run the embedding detector with --threshold 1.5."
Expected: the script exits 1 with a FAIL about the threshold being outside
[-1, 1); it does not silently clamp or proceed.
Failure signs: threshold silently clamped; no validation.
