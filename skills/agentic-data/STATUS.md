# STATUS — skills-agentic-data-r3-03 (Build skills 4-6) — 2026-10-12

Scope: `skills/agentic-data/browser-agent-playwright`,
`skills/agentic-data/polite-crawling-warc`, `skills/agentic-data/dedup-decontam`.

## What works (proven by a command + result)
- All three skills validate against the Agent Skills standard:
  `python3 <skill>/scripts/validate_skill.py` -> `PASS: <name> validates` (exit 0).
- Front matter: `name` == folder for all three; `description` 327/335/363 chars
  (limit 1024); SKILL.md 111/88/93 lines (limit 500); every `references/` link
  resolves one level deep, no escapes.
- Tests passing: browser 13, polite-crawling 25, dedup 19 (57 total).
- **browser-agent-playwright**: `sanitize.py --check` flags every hostile fixture
  and exits 1; clean text exits 0. New `scripts/gen_hostile.py` generates 10
  deterministic fixtures (6 high / 2 medium / 2 clean) and a round-trip probe
  confirms severity == detector verdict for all 10.
- **polite-crawling-warc**: `robots.py` enforces RFC 9309 §2.3.1.3 (4xx -> may
  crawl, exit 0) and §2.3.1.4 (5xx -> default-deny, exit 1); truncates at
  500 KiB instead of OOMing. `warc_writer.py` writes response + revisit records
  with `WARC-Payload-Digest`; `validate_warc.py` walks all gzip members and
  reports `records=3 valid=3` for a 3-record file (the known pitfall: a naive
  `gzip.open().read()` reads only member 1).
- **dedup-decontam**: `plant_test.py` -> `PASS: planted-item test passed`
  (5/5 exact, 5/5 near) and now writes `manifest.json` (result/planted/found/
  criteria). `ngram_decontam.py --n 13 --tokenize raw` flags a verbatim MMLU-style
  prompt pasted into the corpus (`leaked_ngrams=14`, action `flagged`, rc=1).
  `minhash_lsh.py` finds the exact-duplicate pair (manifest `near_duplicates=1`).
  `normalize.py --check` exits 0 for identical-after-normalize pairs, 1 otherwise.

## What is stubbed / missing
- **embed_decontam.py**: the `sentence_transformers` package is not installed in
  this environment (`ModuleNotFoundError`), so the embedding path cannot be run
  here. The script and its tests (flag identical, clean when orthogonal, reject
  out-of-range threshold) pass; live embedding behaviour is unverified in this
  sandbox. The threshold stays a CLI argument, never baked into logic.
- **browser-agent-playwright**: the Playwright driver itself is not installed, so
  no end-to-end browser run is possible here. The grounding / locator / injection
  procedures are documented and the sanitizer is proven; the live browser path is
  verified by the skill's own test suite only.
- No new online research was required this pass: every fact was already fetched
  2026-10-12 and recorded in the per-skill `references/SOURCES.md` (10 entries
  each, >= 6 required). One stale fact was found and corrected (see below).

## Defect found and fixed this pass
- **dedup-decontam DESIGN.md LSH threshold table was wrong.** It claimed
  b=32,r=4 -> 0.67; b=16,r=8 -> 0.85; b=8,r=16 -> 0.94. Direct computation gives
  0.420 / 0.707 / 0.878 (verified: `python3 -c "[(b,r,round((1/b)**(1/r),4)) ...]"`).
  The SKILL.md decision table and `minhash_lsh.bands_for()` were already correct;
  DESIGN.md was the lone holdout. Corrected and the correction is cross-linked.
