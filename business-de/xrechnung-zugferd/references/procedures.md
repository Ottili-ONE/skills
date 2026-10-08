# Procedures — xrechnung-zugferd

All versions are read from `config/versions.json`. Never hardcode a version in this
file or in scripts.

## 1. Classify the document

| Input | Classification | Action |
|---|---|---|
| `.xml` with `CrossIndustryInvoice` root | XRechnung (XML-only) | Validate directly |
| `.pdf` (PDF/A-3) with structured XML attachment named `factur-x.xml` or `zugferd.xml` | ZUGFeRD / Factur-X | Extract XML, validate both PDF and XML |
| `.pdf` with unstructured attachment or no attachment | **sonstige Rechnung** | Reject; not an e-invoice |
| Paper / scanned PDF without XML | **sonstige Rechnung** | Reject; transitional rules may apply 2025-2028 |

Detection command (offline, no external tool):

```bash
python3 - <<'PY'
import sys, zipfile
from pathlib import Path
p = Path(sys.argv[1])
if p.suffix.lower() == '.xml':
    head = p.read_bytes()[:2048]
    print('XML-only' if b'CrossIndustryInvoice' in head else 'other-xml')
elif p.suffix.lower() == '.pdf':
    # crude check: PDF/A-3 carries /EmbeddedFiles
    data = p.read_bytes()
    print('PDF/A-3 hybrid' if b'/EmbeddedFiles' in data else 'PDF-only')
else:
    print('unknown')
PY
```

## 2. Pin versions (never hardcode)

```bash
python3 -c "import json;print(json.load(open('config/versions.json'))['xrechnung-zugferd'])"
```

Re-verification cadence: on every spec/validator bump, re-validate the archive sample
and append a dated entry to `references/SOURCES.md`.

## 3. Profile selection

| Profile | Use case | Mandatory fields beyond minimum |
|---|---|---|
| MINIMUM | B2C / minimal | BT-14, BT-20 only |
| BASIC WL | B2B with simplified line items | + BT-15, BG-25 |
| BASIC | B2B domestic, recipient accepts | + BT-17, BT-18 |
| COMFORT (EN 16931) | B2B default | full BT-* set, Leitweg-ID BT-10 |
| EXTENDED | sector extensions | COMFORT + sector BT-* |

Default for B2B: **COMFORT**.

## 4. Validate

Primary: KoSIT validator (tag `v2026-08-31`).
Fallback: `john-wink/en16931-php` v0.2.0.

Every **error** is blocking. Warnings must be documented, not suppressed.
Typical hard errors:

- BT-14 missing (invoice issue date) — mandatory in every profile
- BT-10 missing or malformed Leitweg-ID
- BT-20 payment terms not parseable
- Tax rate split missing for a rate present in the document

## 5. Business rules

- BT-10 Leitweg-ID: required for B2B (format: 16 hex chars, optional prefix)
- BT-20 payment terms: free text but must contain a payable-amount and a due date
- Tax split: one BG-19 per tax rate present; amount per rate must sum to the total

## 6. Archive

Keep the **original** file unchanged (XML or PDF/A-3 with embedded XML).
Do **not** keep a print-to-PDF copy — it loses the structured XML.

Retention: 8 years from year-end (BEG IV, effective 2025-01-01).
Record in the retention log:

```json
{"file": "...", "sha256": "...", "retention_end": "2034-12-31",
 "export_test": "passed", "validated": "2026-10-08"}
```

## 7. Re-verification

On any spec/validator bump:

```bash
python3 scripts/retention_check.py --archive ./archive --config config/versions.json
```

Append a dated entry to `references/SOURCES.md` recording the run.
