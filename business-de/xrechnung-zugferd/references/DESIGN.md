# DESIGN — xrechnung-zugferd

## Trigger description (draft for SKILL.md front matter)

> Use this skill when an Ottili agent must create, validate, convert, archive
> or decide the validity of a German e-invoice (XRechnung / ZUGFeRD / Factur-X)
> under EN 16931 and UStG §14. Triggers: "is this a valid e-invoice", "which
> profile do I need", "convert this PDF invoice to Factur-X", "archive this
> invoice GoBD-compliant", "the KoSIT validator rejected BT-18".

## What this skill does better than a generic agent

- **Profile cascade with a default**: B2B domestic + full data → COMFORT (EN
  16931). Not "use the highest profile" but a context × data × recipient
  capability table with a defined default and an explicit EXTENDED trigger.
- **BT-18 ≠ BT-20 scoping rule**: both map to the UBL local name
  `PaymentTerms` in some exports, so a whole-document regex false-passes. The
  skill scopes every BT-* check to the element's own text content and ships a
  test that proves the distinction (an IBAN must not satisfy BT-20).
- **Version pinning as a first-class step**: spec and validator versions live
  in `config/versions.json`, never in logic; the skill names the re-verification
  cadence and the exact tags (`v2026-08-31`, KoSIT v1.6.3, CEN Schematron
  1.3.16).
- **Archive artefact rule**: a print-to-PDF **drops the structured XML
  attachment** and is therefore not a valid archive artefact. The skill keeps
  the original and records SHA-256, plus a retrieval-path + export test.
- **Fails closed**: an unrecognised context does not silently fall back to
  COMFORT; `profile_selector.py` exits non-zero.

## Procedure outline

1. **Classify the document** — XML-only (XRechnung), hybrid PDF/A-3 + XML
   (ZUGFeRD/Factur-X), or other (reject as "sonstige Rechnung").
2. **Pin versions** — read `config/versions.json`; re-verify on spec bump and
   log the run in SOURCES.md.
3. **Choose the profile** — MINIMUM / BASIC WL / BASIC / COMFORT / EXTENDED
   via the decision table; default B2B = COMFORT.
4. **Validate** — KoSIT validator tag `v2026-08-31` (or the
   `john-wink/en16931-php` v0.2.0 pure-Python fallback). Every error blocks;
   warnings must be documented. Run `scripts/validate_invoice.py` for the
   offline subset.
5. **Check business rules** — mandatory BT-* fields, Leitweg-ID in BT-10,
   payment terms syntax in BT-20, tax split per rate in BT-19.
6. **Archive** — retain the original artefact unchanged; SHA-256 + retrieval
   path + export test; retention 8 years from year-end (BEG IV, effective
   2025-01-01). Verify later with `scripts/retention_check.py`.
7. **Re-verify** — on any spec/validator bump, re-validate the whole archive
   sample and log it.

## Scripts planned

| Script | Purpose |
|---|---|
| `scripts/profile_selector.py` | Context → profile; fails closed on unrecognised input. |
| `scripts/validate_invoice.py` | Offline BT-* validation scoped to element text; exits non-zero on failure. |
| `scripts/retention_check.py` | Verifies an archived invoice: original present, SHA-256 matches, retention end date computed, export test passed. |

## Five eval prompts

1. **Profile default.** "B2B domestic invoice with full EN 16931 data, recipient
   is Factur-X capable. Which profile?" → COMFORT (EN 16931). Failure sign:
   recommending MINIMUM or EXTENDED.
2. **BT-18 vs BT-20.** "An invoice has an IBAN in the payment block and the
   words 'Zahlbar innerhalb 30 Tagen' elsewhere. Does it pass BT-18 and BT-20?"
   → BT-18 passes (IBAN in the account element), BT-20 passes (terms in the
   terms element). Failure sign: an IBAN satisfying BT-20's "contains a digit"
   test on a whole-document regex.
3. **Print-to-PDF archive.** "We archived a print-to-PDF of the e-invoice.
   Is that GoBD-valid?" → No — the XML attachment is gone. Failure sign:
   accepting the print-to-PDF as the archive artefact.
4. **Unrecognised context.** "Recipient is a B2C customer with minimal data."
   → MINIMUM, and it is rarely an e-invoice at all. Failure sign: silently
   recommending COMFORT.
5. **Version bump.** "The spec moved to the next version. What do we do?"
   → Re-read `config/versions.json`, re-validate the archive sample, log the
   run in SOURCES.md. Failure sign: keeping the old validator tag and assuming
   the archive is still valid.
