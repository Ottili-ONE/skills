# ust-edge-cases — procedures and worked examples

Retrieval date: 2026-10-09. Version-sensitive facts are pinned in
`config/versions.json`; re-verify before relying on a fact.

## 1. Reverse charge (§13b UStG) — goods only

Applies to supplies of **goods** that the buyer resells or processes. The
seller charges 0% and the buyer self-assesses (Steuerverrechnung).

Preconditions (all must hold):
1. Buyer holds a valid USt-IdNr. (verify with
   https://ec.europa.eu/taxation_customs/vies/ — record the check date).
2. The goods are in the §13b list (resalable goods, not services).
3. The supply is intra-community (goods leave DE to another EU state).

Tax key: **06/0** (or V091 in some DATEV exports). Tax amount: 0.00.

**Bad example** — applying reverse charge to services:
```
S 1200  Bank    100.00  06/0
H 8000  Revenue 100.00  06/0
```
Services are **not** §13b; the general place-of-performance rule applies.
This journal would fail the USt-Anmeldung plausibility check.

**Good example** — goods, valid buyer USt-IdNr.:
```
S 1200  Bank    100.00  06/0
H 8000  Revenue 100.00  06/0
```
No tax line; the buyer self-assesses in their USt-Anmeldung.

## 2. Kleinunternehmer (§19 UStG)

Prior-year turnover ≤ EUR 22,000 (2026 threshold). Cannot reclaim input VAT.
Issues **no** e-invoice with a tax line — their invoice is a "sonstige
Rechnung" under §19.

```
S 1200  Bank    119.00  0
H 8000  Revenue 119.00  0
```
The gross amount lands in revenue; no tax line, no 1570 account.

**Pitfall:** a Kleinunternehmer who issues a 19% invoice is committing a
filing error; the USt-Anmeldung must show 0.00.

## 3. Intra-EU B2B (§4a UStG)

Supply of goods to a customer with a valid USt-IdNr. in another EU state.
Tax key **06/0**, 0% rate. The seller must report it in the
Zusammenfassende Meldung (EZM).

## 4. OSS (One Stop Shop)

For EU-wide B2C supplies, the German business registers in its home state
and declares all EU VAT there. Domestic sales still need a German
USt-Anmeldung. Tax key **V091** for the EU leg.

## 5. Rounding (§23 UStDV)

Tax amounts are rounded to **2 decimal places** (cents). Convention:
half-up. Record the convention in the entity's config; the tax authority
accepts banker's rounding in practice, but consistency is what the
plausibility check looks for.

Example: 100.00 × 19% = 19.00; 33.33 × 19% = 6.3326 → 6.33.

## 6. E-invoice interplay

Verified 2026-10-09 against the IHK Chemnitz page
(https://www.ihk.de/chemnitz/e-rechnung, Nr. 5781150):

- The issuing obligation **includes** Umsätze nach §13b UStG
  (reverse charge). A reverse-charge invoice is still an e-invoice — it
  carries the EN 16931 structure with tax amount 0.00 and tax key 06/0.
- **Kleinunternehmen are exempt from issuing** e-invoices (they issue a
  "sonstige Rechnung" under §19). They must still be **able to receive**
  e-invoices since 2025-01-01.
- Kleinbetagsrechnungen (< EUR 250 gross) are also exempt from issuing.

## 7. Verification

Run `scripts/ust_check.py <invoice.json>` — exits 0 on a valid treatment,
2 otherwise.
