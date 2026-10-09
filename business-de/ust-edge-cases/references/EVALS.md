# ust-edge-cases — EVALS

Eight realistic prompts with expected behaviour and failure signs. Each
names a concrete input, the correct output, and the near-miss that a strong
generic agent would most likely produce.

## 1. Prompt
> "Invoice: intra-EU B2B supply of goods to a French customer with USt-IdNr.
> DE999999999. Net EUR 100. What is the tax treatment?"

**Expected behaviour:** tax key **06/0**, tax amount **0.00**, no tax line.
Reference UStG §4a and the EZM (Zusammenfassende Meldung) duty.

**Failure signs:** 19% applied; a 1570 line with a non-zero amount; no
verification of the USt-IdNr. in VIES.

## 2. Prompt
> "Our business had EUR 18,000 turnover last year. We are a
> Kleinunternehmer. Invoice a domestic customer for EUR 100."

**Expected behaviour:** no tax line, gross EUR 100 lands in revenue, tax
key 0. `scripts/ust_check.py` exits 0 with `kleinunternehmer: true`.

**Failure signs:** a 19% tax line; a 1570 account amount; the turnover
threshold not checked.

## 3. Prompt
> "Reverse charge on a service (IT consultancy) to a German customer.
> Which tax key?"

**Expected behaviour:** **not** §13b — §13b is goods only. Apply the
general place-of-performance rule (likely 19%). Flag the distinction.

**Failure signs:** applying 06/0 to a service.

## 4. Prompt
> "Net EUR 33.33 at 19%. What is the tax amount?"

**Expected behaviour:** 6.3326 → **6.33** (rounded to cents, half-up).
`scripts/ust_check.py` accepts 6.33, rejects 6.3326 or 6.34.

**Failure signs:** unrounded amount; inconsistent rounding convention.

## 5. Prompt
> "This invoice is for EUR 199.90 gross. Is it an e-invoice?"

**Expected behaviour:** it is a **Kleinbetagsrechnung** (< EUR 250) — exempt
from the issuing obligation, so a "sonstige Rechnung" is acceptable. But the
business must still be **able to receive** e-invoices.

**Failure signs:** treating it as a mandatory e-invoice; issuing a
non-conforming document and calling it an e-invoice.

## 6. Prompt (near-miss — reverse charge on a service)
> "Supply IT consultancy to a French company that gives us its
> USt-IdNr. DE123456789. Can we use reverse charge?"

**Expected behaviour:** **no** — §13b is goods only. Reverse charge for
services does not exist in that form; the general place-of-performance rule
applies (likely 19% for a German provider). The skill must refuse 06/0 and
say so explicitly.

**Failure signs:** applying 06/0 because a USt-IdNr. was supplied — the
USt-IdNr. is necessary but not sufficient.

## 7. Prompt (near-miss — Kleinunternehmer above the threshold)
> "Our prior-year turnover was EUR 25,000. We call ourselves a
> Kleinunternehmer. Invoice a domestic customer for EUR 100 at 0%."

**Expected behaviour:** **rejected** — EUR 25,000 exceeds the EUR 22,000
threshold, so the entity is not a Kleinunternehmer and must charge 19%.
`scripts/ust_check.py` exits 2.

**Failure signs:** self-declaring Kleinunternehmer without checking the
prior-year figure.

## 8. Prompt (near-miss — 0% key with a tax amount)
> "Book an intra-EU supply: `06/0`, net 100.00, tax amount 0.00. Is that
> enough?"

**Expected behaviour:** arithmetically correct, but the skill must also ask
for the customer USt-IdNr. verification record and the EZM reporting duty.
A 0% rate with a non-zero tax amount is rejected outright.

**Failure signs:** treating a 0% key as interchangeable with a taxed key;
charging a tax amount on a 06/0 line.
