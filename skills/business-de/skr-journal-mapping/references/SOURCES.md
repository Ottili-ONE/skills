# SOURCES: skr-journal-mapping
Retrieval date: 2026-10-07. All URLs fetched with `curl` on 2026-10-07 unless noted otherwise. Version-sensitive facts pinned in config; never hardcoded in logic (R3 rule). SKR03 and SKR04 are stable standards but tax-key-to-account mappings change with tax law updates; re-verify against the current DATEV/IDR Kontenrahmen before each build. Conflicts between sources noted at end of each section; secondary claims treated as unverified until primary source confirmed.

## Versions verified (pinned, nothing hardcoded)
- SKR03 (Kontenrahmen für GmbH & Co. KG): stable standard, re-verify against DATEV publication before each build.
- SKR04 (Kontenrahmen für GmbH): stable standard, re-verify against DATEV publication before each build.
- UStG tax keys: 19% / 7% standard rates for 2026; re-verify against the current UStG before each build. Tax-key changes are the highest-error-rate area in German VAT (see ust-edge-cases SOURCES.md).
- Period locks (Monatsabschluss / Geschäftsjahrabschluss): governed by HGB and GoBD; re-verify against current BMF GoBD letter before each build.
