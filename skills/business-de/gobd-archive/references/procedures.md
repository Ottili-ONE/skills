# Procedures — gobd-archive

All versions are read from `config/versions.json`. Never hardcode a version in
this file or in scripts.

## 1. Classify the document

| Document | German term | Retention class |
|---|---|---|
| Invoice, receipt, booking slip, bank statement | Buchungsbeleg | 8 years |
| Ledger entry / booking (Buchungssatz) | Buchungsbeleg | 8 years |
| Annual account (Bilanz, GuV, inventory) | Bücher / Jahresabschluss | 10 years |
| Commercial correspondence (email, contract, letter) | Geschäftskorrespondenz | 6 years |

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

## Worked examples

### Good — classify a 2026 invoice

```bash
python3 scripts/retention_classify.py --type invoice --year 2026 --json
```

```json
{"ok": true, "document_type": "invoice", "retention_class": "Buchungsbeleg",
 "retention_years": 8, "effective_date": "2025-01-01",
 "retention_end": "2034-12-31", "purge_permitted_after": "2034-12-31",
 "deletion_requires": ["documented purge decision", ...]}
```

### Good — audit export with manifest

```bash
python3 scripts/audit_export.py --source ./archive --output ./export --year 2026 --verify
```

→ `ok: true`, `files: N`, `verify.ok: true`, `MANIFEST.json` written with
per-file SHA-256, export date and period.

### Bad — in-place overwrite

A system that overwrites `invoice-2026-01.pdf` when the supplier re-sends it
violates GoBD immutability. `scripts/immutability_check.py --archive ./archive
--state ./state.json --strict` reports the file under `violations` because its
SHA-256 changed. Fix: write the re-sent invoice as a new file (append-only).

### Bad — "10 years for everything"

A colleague says every document is kept 10 years. For retention periods starting
on/after 2025-01-01 that is wrong: vouchers 8, books/annual accounts 10,
correspondence 6. The "10 years" rule applies only to vouchers whose retention
started before 2025. Confirm with the tax advisor.
