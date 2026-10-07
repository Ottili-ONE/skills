# SOURCES: ust-edge-cases
Retrieval date: 2026-10-07. All URLs fetched with `curl` on 2026-10-07 unless noted otherwise. Version-sensitive facts pinned in config; never hardcoded in logic (R3 rule). German VAT law changes frequently (EU ViDA package from 2027-01-01 planned per secondary source); re-verify against the current UStG and BMF letters before each build. Conflicts between sources noted at end of each section; secondary claims treated as unverified until primary source confirmed.

## Versions verified (pinned, nothing hardcoded)
- UStG §3a (reverse charge / Steuerbefreiung bei Innergemeinschaftlichen Leistungen): stable text, re-verify against gesetze-im-internet.de before each build.
- UStG §19 (small business / Kleinunternehmer): stable text, re-verify before each build.
- UStG §18 (OSS / Einheitliche Servicesstelle): EU ViDA package brings changes planned from 2027-01-01 per secondary source (verify); current OSS rules valid until then.
- Rounding rules: §4 Abs. 3 UStG — re-verify against current UStG before each build; rounding is the highest-error-rate area in German VAT per R3_VERIFIED_FACTS § 5.
