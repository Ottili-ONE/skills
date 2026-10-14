# STATUS — dedup-decontam — 2026-10-14

Scope: `skills/agentic-data/dedup-decontam/` (skill 6 of 10, agentic-data lane).
Task: `skills-agentic-data-r3-03` (build skills 4-6).

## Deliverables claimed in the task prompt
- `SKILL.md` — front matter name == folder, description <=1024 chars, body <500 L.
- `references/` — DESIGN, EVALS, SOURCES, procedures, planted-item-tests.
- `scripts/` — normalize.py, minhash_lsh.py, ngram_decontam.py, embed_decontam.py,
  plant_test.py, validate_skill.py.
- `tests/` — test_dedup_scripts.py, test_pipeline.py.
- `references/EVALS.md` — 12 prompts (>=5 required) with expected behaviour + failure signs.

## Verification run this pass (2026-10-14, PASS 4 / r3-03 close-out)
1. `python3 -m pytest skills/agentic-data/dedup-decontam/ -q` -> **24 passed**, 0 failed.
2. `python3 skills/agentic-data/scripts/acceptance_check.py` -> **ACCEPTANCE: PASS**;
   dedup rows: name == folder, description 329 chars, links resolve one level deep,
   SOURCES 13 URLs, DESIGN has trigger/procedure/scripts/evals, EVALS 12 prompts,
   SKILL.md 113 lines.
3. Per-skill validator: `scripts/validate_skill.py` -> **PASS: dedup-decontam validates
   against the Agent Skills standard**.
4. Script smoke (all six scripts, `--help`, exit 0): normalize, minhash_lsh,
   ngram_decontam, embed_decontam, plant_test, validate_skill.
5. Planted-item test run live this pass:
   `python3 scripts/plant_test.py --out /tmp/plant.json` ->
   `WARN: target 0.7 is not achievable with k=128; using b=16 r=8 -> actual
   threshold 0.7071` then **`PASS: planted-item test passed`** with
   `exact_found=5/5 near_found=5/5 pairs=10`. The detector finds every planted
   duplicate, so no real result may be treated as suspect on the strength of this
   skill alone.
6. Live re-fetch of version-sensitive primary URLs (curl, 2026-10-14) — see SOURCES.md
   "Re-verification 2026-10-14 (PASS 4 / r3-03 close-out)". All 11 returned HTTP 200;
   the GPT-2 pre-tokenizer regex was re-read byte-for-byte at line 53 and matches
   `ngram_decontam._GPT2_PAT` exactly; all seven arXiv titles were re-parsed and
   match the recorded ones; the datasketch v2.0.0 `affine32` note is present
   verbatim. The MinHash/LSH threshold table was recomputed from first principles
   and matches the shipped table exactly.

## What works
- One normalizer (`scripts/normalize.py`) for every comparison: BOM/zero-width strip,
  `\r` drop, lowercase unless code, whitespace collapse, URL canonicalization,
  SHA-256. Two components that normalize differently disagree invisibly, so the
  single function is a hard requirement, not a convention.
- MinHash/LSH: k=128 default, fixed seed, `bands_for()` warns when the requested
  threshold is unreachable for the chosen k (0.94 needs k=256; k=128 tops out at
  0.878). Thresholds are CLI parameters, never baked into logic.
- n-gram decontamination: default n=13 for common benchmarks, tokenization must
  match the benchmark (GPT-2 BPE regex baked in so it cannot drift); flags with
  position, never silently drops.
- Embedding decontamination: cosine similarity with a CLI threshold (0.92 default for
  all-MiniLM-L6-v2, wrong for any other model); `--threshold` out of range is
  rejected by the script.
- Planted-item gate: 5 exact + 5 near-duplicates must be found (5/5 exact, >=4/5
  near) before any result is trusted.

## What is stubbed / missing
None. All scripts run offline; all 24 tests pass; the validator finds 0 problems;
12 eval prompts with expected behaviour and failure signs are shipped.

## Acceptance verdict
**PASS.** The skill validates, scripts run offline, EVALS exist (12 prompts), the
SKILL.md body is 113 lines (<500), and every version-sensitive fact is marked with
the version and date it was verified (datasketch v2.0.0, GPT-2 regex, MMLU paper
2009.03300, 2026-10-14). No push, no history rewrite, no paths outside
`skills/agentic-data/dedup-decontam/**` touched this pass.
