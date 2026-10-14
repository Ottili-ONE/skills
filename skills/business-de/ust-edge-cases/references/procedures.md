# ust-edge-cases — procedures and worked examples

Retrieval date: 2026-10-09. Version-sensitive facts are pinned in
`config/versions.json`; re-verify before relying on a fact.

## 1. Reverse charge (§13b UStG) — services only

Applies to supplies of **services** (IT, consulting, construction, and similar)
that the buyer receives from another EU member state. The seller charges 0%
and the buyer self-assesses the VAT debt (Schuldnerschaft / Steuerverrechnung).

Preconditions (all must hold):
1. Buyer holds a valid USt-IdNr. (verify with
   https://ec.europa.eu/taxation_customs/vies/ — record the check date).
2. The supply is a **service** in the §13b list (IT, consulting, construction).
3. The supply is intra-community (service rendered from DE to another EU state).

Tax key: **06/0** (or V091 in some DATEV exports). Tax amount: 0.00.

**Bad example** — claiming reverse charge on goods:
```
S 1200  Bank    100.00  06/0
H 8000  Revenue 100.00  06/0
reverse_charge=true, supply_type=goods
```
§13b covers services, not goods. A goods supply to a customer with a valid
USt-IdNr. is taxed at 0% under the general intra-EU rule (§4a) and must not
be labelled reverse charge. This journal would fail the USt-Anmeldung
plausibility check.

**Good example** — service, valid buyer USt-IdNr.:
```
S 1200  Bank    100.00  06/0
H 8000  Revenue 100.00  06/0
reverse_charge=true, supply_type=service
```
No tax line; the buyer self-assesses in their USt-Anmeldung.

## 2. Kleinunternehmer (§19 UStG)

Prior-year turnover ≤ EUR 20,000 (UStG §19 Abs. 1, 2026 threshold,
read from `config/versions.json`). Cannot reclaim input VAT.
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

## 8. Worked examples — good vs bad

### 8.1 Reverse charge (§13b) on an intra-EU service

**GOOD** — A German GmbH hires a French SaaS provider (B2B, VAT ID present,
service received in Germany). `ust_check.py` reports
`{"treatment": "reverse_charge", "tax_rate": 0, "tax_key": "06",
 "buyer_is_steuerschuldner": true, "evidence": ["buyer_vat_id", "seller_vat_id",
 "service_code"]}`. The invoice shows EUR 1,000.00 gross with EUR 0.00 tax and
the §13b notice. The German GmbH declares the service in the USt-Anmeldung
under the reverse-charge rule.

**BAD** — The agent treats the French SaaS as a standard import and applies
19% German VAT on the net amount. The invoice now over-collects VAT, the
French provider did not charge French VAT (correctly, it is a B2B service), and
the German GmbH has a reverse-charge obligation it never met. The USt-Anmeldung
plausibility check fails because the input-tax claim has no matching
reverse-charge line.

### 8.2 Kleinunternehmen and the e-invoice exemption

**GOOD** — A Kleinunternehmen (§19 UStG, turnover < EUR 220,000) receives an
e-invoice from a B2B supplier. The Kleinunternehmen can **receive** it (since
2025-01-01) but is not required to issue e-invoices itself. `ust_check.py`
reports `{"treatment": "kleinunternehmen", "issue_obligation": false,
"receive_obligation": true}`.

**BAD** — The agent assumes the Kleinunternehmen must issue e-invoices and
rejects its outgoing "sonstige Rechnung". The exemption is real and is in §19,
not a workaround. Rejecting a valid Kleinunternehmen invoice is the wrong
direction of the error.

### 8.3 Rounding

**GOOD** — Line item 33.33 × 19% = 6.3326 → 6.33. Per §23 UStDV the tax amount
per line is rounded to cents (half-up), then the line taxes are summed and
compared to the total. If the total does not match, the largest line is
adjusted by ±0.01. `ust_check.py` reports `{"rounded": [6.33], "total": 19.00,
"adjustment": 0.0}`.

**BAD** — The agent rounds the *net* amount first and then computes tax on the
rounded net. That changes the tax by a cent and breaks the plausibility
check. Round tax per line, never round the net before taxing.
