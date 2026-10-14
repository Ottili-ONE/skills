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


## 6. "Retention is 6 years for everything"
**Prompt:** "A colleague says retention is 6 years for everything. Who is right?"

**Expected behaviour:** Wrong for most documents. The 6-year class covers only
three sub-types (incoming commercial/business letters, copies of outgoing
letters, other tax-relevant documents) per whk-controlling.de (re-fetched
2026-10-09). Vouchers are 8 years, books/annual accounts 10 years (BEG IV,
effective 2025-01-01). Point out that a sent letter you cannot reproduce is a
GoBD violation, not a filing shortcut.

**Failure signs:** Agreeing with the 6-years-for-everything claim; collapsing
the 8/10-year classes into 6 years; treating a draft or a deleted chat as a
valid substitute.

## 7. "Deletion is automatic after the retention end"
**Prompt:** "The retention end for a 2017 invoice has passed. Can we delete it now?"

**Expected behaviour:** **No** — two independent blockers must both be cleared:
the retention end reached **and** no audit currently open. Run
`scripts/purge_decision.py`; it exits non-zero while either blocker stands, so
it is safe to wire into a CI gate. A 2017 voucher's retention end is
2025-12-31, so on 2026-10-09 the end has passed — but an open audit still
blocks.

**Failure signs:** Deleting on the calendar date alone; treating the retention
end as the only condition; skipping the approval record.

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

### N5. "The Verfahrensdokumentation is a flat JSON file with six keys"
**Trap:** the checker expects a nested `verfahrensdokumentation.sections`
object where each section carries `complete: true`. A flat file with the six
keys reports every section as missing — `verfahrensdokumentation.py --check`
exits 1 with all six in `missing_sections`, even though the *content* is
there. Build the document with `--out` and `--check` it, never hand-write
the envelope.

### N6. "One section is incomplete, the rest are fine"
**Trap:** the check is all-or-nothing. A document missing only `backup`
still exits 1 — a partial Verfahrensdokumentation is not acceptable to the
auditor. Fill every section, then re-run `--check` until `missing_sections`
is empty.

### N7. "The state file is just a cache, delete it after the check"
**Trap:** the immutability state is the hash chain that proves no
in-place modification. A state whose stored hash does not match the file
(e.g. `{'a.txt': 'deadbeef'}`) is a violation: `immutability_check.py` exits 1
with `violations: ["files (deleted)", "a.txt"]`. Deleting the state means the
next run cannot detect edits. The checker is read-only by default
(`--write-state` is opt-in) — keep the state under version control alongside
the archive.


---

## Run these checks

Every prompt above names a script and an expected exit code. This section
gives the exact, copy-paste-safe commands and the output an agent must see.
All commands are run from the skill directory
(`cd skills/business-de/gobd-archive`).

```bash
# 2. retention for a 2026 invoice -> exit 0
python3 scripts/retention_classify.py --type invoice --year 2026
# invoice -> Buchungsbeleg (8y), retention end 2034-12-31

# 2b. correspondence without a subtype -> exit 0 but unconfirmed
python3 scripts/retention_classify.py --type correspondence --year 2026 --json
# {"retention_class": "Geschäftskorrespondenz", "retention_years": 6,
#  "retention_end": "2032-12-31",
#  "warning": "the 6-year class covers only three sub-types; ..."}

# 7. purge 2017 while an audit is open -> exit 1 (blocked)
python3 scripts/purge_decision.py --type invoice --year 2017 --approver "M. Mustermann (Steuerberater)" --reason "retention ended" --open-audit --today 2026-10-14
# {"purge_permitted": false, "blockers": ["audit_open"]}

# 7b. purge 2017, no audit -> exit 0
python3 scripts/purge_decision.py --type invoice --year 2017 --approver "M. Mustermann (Steuerberater)" --reason "retention ended" --today 2026-10-14
# {"purge_permitted": true, "blockers": [],
#  "record_retention_until": "2025-12-31"}

# 7c. Verfahrensdokumentation, complete envelope -> exit 0
python3 scripts/verfahrensdokumentation.py --system "ERP v5.2" --medium "S3 encrypted" --export "DATEV EXTF" --access "RBAC" --backup "daily" --retention "8y" --out /tmp/vd.json
python3 scripts/verfahrensdokumentation.py --check /tmp/vd.json
# {"ok": true, "missing_sections": [], "checked": 6}

# 7d. Verfahrensdokumentation, flat envelope -> exit 1 (all six missing)
python3 scripts/verfahrensdokumentation.py --check evals_fixtures/vd_flat.json
# {"ok": false, "missing_sections": ["system", "medium", "retention",
#  "export", "access", "backup"], "checked": 0}

# 7e. immutability state, hash mismatch -> exit 1
python3 scripts/immutability_check.py --archive evals_fixtures/sample_archive --state evals_fixtures/state_bad.json
# {"ok": false, "violations": ["files (deleted)", "a.txt"], "new_files": ["a.txt"]}

# 7f. immutability state, matching hash -> exit 0
python3 scripts/immutability_check.py --archive evals_fixtures/sample_archive --state evals_fixtures/state_ok.json
# {"ok": true, "violations": [], "checked": 1}
```

The purge record itself is a document: keep it until the retention end of the
documents it describes (`2025-12-31` for a 2017 voucher), not until today plus
8 years. Verified 2026-10-14 against `dejure.org` (HTTP 200; the statute text
is JS-rendered, so the AO §147 classes are corroborated by
`whk-controlling.de`, HTTP 200).
