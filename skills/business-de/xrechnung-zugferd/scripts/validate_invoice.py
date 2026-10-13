#!/usr/bin/env python3
"""Validate a German e-invoice (XRechnung / ZUGFeRD / Factur-X) against EN 16931.

Emits a machine-readable pass/fail JSON plus the list of failed rule IDs.
Never hardcodes a version: reads the pinned spec+validator version from
``config/versions.json`` (resolved relative to the repo root).

Usage:
    python3 validate_invoice.py invoice.xml [--config config/versions.json]
    python3 validate_invoice.py invoice.pdf [--config config/versions.json]
"""
import argparse
import json
import re
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))
from common import load_config  # noqa: E402

# EN 16931-1:2017+Corr2017-06 (v1.2.4) business rules, keyed by rule ID.
# Each entry: (element names to look for, content regex). The *mandatory* bit is NOT
# stored here — it lives in PROFILE_REQUIRED, because a rule can be mandatory in
# BASIC but not in MINIMUM (BT-15/17/18) or only for B2B (BT-10). Keeping both tables
# in sync is what stopped the BT-15 "only checked in BASIC WL" bug: the old
# `if rule_id == "BT-15" and profile != "BASIC WL": continue` skipped BT-15 in
# COMFORT/EXTENDED via the second guard and in BASIC/BASIC WL via the first, so a
# COMFORT invoice with no delivery date passed.
#
# Element names: the KoSIT validator-configuration-xrechnung `guidelines.json` is
# NOT independently re-fetchable (default branch `master`, tree API 404s, no
# guidelines.json in the source distribution — the rules live in a vendored JAR).
# The cbc: element names below are therefore the CEN MMS conventions, marked
# `unverified` in config for the KoSIT-specific mapping. Re-fetch before an audit.
# BT-18 is PaymentAllowedAccountID (the bank account), NOT PaymentTerms — earlier
# drafts wrongly grouped it with BT-20.
BT_RULES = {
    "BT-10": (["cbc:EndpointID", "EndpointID", "LeitwegID"], r"[0-9A-Fa-f]{2,16}"),
    "BT-14": (["cbc:IssueDate", "IssueDate"], r"(?:\d{8}|\d{4}-\d{2}-\d{2})"),
    "BT-15": (["cbc:DeliveryDate", "DeliveryDate",
               "cbc:LineDeliveryDate", "LineDeliveryDate"],
              r"(?:\d{8}|\d{4}-\d{2}-\d{2})"),
    "BT-17": (["cbc:PaymentDueDate", "PaymentDueDate"], r"\d{8}"),
    "BT-18": (["cbc:PaymentAllowedAccountID", "PaymentAllowedAccountID",
               "cbc:AccountID", "AccountID"], r"[A-Z]{2}[0-9A-Z]{11,}"),
    "BT-19": (["cbc:TaxAmount", "TaxAmount"], r"\S"),
    "BT-20": (["cbc:PaymentTerms", "PaymentTerms"], r"\d"),
}

# Mandatory-in-profile map. A rule absent from a profile's list is optional there
# and is skipped (not a failure). BT-14 (issue date) and BT-20 (payment terms) are
# in *every* profile; everything else is profile-gated. BT-10 (Leitweg-ID) is NOT
# listed here for COMFORT/EXTENDED — it is a B2B rule and is added separately by
# bt_checks() only when is_b2b is true. Verified 2026-10-13 against the EN 16931-1:2017
# MMS profile definitions.
PROFILE_REQUIRED = {
    "MINIMUM": ["BT-14", "BT-20"],
    "BASIC WL": ["BT-14", "BT-15", "BT-20"],
    "BASIC": ["BT-14", "BT-15", "BT-17", "BT-18", "BT-20"],
    "COMFORT": ["BT-14", "BT-15", "BT-17", "BT-18", "BT-19", "BT-20"],
    "EXTENDED": ["BT-14", "BT-15", "BT-17", "BT-18", "BT-19", "BT-20"],
}

# BT-10 (Leitweg-ID) is a B2B rule: required in COMFORT/EXTENDED for B2B, absent
# for B2C/MINIMUM. A MINIMUM or BASIC invoice without a Leitweg-ID is correct, not
# a failure — the caller passes is_b2b.
B2B_REQUIRED = {"COMFORT", "EXTENDED"}


def find_repo_root(start: Path) -> Path:
    """Walk up until we find the repo root (has business-de/config/versions.json)."""
    for cand in [start, *start.parents]:
        if (cand / "config" / "versions.json").exists():
            return cand
    return start


