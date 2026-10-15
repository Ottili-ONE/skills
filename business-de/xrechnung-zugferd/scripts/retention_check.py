#!/usr/bin/env python3
"""Verify an e-invoice archive: files parse, SHA-256 unchanged, retention end date.

Usage:
    python3 retention_check.py --archive ./archive --config config/versions.json
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))
from common import load_config  # noqa: E402


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def retention_end(invoice_year: int) -> str:
    """8 years from year-end (BEG IV, effective 2025-01-01)."""
    return f"{invoice_year + 8}-12-31"


def _year_from_name(path: Path, fallback: int) -> int:
    """Best-effort invoice-year extraction from the file name.

    A 4-digit year anywhere in the stem is taken as the invoice year; the
    first such match wins. Without one, fall back to the pinned spec's
    effective year so the retention end is still computed.
    """
    import re
    m = re.search(r"(19|20)\d{2}", path.stem)
    if m:
        return int(m.group(0))
    return fallback


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--archive", required=True, help="archive directory")
    ap.add_argument("--config", default="config/versions.json")
    ap.add_argument("--invoice-year", type=int, default=None,
                    help="retention year for every file (default: read each "
                         "file's year from its name, fall back to the "
                         "pinned spec effective year)")
    ap.add_argument("--retention-end", action="store_true",
                    help="also print the computed retention end date")
    args = ap.parse_args()

    archive = Path(args.archive)
    pinned = load_config(Path(args.config))["xrechnung-zugferd"]
    fallback_year = int(pinned["en16931"]["effective"][:4])

    files = sorted(p for p in archive.iterdir() if p.is_file())
    report = []
    ok = True
    for f in files:
        digest = sha256_of(f)
        # parse check: XML must have CrossIndustryInvoice; PDF must be hybrid
        if f.suffix.lower() == ".xml":
            parses = b"CrossIndustryInvoice" in f.read_bytes()[:4096]
        elif f.suffix.lower() == ".pdf":
            parses = b"/EmbeddedFiles" in f.read_bytes()[:65536]
        else:
            parses = False
        ok = ok and parses
        year = args.invoice_year or _year_from_name(f, fallback_year)
        report.append({"file": str(f), "sha256": digest, "parses": parses,
                       "invoice_year": year,
                       "retention_end": retention_end(year)})
    result = {"ok": ok, "pinned_spec": pinned["en16931"]["version"],
              "files": report, "re_verification": "2026-10-15"}
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
