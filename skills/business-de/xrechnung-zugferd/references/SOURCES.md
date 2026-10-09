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
| 12b | FNFE-MPE Factur-X page | http://fnfe-mpe.org/factur-x/ | **Factur-X 1.09.2 / ZUGFeRD 2.5.2** | **Re-fetched 2026-10-09 (HTTP 200, 238 KB).** The page now advertises 1.09.2/2.5.2 (meta title + description), confirming the earlier bump note. `config/versions.json` is now pinned at **1.09.2** (bumped 2026-10-09 to match the live spec). |
| 13 | EN 16931-1 CEN (re-check) | https://www.cen.eu/standards/EN/16931 | v1.2.4 | Re-fetched 2026-10-09: page returns no version string in HTML (paywall). Version pin retained from the 2026-10-08 corroboration. |

## Conflicts / version-sensitive notes

- **Factur-X version bump (2026-10-09):** the FNFE-MPE page advertises **Factur-X 1.09.2 / ZUGFeRD 2.5.2**. `config/versions.json` is bumped to **1.09.2** on 2026-10-09; the akretion/factur-x *library* tag remains dynamic and is pinned separately as unverified. Re-fetch before any audit.
- The akretion/factur-x library version is dynamic (hatch-vcs) and not published in a
  stable tag. Treat the library version as **unverified**; the *spec* version (1.09.2) is pinned in `config/versions.json`
  instead.
- The KoSIT validator has no public version page; the tag `v2026-08-31` is the closest
  available pin. Re-verify against the repo's release page before any audit.
- EN 16931-1 is paywalled; the profile model is corroborated by the akretion README and
  the FeRD website. Re-verify if a CEN corrigendum lands.

## Re-check 2026-10-09 (task skills-business-de-r3-05)

Every version-sensitive URL in `config/versions.json` was re-fetched with
`curl` on 2026-10-09 (User-Agent `OttiliResearchBot/1.0`, follow redirects,
45 s timeout). Results:

| URL | HTTP | Interpretation |
|---|---|---|
| https://www.gesetze-im-internet.de/ao/ | 404 | The bare AO index path no longer resolves (site layout changed). The BEG IV / AO §147 retention classes remain corroborated by steuer-berater.de, whk-controlling.de and the dejure.org mirror. **Re-fetch before an audit.** |
| https://www.gesetze-im-internet.de/uStg/ | 404 | Same — the bare UStG path no longer resolves. UStG §12/§19/§3g/§4/§18 rates and thresholds are corroborated by the IHK pages in this file and by de.wikipedia.org/wiki/Umsatzsteuergesetz (200 OK). **Re-fetch before an audit.** |
| https://www.gesetze-im-internet.de/beg/ | 200 | BEG page resolves; confirms the BEG IV effective date. |
| https://www.iso20022.org/iso20022/message-definitons | 403 | Access-restricted (bot block). camt.053.001.08 is corroborated by de.wikipedia.org/wiki/Camt-Format (200 OK). |
| https://www.swift.com/standards | 403 | Access-restricted. MT940 status corroborated by de.wikipedia and en.wikipedia. |
| https://www.steuer-berater.de/lexikon/ao-147/ | 404 | The AO §147 lexikon entry moved; the lexikon root (https://www.steuer-berater.de/lexikon/) resolves (200). The 8/10/6 split is corroborated by whk-controlling.de (200) and dejure.org. |
| https://www.bundesbank.de/ | 200 | Root resolves; the specific IBAN page moved (404). |
| https://www.datev.de/ | 200 | Resolves; the EXTF spec is gated behind partner registration. |
| https://github.com/seamless-engineering/datev-extf | 200 | Repo and raw README resolve; EXTF_AS_OF 2026-09-25 confirmed. |
| https://github.com/akretion/factur-x | 200 | Repo resolves (raw README 404 — path is `main`, not `master`). |
| https://github.com/itplr-kosit/validator-configuration-xrechnung | 200 | Repo and tags resolve; the `guidelines.json` mapping remains unverified from source (see xrechnung-zugferd SOURCES). |
| https://de.wikipedia.org/wiki/Camt-Format | 200 | Confirms camt.053.001.08 as the current version. |
| https://de.wikipedia.org/wiki/Internationale_Bankkontonummer | 200 | German IBAN check-digit algorithm corroborated. |
| https://de.wikipedia.org/wiki/Umsatzsteuergesetz | 200 | UStG rates and thresholds corroborated. |

**Net effect on pinned versions:** none changed. Every version in
`config/versions.json` is still current as of 2026-10-09. The two statute
portals (gesetze-im-internet.de AO and UStG) are the weak links — mark them
"re-fetch before audit" rather than trusting the corroboration.
