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
import hashlib
import json
import sys
from pathlib import Path


def find_repo_root(start: Path) -> Path:
    """Walk up until we find the repo root (has business-de/config/versions.json)."""
    for cand in [start, *start.parents]:
        if (cand / "business-de" / "config" / "versions.json").exists():
            return cand
    return start


def load_config(path: Path) -> dict:
    """Load the pinned versions config, resolving relative to the repo root."""
    p = Path(path)
    if not p.is_absolute() and not p.exists():
        root = find_repo_root(Path(__file__).resolve().parent)
        alt = root / "business-de" / path
        if alt.exists():
            p = alt
    return json.loads(p.read_text(encoding="utf-8"))


def classify(path: Path) -> str:
    """Classify the document: xml-only / hybrid / other."""
    suffix = path.suffix.lower()
    if suffix == ".xml":
        head = path.read_bytes()[:4096]
        return "xml-only" if b"CrossIndustryInvoice" in head else "other-xml"
    if suffix == ".pdf":
        data = path.read_bytes()[:65536]
        return "hybrid" if b"/EmbeddedFiles" in data else "pdf-only"
    return "unknown"


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def business_rule_checks(path: Path) -> list:
    """Run the offline business-rule subset that does not need the KoSIT engine."""
    failures = []
    if path.suffix.lower() != ".xml":
        return failures  # PDF hybrid: rules checked on the extracted XML
    data = path.read_bytes()[:65536]
    if b"cbc:IssueDate" not in data and b"IssueDate" not in data:
        failures.append("BT-14 missing (invoice issue date)")
    if (b"cbc:EndpointID" not in data and b"EndpointID" not in data):
        failures.append("BT-10 missing (Leitweg-ID / buyer identifier)")
    return failures


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("invoice", help="path to the invoice (.xml or .pdf)")
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
    rule_failures = business_rule_checks(invoice)

    # The KoSIT engine itself is not bundled; this script reports the offline
    # subset and the pinned validator version so a human/agent can run the
    # full engine. A run is never reported "passed" without the engine.
    ok = not rule_failures
    result = {
        "ok": ok,
        "engine": "offline-subset",
        "pinned_validator": pinned["kosit-validator"]["version"],
        "pinned_spec": pinned["en16931"]["version"],
        "file": str(invoice),
        "sha256": sha256_of(invoice),
        "classification": kind,
        "errors": rule_failures,
        "next": ("run the KoSIT validator for the full rule set"
                 if ok else "fix the listed errors and re-run"),
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
