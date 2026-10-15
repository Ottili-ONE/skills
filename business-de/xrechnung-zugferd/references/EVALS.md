# EVALS — xrechnung-zugferd

Each prompt lists the expected behaviour and the failure signs an agent must
watch for. Run `scripts/validate_invoice.py` on the generated artefact and
compare the JSON output to the expected `ok`/`errors`.

## 1. PDF-only invoice — is it an e-invoice?
**Prompt:** "Our supplier sent a plain PDF invoice with no XML. Is it an e-invoice under German law, and what do we do?"

**Expected behaviour:** Classify as **sonstige Rechnung** (not an e-invoice).
State the UStG §14 e-invoicing obligation applies to B2B from 2020-01-01 and
that a PDF-only document does not satisfy it. List the 2025-2028 transitional
options (acceptance of paper/PDF under the BMF Schreiben 2024-11-15) and the
required next step: request a structured invoice (Factur-X/COMFORT).

**Failure signs:** Calling the PDF an e-invoice; recommending a print-to-PDF
copy as the archive artefact; omitting the transitional period; failing to
mention that the obligation is on the *recipient* to accept e-invoices.

## 2. Generate a ZUGFeRD invoice for a domestic B2B sale
**Prompt:** "Generate a ZUGFeRD invoice for a domestic B2B sale, EUR 1,200.00 net, 19% VAT, buyer has a Leitweg-ID."

**Expected behaviour:** Produce a Factur-X/COMFORT document (PDF/A-3 with
embedded XML) containing BT-10 with the Leitweg-ID, BT-14 issue date, BT-20
payment terms, and a BG-19 tax split for the 19% rate. Run
`scripts/validate_invoice.py`; expect `classification: hybrid`, `ok: true`,
`errors: []`.

**Failure signs:** Emitting XML-only (XRechnung) when ZUGFeRD was requested;
omitting BT-10; producing a print-to-PDF instead of a PDF/A-3 with a structured
attachment; reporting `ok: true` without running the validator.

## 3. Validator reports BT-14 missing
**Prompt:** "My validator reports rule BT-14 missing. What is BT-14 and how do I fix it?"

**Expected behaviour:** Name BT-14 as the **invoice issue date**
(Ausstellungsdatum der Rechnung). State it is mandatory in **every** profile
(MINIMUM through EXTENDED) and that the KoSIT validator 5.x treats it as a hard
error. Give the fix: add `<cbc:IssueDate>YYYY-MM-DD</cbc:IssueDate>` to the
invoice header.

**Failure signs:** Describing BT-14 as optional; suggesting a workaround to
suppress the error; confusing BT-14 with BT-15 (delivery date).

## 4. Pin the XRechnung spec version and show a re-verification run
**Prompt:** "Pin the XRechnung spec version we use and show how a re-verification run would look."

**Expected behaviour:** Read `config/versions.json` (never hardcode) and print
the pinned `en16931` and `kosit-validator` versions. Show a dated re-verification
log entry that records the run, the validator tag, and the archive sample result.
Demonstrate `scripts/validate_invoice.py --config config/versions.json`.

**Failure signs:** Hardcoding a version in the output; omitting the retrieval
date; showing a re-verification that does not re-validate the archive sample.

## 5. Archive this invoice — which file and until when?
**Prompt:** "Archive this invoice: which file do we keep and until when?"

**Expected behaviour:** Keep the **original** file unchanged (XML, or PDF/A-3
with embedded XML). Never keep a print-to-PDF copy. Compute retention as 8
years from year-end (BEG IV): a 2026 invoice is retained until **2034-12-31**.
Record SHA-256, retrieval path and an export test in the retention log.

**Failure signs:** Archiving a print-to-PDF; computing 7 years; omitting the
checksum; failing to record the export test.


## 6. The IBAN is in the PaymentTerms element
**Prompt:** "Our invoice has `<PaymentTerms>IBAN DE89370400440532013000</PaymentTerms>` and
`<PaymentAllowedAccountID>` is missing. The validator says BT-18 is invalid — is
the validator wrong?"

**Expected behaviour:** No, the validator is right. BT-18 is
`PaymentAllowedAccountID` (the bank account) and BT-20 is `PaymentTerms` (free
text). Scoping the check to the element's own text — not the whole document — is
what makes this correct: the IBAN sits in BT-20, so BT-18 is genuinely missing.
A whole-document IBAN regex would false-pass because BT-10's Leitweg-ID
(`DE...`) also matches it. Verified 2026-10-09 against the KoSIT
`validator-configuration-xrechnung guidelines.json`. Give the fix: move the IBAN
into `<cbc:PaymentAllowedAccountID>` and put real payment terms in
`<cbc:PaymentTerms>`.

**Failure signs:** Saying the validator is wrong; running a whole-document IBAN
regex; claiming BT-18 and BT-20 are the same field; failing to distinguish
`PaymentAllowedAccountID` from `PaymentTerms`.


## Near-miss triggers

Prompts that look fine at first glance but hide a trap. The agent must catch
the trap and still produce a passing artefact.

### N1. "The invoice has a Leitweg-ID, so BT-18 is fine"
**Trap:** BT-18 is the **payment account (IBAN)**, not the Leitweg-ID. A
whole-document IBAN regex passes because BT-10's `DE...` value matches it.
Scope every check to the element's own text (see `references/procedures.md`
§4b). Verified 2026-10-09 against the KoSIT `guidelines.json`.

### N2. "BT-20 is the payment account"
**Trap:** BT-20 is `PaymentTerms` (free text), BT-18 is
`PaymentAllowedAccountID` (the IBAN). Some UBL exports give both the same
local name `PaymentTerms`. An IBAN written into BT-20 does **not** satisfy
BT-18. Verified 2026-10-09 against the KoSIT `guidelines.json`.

### N3. "BT-15 is the issue date"
**Trap:** BT-15 is `cbc:DeliveryDate` (the delivery date), NOT
`cbc:IssueDate`. Earlier drafts of this skill reused the issue-date element
name for BT-15, which would have let an invoice pass BT-15 with only its
issue date present. Verified 2026-10-15 against the KoSIT
`validator-configuration-xrechnung guidelines.json`
(rule BT-15 = Auslieferdatum/Lieferdatum -> `cbc:DeliveryDate`).

### N4. "A 2026 invoice is archived until 2033"
**Trap:** 8 years from year-end, not 7. A 2026 invoice is retained until
**2034-12-31**. The clock starts at the end of the calendar year of creation,
not on the document's own date. Verified 2026-10-08 against AO §147 Abs. 3
n.F. (BEG IV, effective 2025-01-01).

### N5. "The validator says BT-14 is fine, so we can archive the print-to-PDF"
**Trap:** a print-to-PDF **drops the structured XML attachment**, so it is
not a valid archive artefact even if the validator ran on the original XML.
Keep the original file (XML, or PDF/A-3 with embedded XML) and record its
SHA-256.
