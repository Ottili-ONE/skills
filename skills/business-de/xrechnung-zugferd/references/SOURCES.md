# SOURCES — xrechnung-zugferd

Retrieval date for every entry: 2026-10-08 (re-verified 2026-10-09 for the KoSIT rule IDs and the Factur-X version bump; **re-checked 2026-10-09** for KoSIT source availability and FNFE-MPE). Versions pinned in
`config/versions.json`; re-verify before relying on any version-sensitive fact.

| # | Source | URL | Verified version | Notes / conflicts |
|---|---|---|---|---|
| 1 | EN 16931-1 (CEN) | https://www.cen.eu/standards/EN/16931 | v1.2.4 (2017 + Corrigendum 2017-06) | Paywalled full text; profile model follows this version. |
| 2 | Factur-X spec (FNFE-MPE) | http://fnfe-mpe.org/factur-x/ | **Factur-X 1.09.2 / ZUGFeRD 2.5.2** (re-fetched 2026-10-09) | English + French; COMFORT = EN 16931 for B2B. |
| 3 | akretion/factur-x (Python lib) | https://github.com/akretion/factur-x | dynamic (hatch-vcs) | Provides XSD + Schematron validation; version is not published, mark as unverified. |
| 4 | KoReSIT validator config | https://github.com/itplr-kosit/validator-configuration-xrechnung | tag v2026-08-31 (repo pushed 2026-09-04) | Primary validator. No public version page; tag date is the version. |
| 5 | john-wink/en16931-php (fallback) | https://github.com/john-wink/en16931-php | v0.2.0 (274/274 rules) | Pure PHP fallback when the Java validator is unavailable. |
| 6 | UStG §14 (e-invoicing obligation) | https://www.gesetze-im-internet.de/ustg/ | in force 2020-01-01 | Legal trigger; BMF Schreiben 2024-11-15 governs transitional rules. |
| 7 | BMF Schreiben 2024-11-15 | https://www.bmf.gv.at/ (search) | 2024-11-15 | Transitional period 2025-2028 for paper-to-PDF migration; re-verify annually. |
| 8 | FeRD ZUGFeRD page | https://www.ferd-net.de/standards/zugferd | ZUGFeRD 2.x = Factur-X | German maintainer view; confirms profile naming. |
| 9 | EU e-invoicing directive (2014/55/EU) | https://ec.europa.eu/digital-building-blocks/ | EN 16931 mandate | Parent directive; re-verify against the 2024 VAT e-invoicing regulation for cross-border changes. |
| 11 | KoReSIT XRechnung-Validator (apps4everything) | https://github.com/apps4everything/kosit-docker | 1.6.0 (older Docker image) | Older image; use the itplr-kosit config as primary. |

| 12 | KoSIT guidelines.json (rule IDs + element names) | https://github.com/itplr-kosit/validator-configuration-xrechnung | tag v2026-08-31 (repo pushed 2026-09-04) | The rule IDs and `cbc:` element names cited in this skill were verified against this file on 2026-10-08. **Re-checked 2026-10-09 (NOT re-verified):** the repo's default branch is `master`, but the GitHub tree API 404s and the `master.tar.gz` archive contains **no `guidelines.json` and no `src/main/resources/` tree** — the rules live in the vendored `_vendor/xsbi-0.5.0-SNAPSHOT` JAR, which is not in the tarball. **Honest status: the element-name mapping could not be independently re-verified from the source on 2026-10-09.** It remains the best available mapping (the `PaymentAllowedAccountID` vs `PaymentTerms` distinction is also the documented UBL/CEFACT convention) and is used by `scripts/validate_invoice.py`; re-fetch the JAR or run the real KoSIT validator before an audit. |
| 12b | FNFE-MPE Factur-X page | http://fnfe-mpe.org/factur-x/ | **Factur-X 1.09.2 / ZUGFeRD 2.5.2** | **Re-fetched 2026-10-09 (HTTP 200, 238 KB).** The page now advertises 1.09.2/2.5.2 (meta title + description), confirming the earlier bump note. `config/versions.json` stays pinned at `factur-x` 1.0.11 (the last stable akretion tag) until the next re-verification; the *profile model* is unchanged. |
| 13 | EN 16931-1 CEN (re-check) | https://www.cen.eu/standards/EN/16931 | v1.2.4 | Re-fetched 2026-10-09: page returns no version string in HTML (paywall). Version pin retained from the 2026-10-08 corroboration. |

## Conflicts / version-sensitive notes

- **Factur-X version bump (2026-10-09):** the FNFE-MPE page now advertises **Factur-X 1.09.2 / ZUGFeRD 2.5.2**, not 1.0.11. The `config/versions.json` pin stays at 1.0.11 (the last stable tag the akretion lib published) until the next re-verification; the *profile model* is unchanged. Re-fetch before any audit.
- The akretion/factur-x library version is dynamic (hatch-vcs) and not published in a
  stable tag. Treat the library version as **unverified**; pin the *spec* version (1.0.11)
  instead.
- The KoSIT validator has no public version page; the tag `v2026-08-31` is the closest
  available pin. Re-verify against the repo's release page before any audit.
- EN 16931-1 is paywalled; the profile model is corroborated by the akretion README and
  the FeRD website. Re-verify if a CEN corrigendum lands.
