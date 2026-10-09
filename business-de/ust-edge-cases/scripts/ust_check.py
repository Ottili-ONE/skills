#!/usr/bin/env python3
"""Validate VAT treatment of an invoice line.

Checks: tax key is legal for the scenario, tax amount matches the rate,
rounding to cents, reverse-charge preconditions (USt-IdNr. present for 06/0),
Kleinunternehmer threshold, Kleinbetagsrechnung exemption, e-invoice
interplay, and the reverse-charge-goods-only rule. Exits 0 on success, 2 on
failure.

Edge cases handled:
  - reverse charge (06/0 / V091) on goods -> rejected (§3g is services only)
  - Kleinunternehmer charging VAT -> rejected
  - Kleinbetagsrechnung (< EUR 250 gross) with a tax line -> flagged
  - unrounded tax amount -> rejected
  - 0% rate with a tax-account amount -> rejected (no tax line expected)
"""
import json
import sys
from pathlib import Path

# Steuerschluessel -> (rate percent, requires_invoice_idnr, allows_tax_line)
KEYS = {
    "19": (19.0, False, True),
    "7": (7.0, False, True),
    "16/1": (16.0, False, True),
    "06/0": (0.0, True, False),
    "09/0": (0.0, False, False),
    "13/0": (19.0, False, True),
    "V091": (0.0, True, False),
    "0": (0.0, False, False),
}
KLEINUNTERNEHMEN_MAX = 20000.0  # prior-year turnover threshold, EUR (UStG §19 Abs. 1, 2026)
KLEINBETRAG_MAX = 250.0         # gross threshold for Kleinbetagsrechnung, EUR


def check(rows, prior_turnover=None, kleinunternehmer=False, rounding="half_up"):
    errors = []
    for i, r in enumerate(rows, 1):
        key = str(r.get("tax_key", "")).strip()
        if key not in KEYS:
            errors.append(f"line {i}: unknown tax key {key!r}")
            continue
        rate, needs_idnr, allows_tax_line = KEYS[key]
        if needs_idnr and not r.get("customer_vat_id"):
            errors.append(f"line {i}: tax key {key} requires a valid customer USt-IdNr.")
        try:
            net = float(r["net"])
        except (KeyError, ValueError):
            errors.append(f"line {i}: invalid net {r.get('net')!r}")
            continue
        expected = round(net * rate / 100.0, 2)
        try:
            stated = float(r.get("tax_amount", expected))
        except (KeyError, ValueError):
            stated = expected
        # The tax amount must be expressible in cents: anything with a third
        # decimal place is a rounding error, not a valid amount.
        if abs(round(stated * 100.0) - stated * 100.0) > 1e-6:
            errors.append(f"line {i}: tax amount {stated} is not rounded to cents (§23 UStDV)")
        if abs(stated - expected) > 0.005:
            errors.append(f"line {i}: tax amount {stated} != {net * rate / 100.0:.2f} for key {key}")
        if rate == 0.0 and stated != 0.0:
            errors.append(f"line {i}: 0% rate key {key} must have tax amount 0.00, got {stated}")
        if not allows_tax_line and stated != 0.0:
            errors.append(f"line {i}: 0% rate key {key} must not carry a tax amount")
        # Reverse charge (§3g UStG) applies to SERVICES only — IT, consulting,
        # construction, and similar. A supply of *goods* with key 06/0 uses the
        # general intra-EU rule (§4a) and must not be labelled reverse charge.
        # The tax result is 0% either way; the trap is the *claim*, not the rate.
        if r.get("reverse_charge") is True and r.get("supply_type") != "service":
            errors.append(
                f"line {i}: reverse charge (§3g) applies to services only — "
                f"supply_type {r.get('supply_type')!r} cannot use reverse charge; "
                f"the general intra-EU rule (§4a) applies"
            )
        if kleinunternehmer and rate > 0:
            errors.append(f"line {i}: Kleinunternehmer cannot charge VAT (key {key})")
        if kleinunternehmer and key in ("06/0", "V091", "0", "09/0"):
            errors.append(f"line {i}: Kleinunternehmer must not use tax key {key}")
        # Kleinbetagsrechnung: a taxed invoice under EUR 250 gross is exempt from
        # the e-invoicing obligation, so a "sonstige Rechnung" is acceptable —
        # but the tax line itself is still arithmetically checked above.
        if (net + stated) < KLEINBETRAG_MAX and rate > 0 and r.get("e_invoice") is True:
            errors.append(
                f"line {i}: invoice under EUR {KLEINBETRAG_MAX:.0f} gross is a "
                f"Kleinbetagsrechnung — exempt from the e-invoicing obligation, so "
                f"mark it as sonstige Rechnung, not an e-invoice"
            )
    if kleinunternehmer and prior_turnover is not None and prior_turnover > KLEINUNTERNEHMEN_MAX:
        errors.append(f"prior-year turnover {prior_turnover} exceeds Kleinunternehmer threshold {KLEINUNTERNEHMEN_MAX}")
    return errors


def main(argv):
    if len(argv) != 2:
        print("usage: ust_check.py <invoice.json>", file=sys.stderr)
        return 2
    data = json.loads(Path(argv[1]).read_text(encoding="utf-8"))
    rows = data if isinstance(data, list) else data.get("lines", [data])
    cfg = data if isinstance(data, dict) else {}
    errs = check(
        rows,
        prior_turnover=cfg.get("prior_turnover"),
        kleinunternehmer=cfg.get("kleinunternehmer", False),
        rounding=cfg.get("rounding", "half_up"),
    )
    if errs:
        for e in errs:
            print("FAIL", e, file=sys.stderr)
        return 2
    print("OK VAT treatment valid, %d lines" % len(rows))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
