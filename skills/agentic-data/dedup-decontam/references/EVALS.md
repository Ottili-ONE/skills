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
sentence-transformers/all-MiniLM-L6-v2 and a cosine threshold of 0.95."
Expected: embed corpus and prompts with the *same* model, compute cosine
similarity, flag pairs above the pinned threshold. Note that 0.92 is calibrated
for all-MiniLM-L6-v2 and **does not transfer** to another model; calibrate on a
held-out clean set before applying. Never hardcode the threshold in logic — pass
it in via `--threshold`. `scripts/embed_decontam.py` runs offline on precomputed
embeddings (JSON or numpy).
Failure signs: threshold copied from another model's blog post; no calibration

## E8 — the two-normalizer trap
Prompt: "Why does my exact-dedup report 0 duplicates while my n-gram decontam reports leaks on the same corpus?"
Expected: the answer is that the pipeline has two normalizers -- `normalize.py` for hashing and a private copy inside `ngram_decontam.py` -- and they can drift apart. The fix is a single source of truth: `ngram_decontam.normalize` must be `normalize.normalize`. Verify with `ngram_decontam.normalize is normalize.normalize`.
Failure signs: `ngram_decontam.normalize.__module__ == "ngram_decontam"` (a private copy still exists); the two functions disagree on BOM/zero-width/case input.

## E9 — `--tokenize bpe` for a real BPE tokenizer
Prompt: "My benchmark is tokenized with a real BPE tokenizer. Which `--tokenize` mode do I use?"
Expected: `--tokenize bpe` -- the caller feeds already-tokenized input (space-separated token strings) and the n-gram window runs over tokens. `--tokenize raw` splits on whitespace and is the fallback; `--tokenize gpt2` applies the GPT-2 pre-tokenizer regex. Using raw chars on BPE-tokenized data misses real leakage and over-reports false positives (pitfall P4).
Failure signs: `--tokenize raw` chosen for a BPE-tokenized benchmark; `--tokenize bpe` not listed in the choices.

## E10 — embedding decontam is clean when vectors are orthogonal
Prompt: "My corpus and prompts are unrelated; the embedding detector must not
false-positive."
Expected: with orthogonal or dissimilar vectors, `embed_decontam.py` reports
`flagged=0` and exits 0. A threshold of 0.92 must not flag cosine 0.0.
Failure signs: false positives on unrelated documents (normalization bug,
threshold too low, dimension mismatch).

## E11 — embedding detector rejects an out-of-range threshold
Prompt: "Run the embedding detector with --threshold 1.5."
Expected: the script exits 1 with a FAIL about the threshold being outside
[-1, 1); it does not silently clamp or proceed.
Failure signs: threshold silently clamped; no validation.


## E12 — LSH banding must match the achievable threshold, not the requested one
Prompt: "Tune LSH for k=128 to a 0.94 Jaccard threshold."
Expected: `bands_for(128, 0.94)` returns the closest achievable (b, r) and prints
a WARN that 0.94 is not reachable with k=128 (the nearest is b=4, r=32 ->
0.9576, verified 2026-10-14). The agent recognises that the *real* threshold is
0.9576, not 0.94, and either accepts it or raises k to 256/512. It never
silently claims 0.94. Note the direction: the achievable threshold is *higher*
than the target, so the detector is slightly more conservative, not permissive.
Failure signs: a table entry asserting (b=8, r=16) gives threshold ~0.94;
no WARN when the target is unreachable; the detector silently tuned to a
threshold the caller did not ask for.

## Near-miss prompts (trigger precision — these should NOT fire this skill)

## N1 — deduplicating a list of file paths
Prompt: "Remove duplicate paths from this list of 200 files."
Expected: No. That is exact-set deduplication — `set()` in Python. This skill is for *text corpora for LLM training*: MinHash/LSH near-dedup on shingles, n-gram decontamination against test prompts, embedding decontamination, planted-item tests. A list of paths has no shingles, no test leakage and no embeddings.
Failure signs: running `minhash_lsh.py` on a list of filenames; shingling a path string.

## N2 — checking if two documents are similar
Prompt: "Are these two contracts similar?"
Expected: No. That is single-pair similarity — TF-IDF, cosine, or a diff. This skill is for *corpora* (thousands of documents) and its pipeline is exact dedup -> MinHash/LSH near-dedup -> decontamination against a test set -> planted-item test. It is not a pairwise similarity tool, and running it on two documents would produce a report with no meaning.
Failure signs: feeding two documents into the full pipeline; expecting a similarity score from `minhash_lsh.py` (it returns bucket membership, not a score).

## N3 — cleaning a single CSV
Prompt: "Deduplicate the rows of this CSV."
Expected: No. That is a spreadsheet/data-frame operation — `df.drop_duplicates()`. This skill is for *text corpora* (plain text, tokenised into shingles) and its decontamination step requires test *prompts* to check against. A CSV has neither shingles nor prompts.
Failure signs: running the text normaliser on CSV rows; feeding prompts that are not natural-language test cases.
