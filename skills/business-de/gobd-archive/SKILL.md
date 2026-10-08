---
name: gobd-archive
description: "Implement GoBD-compliant (Grundsätze ordnungsmäßiger Buchführung) data retention and audit export for German accounting data: immutability, retention classes, Verfahrensdokumentation, and audit-ready export. Use when an agent must store accounting documents, set up a retention policy, produce an audit export, or decide whether a document can be deleted."
license: MIT-compat
compatibility: "framework-agnostic; German GoBD / AO §147 retention; offline validation"
metadata: {}
allowed-tools: []
---

# gobd-archive

## When to use this skill

Use this skill when an agent must store accounting documents, set up a retention
policy, produce an audit export, or decide whether a document can be deleted.
Covers the BEG IV / AO §147 retention classes (effective 2025-01-01), technical
immutability, the Verfahrensdokumentation, and the audit export artefact.

## Quick reference

| Item | Value |
|---|---|
| Vouchers (Buchungsbelege) | 8 years from year-end |
| Books / annual accounts (Bücher/Jahresabschluss) | 10 years from year-end |
| Commercial correspondence (Handels-/Geschäftsbriefe) | 6 years from year-end |
| Effective date | 2025-01-01 (AO §147 Abs. 3 n.F.) |
| Deletion | never before retention end; only via documented purge |
| Fine risk for missing Verfahrensdokumentation | up to EUR 50,000 (§378 AO) |

Read every value from `config/versions.json`; never hardcode.

## Procedure

1. **Classify the document** — invoice (Buchungsbeleg), bookkeeping entry
   (Buchungsdatum/Buchungssatz), annual account (Bilanz/Gewinn- und
   Verlustrechnung), commercial correspondence (Geschäftskorrespondenz).
2. **Assign retention class** — vouchers 8 years, books/annual accounts 10
   years, commercial correspondence 6 years (BEG IV, effective for retention
   periods starting 2025). Pin in config; let the tax advisor confirm.
   Run `python3 scripts/retention_classify.py --type … --year …`.
3. **Enforce immutability** — append-only storage, hash-chained records, no
   in-place updates, no deletion before retention end, deletion only via
   documented, auditable purge with approval record.
4. **Write the Verfahrensdokumentation** — describe the system, the storage
   medium, the retention periods, the export format, the access controls, and
   the backup procedure. This is the document the auditor asks for.
5. **Export for audit** — produce a complete, chronological, checksummed
   export (DATEV EXTF or CSV+XML) covering the retention period, with a
   manifest. Run `python3 scripts/audit_export.py --source … --output … --year …`.
6. **Verify on retention end** — at the end of each retention period, confirm
   the purge is permitted, document the decision, and keep the approval record
   for the full retention of the purge record itself.

## Decision tables

### Retention classes (AO §147 Abs. 3 n.F., effective 2025-01-01)

| Document type | Class | Years | Retention end for 2026 |
|---|---|---|---|
| invoice / voucher / bank statement / booking | Buchungsbeleg | 8 | 2034-12-31 |
| ledger / annual account / balance sheet | Bücher / Jahresabschluss | 10 | 2036-12-31 |
| correspondence / contract | Geschäftskorrespondenz | 6 | 2032-12-31 |

**Threshold rule:** the class depends on the *most demanding* document in a set —
a mixed archive takes the longest period. Documents whose retention period
started **before 2025-01-01** keep the old rule (10 years for vouchers under the
pre-2025 AO §147); confirm with the tax advisor.

## Pitfalls from research

- **"10 years for everything" is wrong** for periods starting on/after 2025-01-01:
  only books/annual accounts get 10 years; vouchers get 8 and correspondence 6.
- In-place overwrite of an invoice is **not** GoBD-compliant. Fix with
  append-only storage, hash-chaining, and no in-place update.
- The BEG URL (`gesetze-im-internet.de/beg/`) now resolves to the
  Bundesentschädigungsgesetz, not the retention statute — the classes live in
  AO §147. Re-verified 2026-10-08 against dejure.org and provimedia.de.
- Deletion before the retention end is never permitted. After the end, delete
  only via a documented, auditable purge, and keep the purge approval record for
  the full retention period of the purge record itself.
- A missing Verfahrensdokumentation is a fine risk (up to EUR 50,000 under
  §378 AO) — it is not optional documentation.

## Verification checklist

- [ ] Document classified correctly
- [ ] Retention class and end date assigned per decision table
- [ ] Immutability verified (hash-chain, no in-place modifications)
- [ ] Verfahrensdokumentation complete (system, medium, periods, export format, access controls, backup)
- [ ] Audit export chronological, checksummed, with manifest
- [ ] Purge decision documented and approved before any deletion
- [ ] Re-verification date recorded in SOURCES.md

## References

- [Procedures and worked examples](references/procedures.md)
- [Standards and sources](references/SOURCES.md)
- [EVALS](references/EVALS.md)
