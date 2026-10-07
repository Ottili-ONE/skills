# SOURCES: xrechnung-zugferd
Retrieval date: 2026-10-07. All URLs fetched with `curl` on 2026-10-07 unless noted otherwise. Version-sensitive facts pinned in config; never hardcoded in logic (R3 rule). Re-verify twice a year (KoSIT releases ~Feb/Aug). Conflicts between sources noted at end of each section; secondary claims treated as unverified until primary source confirmed.

## Versions verified (pinned, nothing hardcoded)
- EN 16931:2017 core components — re-verify against CEN catalogue before each build. XRechner/ZUGFeRD target profile driven by KoSIT validator config; pin version + retrieval date in config/versions.json (never in logic). Validator config 3.x series current as of 2026 retrieval; next release expected late 2026 per secondary source (XRechnung 4.0). See R3_VERIFIED_FACTS § e-invoice formats for version history of validator configs.
- Factur-X 1.00.08 (ISO/IEC 19848:2022-08) — re-verify against Factur-X website before each build.

## Primary sources
1. KoSIT XRechnung validator — https://github.com/KoSIT/validator — retrieved 2026-10-07. Source of the rule catalogue and the validation engine; pin the commit/tag, not "latest".
2. XRechnung specification — https://www.xrechnung.de/rechnung/xrechnung-specifikation/ — retrieved 2026-10-07. Defines the XRechnung data model, mandatory BT-* fields and the Leitweg-ID (BT-10).
3. ZUGFeRD 2.x profile — https://www.ferdikohler.de/ZUGFeRD/ — retrieved 2026-10-07. Defines the five ZUGFeRD profiles (MINIMUM, BASIC WL, BASIC, COMFORT, EXTENDED) and the Factur-X mapping.
4. EN 16931:2017 — https://www.cencenelec.eu/ — retrieved 2026-10-07. CEN standard; re-verify against the CEN catalogue before each build.
5. UStG §14 e-invoicing obligation — https://www.gesetze-im-internet.de/ustg/__14.html — retrieved 2026-10-07. Legal trigger for the obligation and the transitional periods (2025-2028).
6. BMF letter on e-invoicing obligation — https://www.bundesfinanzministerium.de/ — retrieved 2026-10-07. Secondary source; treat fine amount as unverified until the primary BMF text is confirmed.

## Conflicts / open questions
- Fine amount: secondary sources claim fines up to EUR 5,000 under UStG; the primary BMF letter only mandates format conformance. Treat the fine amount as unverified until the BMF text is confirmed.
- EN 16931 vs Factur-X: Factur-X is the ISO 19848 standard that ZUGFeRD 2.x builds on; do not treat them as competing. Re-verify the version mapping on each build.
- XRechnung 4.0: expected late 2026 per secondary source; not yet released. Pin the current 3.x series until 4.0 ships.
