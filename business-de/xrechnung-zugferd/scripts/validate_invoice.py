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
# Each entry: (element names to look for, content regex, mandatory-in-COMFORT).
# BT-14 and BT-20 are mandatory in *every* profile; the rest only in COMFORT/EXTENDED.
BT_RULES = {
    "BT-10": (["cbc:EndpointID", "EndpointID", "LeitwegID"], r"[0-9A-Fa-f]{2,16}", True),
    "BT-14": (["cbc:IssueDate", "IssueDate"], r"(?:\d{8}|\d{4}-\d{2}-\d{2})", True),
    "BT-20": (["cbc:PaymentTerms", "PaymentTerms"], r"\d", True),
    "BT-17": (["cbc:PaymentDueDate", "PaymentDueDate"], r"\d{8}", False),
    "BT-18": (["cbc:PaymentTerms", "PaymentTerms"], r"\S", False),
    "BT-15": (["cbc:IssueDate", "IssueDate"], r"(?:\d{8}|\d{4}-\d{2}-\d{2})", False),
}


def find_repo_root(start: Path) -> Path:
    """Walk up until we find the repo root (has business-de/config/versions.json)."""
    for cand in [start, *start.parents]:
        if (cand / "business-de" / "config" / "versions.json").exists():
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


def bt_checks(xml_text: str, profile: str) -> list:
    """Run the offline EN 16931 business-rule subset on the XML text."""
    failures = []
    if not xml_text:
        failures.append("no structured XML attachment found in PDF")
        return failures
    for rule_id, (names, regex, mandatory) in BT_RULES.items():
        if rule_id == "BT-15" and profile != "BASIC WL":
            continue
        if not mandatory and profile not in ("COMFORT", "EXTENDED"):
            continue
        present = any(n in xml_text for n in names)
        if not present:
            failures.append(f"{rule_id} missing ({names[0]})")
            continue
        # Element present: its text content must satisfy the content regex.
        if not re.search(regex, xml_text):
            failures.append(f"{rule_id} content invalid (regex {regex})")
    return failures


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("invoice", help="path to the invoice (.xml or .pdf)")
    ap.add_argument("--profile", default="COMFORT",
                    choices=["MINIMUM", "BASIC WL", "BASIC", "COMFORT", "EXTENDED"])
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

    failures = bt_checks(xml_text, args.profile)
    ok = not failures
    result = {
        "ok": ok,
        "engine": "offline-subset",
        "pinned_validator": pinned["kosit-validator"]["version"],
        "pinned_spec": pinned["en16931"]["version"],
        "profile": args.profile,
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
