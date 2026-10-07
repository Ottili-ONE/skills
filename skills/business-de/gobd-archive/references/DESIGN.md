# DESIGN: gobd-archive

## Trigger description (SKILL.md description draft, ≤1024 chars)
"Implement GoBD-compliant (Grundsätze ordnungsmäßiger Buchführung) data retention and audit export for German accounting data: immutability, retention classes, Verfahrensdokumentation, and audit-ready export. Use when an agent must store accounting documents, set up a retention policy, produce an audit export, or decide whether a document can be deleted."

## Procedure outline
1. **Classify the document** — invoice (Buchungsbeleg), bookkeeping entry (Buchungsdatum/Buchungssatz), annual account (Bilanz/Gewinn- und Verlustrechnung), commercial correspondence (Geschäftskorrespondenz).
2. **Assign retention class** — vouchers 8 years, books/annual accounts 10 years, commercial correspondence 6 years (BEG IV, effective for retention periods starting 2025). Pin in config; let the tax advisor confirm.
3. **Enforce immutability** — append-only storage, hash-chained records, no in-place updates, no deletion before retention end, deletion only via documented, auditable purge with approval record.
4. **Write the Verfahrensdokumentation** — describe the system, the storage medium, the retention periods, the export format, the access controls, and the backup procedure. This is the document the auditor asks for.
5. **Export for audit** — produce a complete, chronological, checksummed export (DATEV EXTF or CSV+XML) covering the retention period, with a manifest.
6. **Verify on retention end** — at the end of each retention period, confirm the purge is permitted, document the decision, and keep the approval record for the full retention of the purge record itself.

## Scripts planned
- `scripts/retention_classify.py` — given a document type and date, outputs the retention class and end date.
- `scripts/audit_export.py` — produces a checksummed export manifest and archive for a given period.
- `scripts/immutability_check.py` — verifies the archive has no in-place modifications since the last check (hash-chain verification).

## Five eval prompts
1. "Our system overwrites invoices in place. Is that GoBD-compliant?" → must say no, explain immutability, and list the three fixes (append-only, hash-chaining, no in-place update).
2. "What retention period applies to a 2026 invoice and when can we delete it?" → must say 8 years from year-end (2034-12-31) for vouchers, and that deletion requires a documented purge decision.
3. "Write the Verfahrensdokumentation checklist for our archive." → must list system description, storage medium, retention periods, export format, access controls, backup procedure.
4. "Export our 2026 accounting data for the auditor." → must produce a chronological, checksummed export with a manifest, not a raw DB dump.
5. "A colleague says retention is 10 years for everything. Who is right?" → must explain the BEG IV classes (8/10/6) and that the tax advisor confirms.

## What this skill does better than generic agents
- It encodes the *legal* retention classes (BEG IV) with the correct effective date, not a generic "7 years".
- It treats immutability as a technical property (hash-chaining, append-only), not a policy statement.
- It produces the Verfahrensdokumentation checklist, which generic agents skip.
- It distinguishes the three retention classes and the purge approval record.
