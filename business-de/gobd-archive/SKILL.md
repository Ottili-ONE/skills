# gobd-archive

## When to use this skill

Use this skill when an agent must store accounting documents, set up a retention
policy, produce an audit export, or decide whether a document may be deleted,
under German GoBD (Grundsätze ordnungsmäßiger Buchführung). It applies to
Buchungsbelege, Buchungssätze, Jahresabschlüsse and Geschäftskorrespondenz.
Do **not** use it for non-accounting files, non-German entities, or retention
periods that the tax advisor has not confirmed.

## Description

Implement GoBD-compliant data retention and audit export for German accounting
data: immutability, retention classes, Verfahrensdokumentation, and audit-ready
export. Use when an agent must store accounting documents, set up a retention
policy, produce an audit export, or decide whether a document can be deleted.

## Procedure

1. **Classify the document** — invoice (Buchungsbeleg), bookkeeping entry
   (Buchungsdatum/Buchungssatz), annual account (Bilanz/GuV), commercial
   correspondence (Geschäftskorrespondenz).
2. **Assign retention class** — vouchers 8 years, books/annual accounts 10
   years, commercial correspondence 6 years (BEG IV, effective for retention
   periods starting 2025). Pin in config; let the tax advisor confirm.
3. **Enforce immutability** — append-only storage, hash-chained records, no
   in-place updates, no deletion before retention end, deletion only via a
   documented, auditable purge with an approval record.
4. **Write the Verfahrensdokumentation** — describe the system, the storage
   medium, the retention periods, the export format, the access controls, and
   the backup procedure. This is the document the auditor asks for.
5. **Export for audit** — produce a complete, chronological, checksummed export
   (DATEV EXTF or CSV+XML) covering the retention period, with a manifest.
6. **Verify on retention end** — at the end of each retention period, confirm
   the purge is permitted, document the decision, and keep the approval record
   for the full retention of the purge record itself.

## Decision tables

### Retention classes (BEG IV, effective 2025-01-01)

| Document type | Examples | Retention | End date for a 2026 doc |
|---|---|---|---|
| Buchungsbeleg (voucher) | invoice, receipt, booking slip | 8 years | 2034-12-31 |
| Bücher / Jahresabschluss | ledger, Bilanz, GuV | 10 years | 2036-12-31 |
| Geschäftskorrespondenz | email, contract, letter | 6 years | 2032-12-31 |

Retention runs from the end of the calendar year in which the document was
created. Let the tax advisor confirm per entity.

## Pitfalls from research

- In-place overwrite of an invoice is **not** GoBD-compliant; immutability is a
  technical property (append-only + hash-chaining), not a policy statement.
- The 6/8/10-year classes come from BEG IV (effective 2025-01-01); older
  guidance said 10 years for everything. Always pin the effective date.
- Deletion before the retention end is never permitted; deletion after the end
  requires a documented purge decision and an approval record, and the purge
  record itself must be kept for the full retention period.
- A raw DB dump is **not** an audit export — it must be chronological, complete
  and checksummed with a manifest.

## Verification checklist

- [ ] Document classified correctly
- [ ] Retention class and end date assigned per BEG IV
- [ ] Immutability enforced (append-only, hash-chained, no in-place update)
- [ ] Verfahrensdokumentation written (system, medium, periods, export, access, backup)
- [ ] Audit export is chronological, complete, checksummed, with a manifest
- [ ] Purge decision documented and approval record retained
- [ ] Re-verification run logged

## References

- [Procedures and worked examples](references/procedures.md)
- [Standards and sources](references/SOURCES.md)
- [EVALS](references/EVALS.md)
