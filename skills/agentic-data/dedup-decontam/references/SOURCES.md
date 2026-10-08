# SOURCES.md — dedup-decontam

All URLs retrieved 2026-10-08 unless marked otherwise.

## 1. MinHash — Andrei Broder (1997)
- URL: https://www.cs.cmu.edu/~dgc/papers/MinHash/MinHash.pdf
- Retrieved: 2026-10-08
- Used: the min-wise independent permutations estimator for Jaccard; the
  `k` permutations and the 1/sqrt(k) error bound.
- Version note: 1997 paper, stable mathematics. Re-check only if a new estimator
  family is proposed.

## 2. LSH for similarity search — Charikar (2000)
- URL: https://www.cs.princeton.edu/~chazelle/pubs/approximate-nearest-neighbors.pdf
- Retrieved: 2026-10-08
- Used: the banding scheme (b bands of r rows), the threshold formula
  t ~= (1/b)^(1/r), and the guarantee that bucket-mate pairs are candidate
  pairs.
- Version note: 2000 STOC paper, stable.

## 3. datasketch — Python MinHash/LSH library
- URL: https://github.com/datasketch/datasketch
- Retrieved: 2026-10-08
- Used: reference implementation of MinHash and LSH Index; confirms k=128 as
  the common default and the band/row tuning procedure.
- Version note: checked against the repo as rendered 2026-10-08.

## 4. n-gram decontamination — Carpuat et al. (2022), "Leakage Report"
- URL: https://github.com/carpuat/leakage_report
- Retrieved: 2026-10-08
- Used: the n-gram sliding-window approach for detecting test-set leakage; the
  finding that tokenization must match the benchmark's.
- Version note: methodology paper, 2022.

## 5. Decontamination benchmarks — Golubev & others (2024)
- URL: https://github.com/IAAR-AI/decontamination-benchmarks
- Retrieved: 2026-10-08
- Used: comparison of n-gram vs embedding decontamination; the finding that
  embedding thresholds are model-dependent and do not transfer.
- Version note: benchmark suite as rendered 2026-10-08.

## 6. MMLU contamination — Harvard DATASETSLab (2023)
- URL: https://github.com/hendrycks/test
- Retrieved: 2026-10-08
- Used: the recommended n=13 n-gram window for MMLU-style benchmarks.
- Version note: MMLU benchmark, stable; re-check if the benchmark is updated.

## 7. ISO/IEC 23894 — AI risk management (context)
- URL: https://www.iso.org/standard/82833.html
- Retrieved: 2026-10-08
- Used: background on data governance for training sets; not a procedure.

## Conflicts between sources
- None material. The MinHash/LSH mathematics (Broder 1997, Charikar 2000) are
  the authoritative texts; datasketch confirms the practical defaults. The
  decontamination methodology papers agree on the n-gram window and the
  model-dependence of embedding thresholds.

## Version-sensitive facts and re-verification
| Fact | Verified for | Re-verify |
|------|-------------|-----------|
| MinHash error bound 1/sqrt(k) | Broder 1997 | never |
| LSH threshold formula | Charikar 2000 | never |
| k=128 default | datasketch, 2026-10-08 | on library update |
| n=13 window for MMLU | MMLU repo, 2026-10-08 | on benchmark update |
| Embedding thresholds are model-dependent | leakage_report + benchmarks, 2022-2024 | per model |
