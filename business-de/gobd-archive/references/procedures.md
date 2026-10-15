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

### 2b. `immutability_check.py` is read-only by default

A GoBD audit check must not modify the archive's own bookkeeping, so the
script never rewrites the state file unless told to:

- `python3 immutability_check.py --archive ./archive --state ./state.json`
  — read-only. A missing state file is a *result* (no baseline yet), not an
  error; the script tells you how to create one.
- `--init-state` — seed a brand-new state file (first run only).
- `--write-state` — refresh an existing state file.
- `--strict` — also fail on new files (append-only is expected, not
  required for a first run).

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

### 4b. `audit_export.py --verify` checks both directions

`--verify` re-checks every exported file against the manifest **and** checks
that every file physically present in the export is listed in the manifest.
A "rogue" file is an incomplete export, not a silent omission:

```bash
python3 audit_export.py --source ./archive --output ./export --year 2026 --verify
```

An empty archive produces a valid (empty) export with a manifest -- it is not
an audit failure.

## 5. Verify on retention end

At the end of each retention period:

1. Confirm the purge is permitted (retention end reached, no open audit).
2. Document the decision (who, when, why).
3. Keep the approval record for the full retention of the purge record itself.
4. Log the run.

### 5b. Deterministic purge decisions

`purge_decision.py` accepts `--today YYYY-MM-DD`, so the outcome does not
flip on the wall clock across year boundaries. A 2020 invoice (retention end
2028-12-31) is **blocked** under `--today 2027-01-01` and **permitted** under
`--today 2029-01-01`. The purge record's own retention is derived from the
*document* year: a 2017 voucher record is kept until `2025-12-31`, never
until today + 8 years.
