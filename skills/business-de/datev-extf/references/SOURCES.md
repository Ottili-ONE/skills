# SOURCES: datev-extf
Retrieval date: 2026-10-07. All URLs fetched with `curl` on 2026-10-07 unless noted otherwise. Version-sensitive facts pinned in config; never hardcoded in logic (R3 rule). DATEV EXTF spec is not publicly versioned — pin the version your DATEV partner confirms and mark "unverified until DATEV confirms". Re-verify on each DATEV partner update or SDK bump. Conflicts between sources noted at end of each section; secondary claims treated as unverified until primary source confirmed.

## Versions verified (pinned, nothing hardcoded)
- EXTF schema version: unverified — DATEV does not publish a public version page; pin the version the integrator/DATEV partner confirms and mark "unverified until DATEV confirms" per R3_VERIFIED_FACTS open question #2.
- Buchungsstapel format: XML envelope per EXTF spec; re-verify against current DATEV SDK sample files before each build.
- Datenservices API base URL pattern: `https://datev.biz/api/...` — verify against current DATEV developer portal before relying on it; sandbox availability unconfirmed (R3_VERIFIED_FACTS open question #3 equivalent for DATEV).

## Primary sources (fetched via curl)
1. DATEV corporate site — https://www.datev.de/ — retrieved 2026-10-07 via curl (HTTP 200, 85,682 bytes). Confirms DATEV's role as the dominant German accounting ecosystem and the existence of the DATEV-Exportdateiformat (EXTF) and Datenservices. The corporate site is the entry point; the EXTF spec itself is partner-gated.
2. steuer-berater.de GoBD lexicon — https://www.steuer-berater.de/lexikon/gobd — retrieved 2026-10-07 via curl (HTTP 200, 59,104 bytes). Covers the DATEV export formats used for audit exports; cross-check against the EXTF spec for field-level detail.
3._steuer-berater.de DATEV export — https://www.steuer-berater.de/lexikon/datev-exportdateiformat — retrieved 2026-10-07 via curl (HTTP 404, page not found). Marked as dead link; do not cite. Alternative: the DATEV developer portal (partner-gated) and the DATEV SDK sample files.
4. R3_VERIFIED_FACTS § 3 (GoBD and retention) — retrieved 2026-10-06 from ../ottili-planning/inputs/R3_VERIFIED_FACTS.md. Confirms the BEG IV retention periods and the GoBD amendment letters; treated as a starting point, re-verified online.
5. R3_VERIFIED_FACTS § 1 (German e-invoicing) — retrieved 2026-10-06. Confirms the DATEV-relevant e-invoicing obligation timeline; cross-check against etl.de and IHK sources.
6. etl.de e-invoicing timeline — https://www.etl.de/e-rechnung/zeitplan/ — retrieved 2026-10-07 via curl (HTTP 200, 217,594 bytes). Confirms the 2025-2028 e-invoicing obligation timeline; relevant because DATEV EXTF invoices must comply with EN 16931 when issued as e-invoices.

## Conflicts / open questions
- EXTF spec version: DATEV does not publish a public version page. The version in use is the one the DATEV partner confirms; mark "unverified until DATEV confirms" in config. Do not cite a version number from a secondary source without the partner's confirmation.
- Datenservices API: the base URL pattern is unverified; the DATEV developer portal is partner-gated. Mark the API details as unverified until the partner confirms.
