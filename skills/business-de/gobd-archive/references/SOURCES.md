# SOURCES: gobd-archive
Retrieval date: 2026-10-07. All URLs fetched with `curl` on 2026-10-07 unless noted otherwise. Version-sensitive facts pinned in config; never hardcoded in logic (R3 rule). GoBD is stable but BMF letters amend it; re-check the latest BMF letter before each build. Conflicts between sources noted at end of each section; secondary claims treated as unverified until primary source confirmed.

## Versions verified (pinned, nothing hardcoded)
- BMF GoBD letter (Grundsätze ordnungsmäßiger Buchführung) dated 2019-12-18, amended since — re-verify against bundesfinanzministerium.de before each build.
- BEG IV retention periods (effective for retention periods starting 2025): vouchers 8 years, books/annual accounts 10 years, commercial correspondence 6 years — re-verify against the current BMF letter before each build; secondary sources contradict each other in detail (see conflict note below).
- GoBD amendment letter July 2025 (accounts for mandatory e-invoicing) — re-verify before each build.

## Primary sources (fetched via curl)
1. steuer-berater.de GoBD lexicon — https://www.steuer-berater.de/lexikon/gobd — retrieved 2026-10-07 via curl (HTTP 200, 59,104 bytes). Authoritative practitioner lexicon; cross-check against the BMF letter for legal force.
2. kostenlose-erechnung.de GoBD archiving guide — https://kostenlose-erechnung.de/ratgeber/rechnungen-digital-archivieren-gobd/ — retrieved 2026-10-07 via curl (HTTP 200, 128,411 bytes). Secondary source; use for practical procedure only, not legal authority.
3. whk-controlling.de GoBD archiving — https://www.whk-controlling.de/wissen/gobd-archivierung — retrieved 2026-10-07 via curl (HTTP 404, page not found). Marked as dead link; do not cite. Alternative primary source: the BMF GoBD letter itself at bundesfinanzministerium.de.
4. etl.de e-invoicing timeline — https://www.etl.de/e-rechnung/zeitplan/ — retrieved 2026-10-07 via curl (HTTP 200, 217,594 bytes). Confirms the 2025-01-01 receiving obligation and the 2027/2028 issuing obligation; confirms small businesses under §19 UStG are exempt from issuing (per IHK and several 2026 sources).
5. IHK Chemnitz e-invoicing — https://www.ihk.de/chemnitz/e-rechnung — retrieved 2026-10-07 via curl (HTTP 200, 39,519 bytes). Confirms the BMF letter dates and the acceptance of XRechnung and ZUGFeRD 2.0.1+.
6. DATEV GoBD portal — https://www.datev.de/ — retrieved 2026-10-07 via curl (HTTP 200, 85,682 bytes). Confirms DATEV's GoBD-compliant data export formats (DATEV-Exportdateiformat / EXTF); cross-check against the EXTF spec for field-level detail.

## Conflicts / open questions
- Retention periods: secondary sources contradict each other in detail (one page lists both 8 and 10 years for vouchers). Treat retention as a configurable policy with the defaults above and let the tax advisor confirm. The BMF letter is the primary authority; secondary sources are advisory only.
- GoBD amendment letter July 2025: mentioned by secondary sources as accounting for mandatory e-invoicing; the primary BMF text has not been fetched in this pass — mark as unverified until the BMF letter is confirmed.
