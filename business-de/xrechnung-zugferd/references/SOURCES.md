# Sources — xrechnung-zugferd

Retrieval date: **2026-10-13** (this pass). Earlier entries retained below.

## Re-fetched / new on 2026-10-13

| # | URL | Status | Fact recorded | Verified version |
|---|-----|--------|---------------|------------------|
| S1 | https://github.com/itplr-kosit/validator-configuration-xrechnung/blob/master/CHANGELOG.md | **503** (re-probed 2026-10-13 — was 200 earlier this day; the URL is now unreliable. Facts retained but re-fetch from the raw GitHub URL before an audit.) | **2026-08-31 release is compatible with XRechnung 3.0**, uses CEN Schematron Rules **1.3.16** and KoSIT Validator **v1.6.3**. Added custom level "error" for `CII-SR-465`/`CII-SR-466`; custom "information" for `CII-SR-475`/`CII-SR-476` (wrong rule context in CEN Schematron 1.3.16, replaced by BR-TMP-4/5). Dummy IBANs in test files. A document that could not be processed is now assessed as "sollte nicht automatisiert angenommen werden" rather than "zurückzuweisen". | tag `v2026-08-31`, KoSIT Validator v1.6.3, CEN Schematron 1.3.16 |
| S2 | https://github.com/itplr-kosit/validator-configuration-xrechnung/tags | 200 | Release tags: `v2026-08-31`, `v2026-01-31`, `release-2025-07-10`, `release-2025-03-21`, `release-2024-10-31`, `release-2024-06-20`, `release-2023-11-15`, `release-2023-09-22`. Default branch is `master`. | 2026-10-13 |
| S3 | https://www.ferd-net.de | 200 | FERD publishes the ZUGFeRD / Factur-X specification and profile model. Primary source for the profile set (MINIMUM, BASIC WL, BASIC, COMFORT, EXTENDED). | re-fetched 2026-10-13 |
| S4 | https://agentskills.io/specification | 200 | Agent Skills open standard: folder + SKILL.md with YAML front matter (name, description required; license, compatibility, metadata, allowed-tools optional); progressive disclosure; description <= 1024 chars; SKILL.md < 500 lines, body < ~5000 tokens. | re-fetched 2026-10-13 |

**Conflict noted:** RESEARCH.md and R3_VERIFIED_FACTS.md cite a 2026-09-27 package page naming FacturX 1.09 / ZUGFeRD 2.5.2. The FERD spec page (S3) was not version-stamped on retrieval; the pinned versions in `config/versions.json` (Factur-X 1.0.11) remain the conservative choice until FERD publishes a dated changelog. **Re-verification note:** fetch the FERD changelog page before the next spec bump.

## Earlier sources (2026-10-08 pass)
| # | Source | URL | Verified version | Notes / conflicts |
|---|---|---|---|---|
| 1 | EN 16931-1 (CEN) | https://www.cen.eu/standards/EN/16931 | v1.2.4 (2017 + Corrigendum 2017-06) | Paywalled full text; profile model follows this version. |
| 2 | Factur-X spec (FNFE-MPE) | http://fnfe-mpe.org/factur-x/ | Factur-X 1.0.11 | English + French; COMFORT = EN 16931 for B2B. |
| 3 | akretion/factur-x (Python lib) | https://github.com/akretion/factur-x | dynamic (hatch-vcs) | Provides XSD + Schematron validation; version is not published, mark as unverified. |
| 5 | john-wink/en16931-php (fallback) | https://github.com/john-wink/en16931-php | v0.2.0 (274/274 rules) | Pure PHP fallback when the Java validator is unavailable. |
| 6 | UStG §14 (e-invoicing obligation) | https://www.gesetze-im-internet.de/ustg/ | in force 2020-01-01 | Legal trigger; BMF Schreiben 2024-11-15 governs transitional rules. |
| 7 | BMF Schreiben 2024-11-15 | https://www.bmf.gv.at/ (search) | 2024-11-15 | Transitional period 2025-2028 for paper-to-PDF migration; re-verify annually. |
| 8 | FeRD ZUGFeRD page | https://www.ferd-net.de/standards/zugferd | ZUGFeRD 2.x = Factur-X | German maintainer view; confirms profile naming. |
| 9 | EU e-invoicing directive (2014/55/EU) | https://ec.europa.eu/digital-building-blocks/ | EN 16931 mandate | Parent directive; re-verify against the 2024 VAT e-invoicing regulation for cross-border changes. |
| 10 | KoReSIT XRechnung-Validator (apps4everything) | https://github.com/apps4everything/kosit-docker | 1.6.0 (older Docker image) | Older image; use the itplr-kosit config as primary. |

## Conflicts / version-sensitive notes (2026-10-08 pass, retained)

- The akretion/factur-x library version is dynamic (hatch-vcs) and not published in a
  stable tag. Treat the library version as **unverified**; pin the *spec* version (1.0.11)
  instead.
- The KoSIT validator has no public version page; the tag `v2026-08-31` is the closest
  available pin. Re-verify against the repo's release page before any audit.
- EN 16931-1 is paywalled; the profile model is corroborated by the akretion README and
  the FeRD website. Re-verify if a CEN corrigendum lands.

## Re-verification 2026-10-13

All primary URLs re-probed with curl on 2026-10-13. Statuses recorded per row above. No fact changed as a result of the re-probe; the only material change is the KoSIT changelog URL (xrechnung-zugferd) returning 503.
