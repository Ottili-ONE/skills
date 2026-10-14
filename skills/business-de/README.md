# business-de — German business skill package

Ten domain skills for German accounting, compliance, carriers, e-invoicing and
archive work. All scripts are **offline-first**: they run with no network and
only contact a carrier when you pass `--execute`. Install with
`python3 scripts/install-skill.py business-de` or copy the folder next to your
other skills.

## Skills

- **bank-reconciliation-camt** — Reconcile camt.053/MT940 files against open
  items; balance equation, duplicate, unallocated and rounding checks with
  reason codes. `scripts/recon_check.py`.
- **carrier-apis-de** — DHL, DHL-Express, DPD, GLS, Hermes, UPS label, track and
  reconcile calls with idempotency keys and TTL-cached tracking.
  `scripts/label_create.py`, `scripts/track.py`, `scripts/reconcile.py`.
- **datev-extf** — Build and validate DATEV EXTF (KID 700/701/702) stapel and
  single postings from CSV; checks the 2026 field layout and account rules.
  `scripts/build_stapel.py`, `scripts/validate_extf.py`.
- **dsgvo-ai-act-labeling** — Classify training data under the EU AI Act and
  GDPR; produces a labeling decision record with article mapping and review
  gates. `scripts/process_register.py`, `scripts/disclosure_label.py`, `scripts/label_check.py`.
- **gobd-archive** — GoBD-compliant archive export: retention periods, hash
  chains, index and retrieval test. `scripts/audit_export.py`, `scripts/retention_classify.py`, `scripts/purge_decision.py`, `scripts/verfahrensdokumentation.py`, `scripts/immutability_check.py`.
- **publish-reconcile-wp-meta** — Reconcile WordPress post meta against a
  publish log; detects double-publish, missing meta and drift.
  `scripts/reconcile.py`, `scripts/wp_publish.py`, `scripts/meta_publish.py`, `scripts/idempotency_store.py`.
- **skr-journal-mapping** — Map SKR 03/04/18/25 accounts to posting templates;
  validates the complete journal against the chart of accounts.
  `scripts/map_skr.py`, `scripts/journal_check.py`.
- **ust-edge-cases** — Umsatzsteuer edge cases: rounding, zero-rated, intra-community
  and chain transactions with a decision table per scenario.
  `scripts/ust_check.py`.
- **webhooks-safe** — Validate webhook payloads before acting: signature
  verification, replay-window and payload-schema checks.
  `scripts/verify.py`, `scripts/dedupe.py`, `scripts/ordering.py`, `scripts/deadletter.py`, `scripts/ssrf_check.py`.
- **xrechnung-zugferd** — Build and validate XRechnung/ZUGFeRD 2.x/3.x
  invoices; namespace, business rule and semantic checks.
  `scripts/validate_invoice.py`.

## Install hints

```bash
# from the repo root
python3 scripts/install-skill.py business-de

# run the offline validator on all ten skills
python3 scripts/validate_skill.py --all

# run every EVALS.md prompt as a real command
python3 skills/business-de/scripts/run_evals.py
```

Each skill ships `references/EVALS.md` (5 prompts + 3 near-misses with expected
exit codes), `references/SOURCES.md` (version pins and retrieval dates) and
`evals_fixtures/` (shipped sample inputs for the runnable command sections).
See `HANDOFF.md` for what to re-verify before the next ten skills.
