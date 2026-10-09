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
   for the full retention of the purge record itself. Two independent
   blockers: the retention end must be reached **and** no audit may be open.
   Produce the record with `scripts/purge_decision.py` (it exits non-zero
   when the purge is blocked, so it is safe to wire into a CI gate).

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
- **The 6-year class is narrower than "all correspondence".** Per whk-controlling.de
  (re-fetched 2026-10-09) it covers *empfangene* Handels- oder Geschäftsbriefe,
  **Wiedergaben der abgesandten Handelsbriefe** (copies of outgoing letters) and
  sonstige Unterlagen mit steuerlicher Bedeutung. An outgoing letter you cannot
  reproduce is a GoBD violation, not a filing shortcut.
- **Three blockers, not one.** A purge is blocked if (a) the retention end has
  not been reached, OR (b) an audit is currently open. Both are checked by
  `scripts/purge_decision.py` before any deletion.
- The purge record itself is a document: keep it for the full retention period
  of the documents it describes (a 2017 purge record is kept until 2025-12-31
  for vouchers).

## Verification checklist

- [ ] Document classified correctly
- [ ] Retention class and end date assigned per BEG IV
- [ ] Immutability enforced (append-only, hash-chained, no in-place update)
- [ ] Verfahrensdokumentation written (system, medium, periods, export, access, backup)
- [ ] Audit export is chronological, complete, checksummed, with a manifest
- [ ] Purge decision documented and approval record retained (retention end
      reached AND no open audit)
- [ ] Purge record itself retained for the full retention period
- [ ] Re-verification run logged

## References

- [Procedures and worked examples](references/procedures.md)
- [Standards and sources](references/SOURCES.md)
- [EVALS](references/EVALS.md)
