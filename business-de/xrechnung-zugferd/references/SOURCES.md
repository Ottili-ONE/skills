# Sources — xrechnung-zugferd

Retrieval date: **2026-10-13** (this pass). Earlier entries retained below.

## Re-fetched / new on 2026-10-13

| # | URL | Status | Fact recorded | Verified version |
|---|-----|--------|---------------|------------------|
| S1 | https://github.com/itplr-kosit/validator-configuration-xrechnung/blob/master/CHANGELOG.md | 200 | **2026-08-31 release is compatible with XRechnung 3.0**, uses CEN Schematron Rules **1.3.16** and KoSIT Validator **v1.6.3**. Added custom level "error" for `CII-SR-465`/`CII-SR-466`; custom "information" for `CII-SR-475`/`CII-SR-476` (wrong rule context in CEN Schematron 1.3.16, replaced by BR-TMP-4/5). Dummy IBANs in test files. A document that could not be processed is now assessed as "sollte nicht automatisiert angenommen werden" rather than "zurückzuweisen". | tag `v2026-08-31`, KoSIT Validator v1.6.3, CEN Schematron 1.3.16 |
| S2 | https://github.com/itplr-kosit/validator-configuration-xrechnung/tags | 200 | Release tags: `v2026-08-31`, `v2026-01-31`, `release-2025-07-10`, `release-2025-03-21`, `release-2024-10-31`, `release-2024-06-20`, `release-2023-11-15`, `release-2023-09-22`. Default branch is `master`. | 2026-10-13 |
| S3 | https://www.ferd-net.de | 200 | FERD publishes the ZUGFeRD / Factur-X specification and profile model. Primary source for the profile set (MINIMUM, BASIC WL, BASIC, COMFORT, EXTENDED). | re-fetched 2026-10-13 |
| S4 | https://agentskills.io/specification | 200 | Agent Skills open standard: folder + SKILL.md with YAML front matter (name, description required; license, compatibility, metadata, allowed-tools optional); progressive disclosure; description <= 1024 chars; SKILL.md < 500 lines, body < ~5000 tokens. | re-fetched 2026-10-13 |

**Conflict noted:** RESEARCH.md and R3_VERIFIED_FACTS.md cite a 2026-09-27 package page naming FacturX 1.09 / ZUGFeRD 2.5.2. The FERD spec page (S3) was not version-stamped on retrieval; the pinned versions in `config/versions.json` (Factur-X 1.0.11) remain the conservative choice until FERD publishes a dated changelog. **Re-verification note:** fetch the FERD changelog page before the next spec bump.

## Earlier sources (2026-10-08 pass)
