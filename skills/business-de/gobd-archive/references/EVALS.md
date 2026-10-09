# EVALS — gobd-archive

Each prompt lists the expected behaviour and the failure signs an agent must
watch for. Run the relevant script and compare the output to the expected.

## 1. In-place overwrite — is it GoBD-compliant?
**Prompt:** "Our system overwrites invoices in place. Is that GoBD-compliant?"

**Expected behaviour:** Say **no**. Explain immutability as a technical
property: append-only storage, hash-chained records, no in-place update. List
the three fixes: (1) append-only storage, (2) hash-chaining, (3) forbid in-place
update. Reference the Verfahrensdokumentation requirement.

**Failure signs:** Calling in-place overwrite acceptable; suggesting a policy
statement instead of a technical control; omitting the purge approval record.

## 2. Retention period for a 2026 invoice
**Prompt:** "What retention period applies to a 2026 invoice and when can we delete it?"

**Expected behaviour:** 8 years from year-end → **2034-12-31** (Buchungsbeleg,
AO §147 Abs. 3 n.F., effective 2025-01-01). Deletion after that requires a
documented purge decision with an approval record. Demonstrate
`scripts/retention_classify.py --type invoice --year 2026`.

**Failure signs:** Saying 7 years; computing from the invoice date instead of
year-end; saying deletion is automatic on the end date.

## 3. Verfahrensdokumentation checklist
**Prompt:** "Write the Verfahrensdokumentation checklist for our archive."

**Expected behaviour:** List all six items: system description, storage medium,
retention periods, export format, access controls, backup procedure. State that
it must exist for the full retention period and that a missing one is a fine
risk (up to EUR 50,000 under §378 AO).

**Failure signs:** A checklist missing access controls or the backup procedure;
omitting the retention-period link.

## 4. Export 2026 accounting data for the auditor
**Prompt:** "Export our 2026 accounting data for the auditor."

**Expected behaviour:** Produce a chronological, complete, checksummed export
with a manifest (MANIFEST.json), not a raw DB dump. Demonstrate
`scripts/audit_export.py --source ./archive --output ./export --year 2026`.

**Failure signs:** Exporting a raw DB dump; omitting the manifest; exporting
out of chronological order.

## 5. "Retention is 10 years for everything" — who is right?
**Prompt:** "A colleague says retention is 10 years for everything. Who is right?"

**Expected behaviour:** The colleague is wrong for documents whose retention
period starts on/after 2025-01-01. Explain the BEG IV / AO §147 classes: 10y for
books/annual accounts, 8y for vouchers, 6y for commercial correspondence. The
"10 years for everything" rule applies only to vouchers whose retention started
before 2025. Let the tax advisor confirm per entity.

**Failure signs:** Agreeing with the colleague unconditionally; citing the old
guidance without the effective date; failing to mention the tax-advisor
confirmation.


## Near-miss triggers

### N1. "Retention is 6 years for everything"
**Trap:** the 6-year class is narrower than "all correspondence". Per
whk-controlling.de (re-fetched 2026-10-09) it covers *empfangene* Handels- oder
Geschäftsbriefe, **Wiedergaben der abgesandten Handelsbriefe** (copies of
outgoing letters) and sonstige Unterlagen mit steuerlicher Bedeutung. An
outgoing letter you cannot reproduce is a GoBD violation.

### N2. "Deletion is automatic after the retention end"
**Trap:** two independent blockers — the retention end must be reached **and**
no audit may be open. Both are checked by `scripts/purge_decision.py`, which
exits non-zero when blocked.

### N3. "The purge record can be deleted with the documents"
**Trap:** the purge record itself is a document — keep it for the full
retention period of the documents it describes (a 2017 purge record is kept
until 2025-12-31 for vouchers).

### N4. "A raw DB dump is fine for the auditor"
**Trap:** an audit export must be chronological, complete, checksummed and
carry a manifest (MANIFEST.json). A raw DB dump is not an audit export.
