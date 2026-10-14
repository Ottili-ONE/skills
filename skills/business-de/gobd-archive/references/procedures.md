# Procedures — gobd-archive

All versions are read from `config/versions.json`. Never hardcode a version in
this file or in scripts.

## 1. Classify the document

| Document | German term | Retention class |
|---|---|---|
| Invoice, receipt, booking slip, bank statement | Buchungsbeleg | 8 years |
| Ledger entry / booking (Buchungssatz) | Buchungsbeleg | 8 years |
| Annual account (Bilanz, GuV, inventory) | Bücher / Jahresabschluss | 10 years |
| Correspondence (3 sub-types only) | Geschäftskorrespondenz | 6 years |

Retention runs from the **end of the calendar year** in which the document was
created. Effective for retention periods starting 2025-01-01 (AO §147 Abs. 3
n.F.). Let the tax advisor confirm per entity.

## 2. Enforce immutability

Immutability is a **technical** property, not a policy statement:

1. **Append-only** storage — no in-place update of a stored document.
2. **Hash-chaining** — each record stores `sha256(prev) + sha256(self)`.
3. **No deletion before retention end** — deletion after the end requires a
   documented, auditable purge with an approval record.
4. The purge record itself must be kept for the full retention period.

## 3. Verfahrensdokumentation checklist

The auditor asks for this document. It must exist for the full retention
period. It must describe:

1. **System** — what stores the accounting data (name, version, location).
2. **Storage medium** — disk, cloud, backup medium, encryption.
3. **Retention periods** — the 6/8/10-year classes with their effective date.
4. **Export format** — DATEV EXTF or CSV+XML, with a manifest.
5. **Access controls** — who can read, write, delete; how it is enforced.
6. **Backup procedure** — frequency, retention, restore test.

## 4. Export for audit

Produce a **complete, chronological, checksummed** export covering the
retention period, with a manifest. A raw DB dump is **not** an audit export.

The manifest records, per file:

```json
{"file": "...", "sha256": "...", "retention_class": "voucher",
 "retention_end": "2034-12-31", "exported": "2026-10-08"}
```

## 5. Verify on retention end

At the end of each retention period:

1. Confirm the purge is permitted (retention end reached, no open audit).
2. Document the decision (who, when, why).
3. Keep the approval record for the full retention of the purge record itself.
4. Log the run.

## 6. Worked examples — good vs bad

### 6.1 Classifying a document

**GOOD** — An invoice dated 2026-03-15. Run
`retention_classify.py --type invoice --year 2026`. Output:
`retention_class: voucher, retention_years: 8, retention_end: 2034-12-31`.
The year-end rule is applied: a 2026 document runs to 2034-12-31, not
2034-03-15.

**BAD** — The same invoice is classified as `correspondence` because "it is
paper". An invoice is a Buchungsbeleg (8y), never Geschäftskorrespondenz
(6y). The 6-year class is narrower than "all paper": only the three
sub-types in `CORRESPONDENCE_SUBTYPES` qualify. A draft quote, a working
spreadsheet or a deleted chat message is NOT a valid substitute for a
retained record.

### 6.2 Purge decision

**GOOD** — A 2017 invoice, retention_end 2025-12-31, no open audit, operator
`finance-1` approved on 2026-01-15. `purge_decision.py` emits
`{"decision": "purge_permitted", "approval": "finance-1@2026-01-15"}` and
writes a purge record whose own retention runs to 2035-12-31.

**BAD** — The operator deletes the 2017 invoice in January 2026 with no
approval record and no purge log. The retention end had just been reached, so
the deletion is *technically* permitted, but without the approval record the
auditor cannot distinguish a lawful purge from an uncontrolled delete. The
skill blocks: `purge_decision.py` exits 2 with
`"error": "no approval record on file"`.