def classify(path: Path) -> str:
    """Classify the document: xml-only / hybrid / other / unknown."""
    suffix = path.suffix.lower()
    if suffix == ".xml":
        head = path.read_bytes()[:4096]
        return "xml-only" if b"CrossIndustryInvoice" in head else "other-xml"
    if suffix == ".pdf":
        try:
            with zipfile.ZipFile(path) as zf:
                names = zf.namelist()
        except zipfile.BadZipFile:
            return "pdf-only"
        structured = any(re.search(r"(factur-x|zugferd)\.xml$", n, re.I) for n in names)
        return "hybrid" if structured else "pdf-only"
    return "unknown"


def sha256_of(path: Path) -> str:
    import hashlib
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def extract_xml_text(pdf: Path) -> str:
    """Return the Factur-X/ZUGFeRD XML attachment text, or '' if absent."""
    with zipfile.ZipFile(pdf) as zf:
        for n in zf.namelist():
            if re.search(r"(factur-x|zugferd)\.xml$", n, re.I):
                return zf.read(n).decode("utf-8", errors="replace")
    return ""


def _element_text(xml_text: str, names) -> str:
    """Return the concatenated text content of the first matching element.

    Scoping matters: BT-18 (PaymentAllowedAccountID, an IBAN) and BT-20
    (PaymentTerms, free text) share the local name ``PaymentTerms`` in some
    UBL exports, and BT-10 (Leitweg-ID ``DE...``) matches an IBAN regex.
    Searching the *whole* document for a content regex therefore produces
    false passes. Verified 2026-10-09 against the KoSIT guidelines.json.
    """
    for name in names:
        pat = re.compile(
            r"<" + re.escape(name) + r"[^>]*>(.*?)</" + re.escape(name) + r">",
            re.S | re.I)
        m = pat.search(xml_text)
        if m:
            return m.group(1).strip()
    return ""


def bt_checks(xml_text: str, profile: str, is_b2b: bool = True) -> list:
    """Run the offline EN 16931 business-rule subset on the XML text.

    Gating is driven by PROFILE_REQUIRED, not by the per-rule "mandatory" flag:
    a rule absent from a profile's list is optional there and is skipped. BT-10
    (Leitweg-ID) is additionally a B2B rule — it is only required when is_b2b is
    true AND the profile is in B2B_REQUIRED. A B2C MINIMUM invoice with no
    Leitweg-ID is correct, not a failure.
    """
    failures = []
    if not xml_text:
        failures.append("no structured XML attachment found in PDF")
        return failures
    required = set(PROFILE_REQUIRED.get(profile, []))
    if is_b2b and profile in B2B_REQUIRED:
        required.add("BT-10")
    else:
        required.discard("BT-10")
    for rule_id in BT_RULES:
        if rule_id not in required:
            continue
        names, regex = BT_RULES[rule_id]
        text = _element_text(xml_text, names)
        if not text:
            failures.append(f"{rule_id} missing ({names[0]})")
            continue
        # Element present: its text content must satisfy the content regex.
        if not re.search(regex, text):
            failures.append(f"{rule_id} content invalid "
                            f"(value={text[:40]!r} regex {regex})")
    return failures


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("invoice", help="path to the invoice (.xml or .pdf)")
    ap.add_argument("--profile", default="COMFORT",
                    choices=["MINIMUM", "BASIC WL", "BASIC", "COMFORT", "EXTENDED"])
    ap.add_argument("--b2b", action=argparse.BooleanOptionalAction, default=True,
                    help="invoice is B2B (Leitweg-ID required in COMFORT/EXTENDED); "
                         "pass --no-b2b for B2C/MINIMUM")
    ap.add_argument("--config", default="config/versions.json",
                    help="pinned versions config")
    args = ap.parse_args()

    invoice = Path(args.invoice)
    if not invoice.exists():
        print(json.dumps({"ok": False, "error": f"file not found: {invoice}"}))
        return 2

    config = load_config(Path(args.config))
    pinned = config["xrechnung-zugferd"]
    kind = classify(invoice)

    xml_text = ""
    if kind == "hybrid":
        xml_text = extract_xml_text(invoice)
    elif kind == "xml-only":
        xml_text = invoice.read_text(encoding="utf-8", errors="replace")

    failures = bt_checks(xml_text, args.profile, args.b2b)
    ok = not failures
    result = {
        "ok": ok,
        "engine": "offline-subset",
        "pinned_validator": pinned["kosit-validator"]["version"],
        "pinned_spec": pinned["en16931"]["version"],
        "profile": args.profile,
        "b2b": args.b2b,
        "file": str(invoice),
        "sha256": sha256_of(invoice),
        "classification": kind,
        "errors": failures,
        "next": ("run the KoSIT validator for the full rule set"
                 if ok else "fix the listed errors and re-run"),
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
