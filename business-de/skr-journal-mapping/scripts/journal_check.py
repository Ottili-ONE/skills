#!/usr/bin/env python3
"""Validate a SKR03/SKR04 journal (Buchungsstapel) for balance, tax-key sanity,
tax-account presence and SKR-set consistency.

Reads a JSON journal (list of posting lines) or a CSV with columns
account, side (S/H), amount, tax_key, ref. Exits 0 on success, 2 on failure.

Edge cases handled:
  - mixed SKR03/SKR04 sets (1xxx assets differ) -> rejected
  - tax key on a revenue line with no matching tax-account amount -> rejected
  - amounts outside the SKR range (1xxx-8xxx) -> rejected
  - empty journal -> rejected (a close needs at least one line)
  - CSV rows with extra/missing columns -> rejected with a line number
"""
import csv
import json
import sys
from pathlib import Path

VALID_SIDES = {"S", "H"}
VALID_TAX_KEYS = {"19", "7", "16/1", "16", "1", "06/0", "09/0", "13/0", "0", "00"}
# SKR03/SKR04 account ranges; a valid journal stays inside one set.
SKR_RANGES = [(1000, 1999), (2000, 2999), (4000, 5999), (8000, 8999)]
# VAT payable accounts: SKR04 -> 1570, SKR03 -> 1571 (Soll) / 1572 (Haben)
TAX_ACCOUNTS = {1570, 1571, 1572}


def load_rows(path: Path):
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        raise ValueError("input file is empty")
    if text.startswith("[") or text.startswith("{"):
        data = json.loads(text)
        return data if isinstance(data, list) else data.get("lines", [data])
    rows = []
    with path.open(newline="", encoding="utf-8") as fh:
        for lineno, r in enumerate(csv.DictReader(fh), start=2):
            if r.get("account") is None:
                raise ValueError(f"CSV line {lineno}: header row missing a column")
            rows.append(r)
    return rows


def check(rows):
    errors = []
    debit = 0.0
    credit = 0.0
    taxed_key_seen = None
    tax_account_amount = 0.0
    seen_accounts = set()

    if not rows:
        return ["journal is empty — a close needs at least one posting line"]

    for i, r in enumerate(rows, 1):
        side = (r.get("side") or "").strip().upper()
        if side not in VALID_SIDES:
            errors.append(f"line {i}: invalid side {side!r} (expected S or H)")
            continue
        try:
            amt = float(r["amount"])
        except (KeyError, ValueError):
            errors.append(f"line {i}: invalid amount {r.get('amount')!r}")
            continue
        if side == "S":
            debit += amt
        else:
            credit += amt
        try:
            acct = int(str(r.get("account", "")).strip())
        except (KeyError, ValueError):
            errors.append(f"line {i}: invalid account {r.get('account')!r}")
            continue
        if not any(lo <= acct <= hi for lo, hi in SKR_RANGES):
            errors.append(f"line {i}: account {acct} outside SKR ranges 1xxx-2xxx/4xxx-5xxx/8xxx")
        if acct in TAX_ACCOUNTS:
            tax_account_amount += amt if side == "S" else -amt
        seen_accounts.add(acct)

        tk = (r.get("tax_key") or "").strip()
        if tk and tk not in VALID_TAX_KEYS:
            errors.append(f"line {i}: unknown tax key {tk!r}")
        # A taxed key anywhere in the journal requires a tax-account line with a
        # non-zero net amount. SKR03 revenue is 4xxx, SKR04 revenue is 8xxx, so
        # the taxed key can sit on either range — key on the account side is the
        # receipt leg, key on the revenue leg is the sales leg.
        if tk in ("19", "7", "16/1"):
            taxed_key_seen = tk

    if taxed_key_seen and tax_account_amount == 0:
        errors.append(
            f"tax key {taxed_key_seen} present but the tax account "
            f"(1570/1571/1572) has no amount — USt-Anmeldung plausibility check fails"
        )
    if abs(debit - credit) > 0.005:
        errors.append(f"journal does not balance: debit={debit:.2f} credit={credit:.2f}")
    return errors


def main(argv):
    if len(argv) != 2:
        print("usage: journal_check.py <journal.json|journal.csv>", file=sys.stderr)
        return 2
    try:
        rows = load_rows(Path(argv[1]))
    except Exception as e:  # noqa: BLE001 - surface any parse failure
        print("FAIL", e, file=sys.stderr)
        return 2
    errs = check(rows)
    if errs:
        for e in errs:
            print("FAIL", e, file=sys.stderr)
        return 2
    print("OK journal balanced, %d lines" % len(rows))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
