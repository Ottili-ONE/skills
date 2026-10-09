#!/usr/bin/env python3
"""Generate SKR-compliant journal entries from invoice lines.

Reads tax rates from config/versions.json (never hardcoded). Emits one journal
entry per invoice line with Konto, Betrag, Steuerschluessel, Belegdatum,
Buchungsdatum. Mismatches against the account default are reported as blocking
errors until a human reviewer resolves them.

Usage:
    python3 generate_journal.py --skr 04 --lines inv.json --output journal.json
"""
import argparse
import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))
from common import load_config  # noqa: E402

ACCOUNT_TAX_KEYS = {
    "04": {"4000": "19", "4100": "00", "4200": "00", "4300": "07",
           "8000": "19", "8100": "19", "8200": "19", "8300": "07",
           "8400": "00", "8600": "19", "8900": "19"},
    "03": {"4000": "19", "4100": "00", "4200": "00", "4300": "07",
           "8000": "19", "8100": "19", "8200": "19", "8300": "07",
           "8400": "00", "8600": "19", "8900": "19"},
}

VALID_SIDES = {"S", "H"}
KEY_TO_RATE = {"19": "standard", "07": "reduced", "00": "zero"}


def validate_line(line, rates, skr):
    errors = []
    for field in ("account", "amount", "belegdatum", "tax_key"):
        if field not in line or line[field] in (None, ""):
            errors.append("missing mandatory field '%s'" % field)
            return errors
    if line["side"] not in VALID_SIDES:
        errors.append("side must be S or H, got '%s'" % line["side"])
    if line["account"] not in ACCOUNT_TAX_KEYS.get(skr, {}):
        errors.append("account %s not in SKR%s" % (line["account"], skr))
    beleg = str(line["belegdatum"])
    if len(beleg) != 8 or not beleg.isdigit():
        errors.append("belegdatum must be YYYYMMDD, got '%s'" % beleg)
    if line["tax_key"] not in KEY_TO_RATE:
        errors.append("tax_key must be 19/07/00, got '%s'" % line["tax_key"])
    return errors


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--skr", default="04", choices=["03", "04"])
    ap.add_argument("--lines", required=True, help="JSON file: list of invoice lines")
    ap.add_argument("--output", required=True)
    ap.add_argument("--config", default="config/versions.json")
    args = ap.parse_args()

    pinned = load_config(args.config)["skr-journal-mapping"]
    rates = pinned["ust_rates_2026"]
    lines = json.loads(Path(args.lines).read_text(encoding="utf-8"))

    if not isinstance(lines, list):
        print(json.dumps({"ok": False, "error": "--lines must be a JSON array"},
                         indent=2, ensure_ascii=False))
        return 1

    entries = []
    blocking = []
    for i, line in enumerate(lines):
        errs = validate_line(line, rates, args.skr)
        if errs:
            blocking.append({"index": i, "errors": errs, "line": line})
            continue
        default_key = ACCOUNT_TAX_KEYS[args.skr][line["account"]]
        entry = {
            "konto": line["account"],
            "betrag": line["amount"],
            "seite": line["side"],
            "side": line["side"],
            "steuerschluessel": line["tax_key"],
            "rate_percent": rates[KEY_TO_RATE[line["tax_key"]]],
            "belegdatum": line["belegdatum"],
            "buchungsdatum": line.get("buchungsdatum",
                                      str(date.today().strftime("%Y%m%d"))),
            "buchungstext": line.get("text", ""),
        }
        if line["tax_key"] != default_key:
            entry["tax_key_override"] = {
                "default": default_key,
                "used": line["tax_key"],
                "reason": line.get("override_reason", "unspecified"),
            }
        entries.append(entry)

    result = {
        "ok": len(blocking) == 0,
        "kontenrahmen": "SKR%s" % args.skr,
        "entries": entries,
        "blocking_errors": blocking,
        "rates_from_config": rates,
    }
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(
        json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"ok": result["ok"], "entries": len(entries),
                      "blocking": len(blocking), "output": args.output},
                     indent=2, ensure_ascii=False))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
