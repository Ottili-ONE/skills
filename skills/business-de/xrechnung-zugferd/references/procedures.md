# Procedures — xrechnung-zugferd

All versions are read from `config/versions.json`. Never hardcode a version in this
file or in scripts. The standard moves ~twice a year; re-verify on every bump.

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
    data = p.read_bytes()
    print('PDF/A-3 hybrid' if b'/EmbeddedFiles' in data else 'PDF-only')
else:
    print('unknown')
PY
```

**Near-miss trap:** a PDF/A-3 that embeds a *scan image* also carries
`/EmbeddedFiles` (or none at all) — it is **not** hybrid. Only a PDF/A-3 with a
`factur-x.xml` / `zugferd.xml` structured attachment is a ZUGFeRD invoice. The
validator's `classification` field distinguishes `hybrid` from `pdf-only`.

## 2. Pin versions (never hardcode)

```bash
python3 -c "import json;print(json.load(open('config/versions.json'))['xrechnung-zugferd'])"
```

Re-verification cadence: on every spec/validator bump, re-validate the archive
sample and append a dated entry to `references/SOURCES.md`.

## 3. Profile selection

| Profile | Use case | Mandatory fields beyond minimum |
|---|---|---|
| MINIMUM | B2C / minimal | BT-14, BT-20 only |
| BASIC WL | B2B with simplified line items | + BT-15, BG-25 |
| BASIC | B2B domestic, recipient accepts | + BT-17, BT-18 |
| COMFORT (EN 16931) | B2B default | full BT-* set, Leitweg-ID BT-10 |
| EXTENDED | sector extensions | COMFORT + sector BT-* |

Default for B2B: **COMFORT**.

Run `python3 scripts/profile_selector.py --context B2B --data full --recipient
factur-x` to get the recommendation plus the missing-fields list.

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

## Worked examples

### Good output — valid COMFORT invoice (XML-only)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CrossIndustryInvoice xmlns="urn:un:cefact:standard:CrossIndustryInvoice:1:1">
  <IssueDate>2026-06-02</IssueDate>          <!-- BT-14 -->
  <LeitwegID>DE12345678901234</LeitwegID>     <!-- BT-10 -->
  <PaymentTerms>net 30</PaymentTerms>          <!-- BT-20 -->
  <PaymentDueDate>2026-07-02</PaymentDueDate>  <!-- BT-17 -->
</CrossIndustryInvoice>
```

`python3 scripts/validate_invoice.py inv.xml` → `ok: true, errors: []`.

### Bad output — missing BT-14 and BT-10

```xml
<CrossIndustryInvoice xmlns="urn:un:cefact:standard:CrossIndustryInvoice:1:1">
</CrossIndustryInvoice>
```

Validator → `ok: false`, errors: `BT-14 missing`, `BT-10 missing`,
`BT-20 missing`. All three are blocking; the invoice cannot be archived until
fixed.

### Bad output — print-to-PDF "archive"

A `print-to-PDF` copy of an e-invoice is **not** a valid archive artefact: it
loses the structured XML and therefore the document is no longer machine
readable. Keep the original XML or the original PDF/A-3 with the embedded
`factur-x.xml`. The retention log must record the SHA-256 of the *original*,
not of the print copy.
