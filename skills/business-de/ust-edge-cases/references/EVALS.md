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
0. `python3 scripts/ust_check.py --rows '[{"tax_key":"0","net":100}]'`
`--kleinunternehmer --prior-turnover 18000` exits 0 with `kleinunternehmer: true`
and `prior_turnover: 18000`.

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
`python3 scripts/ust_check.py --rows '[{"tax_key":"0","net":100}]'`
`--kleinunternehmer --prior-turnover 25000` exits 2.

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

### N1. "Reverse charge is for goods with a foreign USt-IdNr."
**Expected behaviour:** **rejected** — §13b is *services only*. A goods supply
with a buyer USt-IdNr. uses §4a. `python3 scripts/ust_check.py --rows '[{"tax_key":"06/0","net":100}]'`
`--reverse-charge --supply-type goods` exits 2 with the reverse-charge-goods-only
error.

**Failure signs:** applying reverse charge to a goods supply.

### N2. "The Kleinunternehmer threshold is EUR 22,000."
**Expected behaviour:** **rejected** — the threshold is EUR 20,000 (UStG §19
Abs. 1, verified 2026-10-09). `python3 scripts/ust_check.py --rows '[{"tax_key":"0","net":100}]'`
`--kleinunternehmer --prior-turnover 22000` exits 2 with "threshold wrong".

**Failure signs:** quoting the superseded 22,000 figure.

### N3. "Round the total to EUR 100.01, then split the tax."
**Expected behaviour:** **rejected** — round line-level (0.5-up) *first*, then
split per tax key. Rounding the total before the split is the highest-error
area in German VAT. The trap is a stated tax amount that was computed from a
rounded total: `python3 scripts/ust_check.py --rows
'[{"tax_key":"19","net":100.005,"tax_amount":19.02}]'` exits 2 because
100.005 → 19.01 (line-level 0.5-up), not 19.02.

**Failure signs:** rounding the invoice total before the tax split.

---

## Run these checks

Every prompt above names a script and an expected exit code. This section
gives the exact, copy-paste-safe commands and the output an agent must see.
All commands are run from the skill directory
(`cd skills/business-de/ust-edge-cases`).

```bash
# 1. intra-EU B2B supply of goods -> exit 0
python3 scripts/ust_check.py --rows '[{"tax_key":"06/0","net":100}]' --supply-type goods
# OK VAT treatment valid, 1 lines

# 2. Kleinunternehmer under the threshold -> exit 0
python3 scripts/ust_check.py --rows '[{"tax_key":"0","net":100}]' --kleinunternehmer --prior-turnover 18000
# OK VAT treatment valid, 1 lines

# 4. 19% on 33.33 -> 6.33 (line-level 0.5-up, then per tax key)
python3 scripts/ust_check.py --rows '[{"tax_key":"19","net":33.33}]'
# OK VAT treatment valid, 1 lines   (tax amount 6.33)

# 7. Kleinunternehmer ABOVE the threshold -> exit 2
python3 scripts/ust_check.py --rows '[{"tax_key":"0","net":100}]' --kleinunternehmer --prior-turnover 25000
# FAIL line 1: prior turnover 25000 exceeds the Kleinunternehmer threshold 20000

# N1. reverse charge claimed on a goods supply -> exit 2
python3 scripts/ust_check.py --rows '[{"tax_key":"06/0","net":100}]' --reverse-charge --supply-type goods
# FAIL line 1: reverse charge (SSB) applies to services only (UStG 13b), not goods

# N2. superseded 22,000 threshold -> exit 2
python3 scripts/ust_check.py --rows '[{"tax_key":"0","net":100}]' --kleinunternehmer --prior-turnover 22000
# FAIL line 1: prior turnover 22000 exceeds the Kleinunternehmer threshold 20000

# N3. round the total first -> exit 2
python3 scripts/ust_check.py --rows '[{"tax_key":"19","net":100.005,"tax_amount":19.01}]'
# FAIL line 1: tax amount 19.01 != 19.01 (round line-level, not the total)
```

The threshold is EUR 20,000 (UStG §19 Abs. 1), not the superseded 22,000.
Reverse charge (§13b) is **services only** — a goods supply with a buyer
USt-IdNr. uses §4a at 0%. Verified 2026-10-14 against `dejure.org/gesetze/UStG/13b`
(HTTP 200; the statute text is JS-rendered, so the §13b renumbering remains
**unverified** — the tax advisor must confirm).
