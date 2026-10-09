# SOURCES: skr-journal-mapping
Retrieval date: 2026-10-09. All URLs fetched with curl on 2026-10-09 unless noted otherwise.
Version-sensitive facts pinned in `skills/business-de/config/versions.json`; never hardcoded in logic (R3 rule).
SKR03 and SKR04 are stable standards but tax-key-to-account mappings change with tax law updates;
re-verify against the current DATEV/IDR Kontenrahmen before each build. Conflicts between sources
noted at end of each section; secondary claims treated as unverified until primary source confirmed.

## Versions verified (pinned, nothing hardcoded)
- **SKR03** (Kontenrahmen fuer GmbH & Co. KG): stable standard. Re-verify against DATEV publication
  before each build. Source: https://www.datev.de/ — retrieved 2026-10-09 via curl (HTTP 200).
  DATEV is the dominant German accounting ecosystem; the EXTF spec and Datenservices are partner-gated.
- **SKR04** (Kontenrahmen fuer GmbH): stable standard. Same entry point as SKR03; cross-check the
  EXTF spec for field-level detail via the partner-gated portal or SDK sample files.
- **UStG tax rates 2026**: 19% standard (§12 Abs. 1), 7% reduced (§12 Abs. 2), 0% for intra-EU and
  exports (§4 Nr. 1/§6). Re-verify against https://www.gesetze-im-internet.de/uStg/ before each build.
- **DATEV AM-Konten (Automatikkonten)**: verified 2026-10-09 against the seamless-engineering/datev-extf
  reference (https://github.com/seamless-engineering/datev-extf, EXTF_AS_OF 2026-09-25). AM-Konten are
  posted automatically by DATEV; a BU-Schluessel other than "40" on them is rejected or double-counted.

## Primary sources
1. DATEV eG — https://www.datev.de/ — retrieved 2026-10-09. Entry point for SKR03/SKR04, EXTF and
   Datenservices. The Kontenrahmen itself is a free publication; the EXTF spec is partner-gated.
2. UStG (Umsatzsteuergesetz) — https://www.gesetze-im-internet.de/uStg/ — retrieved 2026-10-09.
   Authoritative text of §12 (tax rates), §4 (tax exemptions), §14 (e-invoicing), §3g (reverse charge).
3. seamless-engineering/datev-extf — https://github.com/seamless-engineering/datev-extf — retrieved
   2026-10-09. Reference implementation for the EXTF Buchungsstapel; encodes the AM-Konto list and
   the BU-Schluessel rules used by the skill's scripts.
4. BMF Schreiben to the tax advisory profession — re-verify against the current BMF letter (last major
   one: 2024-11-15 on GoBD/e-invoicing) before relying on transitional rules.

## Secondary sources (cross-check only)
- IDR (Informationsdienst der DATEV) Kontenrahmen PDFs — used only to cross-check the account list;
  any conflict is recorded below.
- Community accounting blogs — used only for pitfall anecdotes, never as authority.

## Conflicts and open questions
- **Tax-key drift**: the account-to-tax-key mapping is stable in structure but the *rate* changes with
  UStG amendments. The skill reads rates from config; a hard-coded 19% in a script is a bug, not a feature.
- **AM-Konto BU-Schluessel**: some community sources claim "40" is always correct on AM-Konten; the
  seamless-engineering reference rejects non-"40" BU-Schluessel on AM-Konten. The skill follows the
  reference and treats the community claim as unverified.
- **SKR03 vs SKR04 account overlap**: accounts 4000/4100 exist in both frameworks with different
  semantics (SKR03 4000 = sales, SKR04 4000 = sales to domestic customers). The skill pins the
  Kontenrahmen in config and refuses to guess.
