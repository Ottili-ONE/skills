# ust-edge-cases — EVALS

Eight realistic prompts with expected behaviour and failure signs. Each
names a concrete input, the correct output, and the near-miss that a strong
generic agent would most likely produce.

## 1. Prompt
> "Invoice: intra-EU B2B supply of goods to a French customer with USt-IdNr.
> DE999999999. Net EUR 100. What is the tax treatment?"

**Expected behaviour:** tax key **06/0**, tax amount **0.00**, no tax line.
This is the general intra-EU rule (\u00a74a), *not* reverse charge. Reference
the EZM (Zusammenfassende Meldung) duty. Run
`scripts/ust_check.py` with `reverse_charge: false, supply_type: "goods"` \u2014
exits 0.

**Failure signs:** 19% applied; a 1570 line with a non-zero amount; labelling
the supply as reverse charge (\u00a73g); no VIES verification record.

## 2. Prompt
> "Our business had EUR 18,000 turnover last year. We are a
> Kleinunternehmer. Invoice a domestic customer for EUR 100."

**Expected behaviour:** no tax line, gross EUR 100 lands in revenue, tax key
0. `scripts/ust_check.py` exits 0 with `kleinunternehmer: true` and
`prior_turnover: 18000`.

**Failure signs:** a 19% tax line; a 1570 account amount; the turnover
threshold not checked.

## 3. Prompt
> "Reverse charge on a supply of goods to a German customer. Which tax key?"

**Expected behaviour:** **not** \u00a73g \u2014 \u00a73g is services only. A goods
supply to a customer with a USt-IdNr. uses the general intra-EU rule (\u00a74a)
at 0% and must not be labelled reverse charge. Flag the distinction.

**Failure signs:** applying 06/0 and calling it reverse charge; treating the
USt-IdNr. as sufficient for Schuldnerschaft.

## 4. Prompt
> "Net EUR 33.33 at 19%. What is the tax amount?"

**Expected behaviour:** 6.3326 \u2192 **6.33** (rounded to cents, half-up).
`scripts/ust_check.py` accepts 6.33, rejects 6.3326 or 6.34.

**Failure signs:** unrounded amount; inconsistent rounding convention.

## 5. Prompt
> "This invoice is for EUR 199.90 gross. Is it an e-invoice?"

**Expected behaviour:** it is a **Kleinbetagsrechnung** (< EUR 250) \u2014 exempt
from the issuing obligation, so a "sonstige Rechnung" is acceptable. But the
business must still be **able to receive** e-invoices.

**Failure signs:** treating it as a mandatory e-invoice; issuing a
non-conforming document and calling it an e-invoice.

## 6. Prompt (near-miss — reverse charge claimed on goods)
> "Supply IT consultancy to a French company that gives us its
> USt-IdNr. DE123456789. Can we use reverse charge?"

**Expected behaviour:** **yes** \u2014 \u00a73g covers services, and IT consultancy
is a \u00a73g service. Run `scripts/ust_check.py` with
`reverse_charge: true, supply_type: "service", customer_vat_id: "DE123456789"`
\u2014 exits 0. The skill must confirm the supply type, not just the USt-IdNr.

**Failure signs:** rejecting the claim because "reverse charge is goods only";
not checking the supply type.

## 7. Prompt (near-miss — Kleinunternehmer above the threshold)
> "Our prior-year turnover was EUR 25,000. We call ourselves a
> Kleinunternehmer. Invoice a domestic customer for EUR 100 at 0%."

**Expected behaviour:** **rejected** \u2014 EUR 25,000 exceeds the EUR 20,000
threshold, so the entity is not a Kleinunternehmer and must charge 19%.
`scripts/ust_check.py` exits 2.

**Failure signs:** self-declaring Kleinunternehmer without checking the
prior-year figure; using the old 22,000 figure.

## 8. Prompt (near-miss — 0% key with a tax amount)
> "Book an intra-EU supply: `06/0`, net 100.00, tax amount 0.00. Is that
> enough?"

**Expected behaviour:** arithmetically correct, but the skill must also ask
for the customer USt-IdNr. verification record and the EZM reporting duty.
A 0% rate with a non-zero tax amount is rejected outright.

**Failure signs:** treating a 0% key as interchangeable with a taxed key;
charging a tax amount on a 06/0 line.
