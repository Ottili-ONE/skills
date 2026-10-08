#!/usr/bin/env python3
"""Validate a gzip WARC 1.1 file for mandatory header fields. Offline.

Machine-readable summary (counts) -> stdout; human detail (FAIL:/PASS:/WARN:/INFO:)
-> stderr. Exit 0 = all records valid; exit 1 = any FAIL.

Usage:
  python3 validate_warc.py out.warc.gz
"""
import argparse
import gzip
import re
import sys

RECORD_SEP = b"\r\n\r\n"
MANDATORY = ["WARC-Type", "WARC-Record-ID", "WARC-Date", "WARC-Target-URI",
             "Content-Length", "WARC-Payload-Digest"]
VALID_TYPES = {"warcinfo", "response", "resource", "request", "metadata",
               "revisit", "conversion", "continuation"}
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
RECORD_ID_RE = re.compile(r"^<urn:uuid:[0-9a-fA-F-]+>$")


def parse_records(data: bytes):
    """Yield raw record bytes (header + block)."""
    start = 0
    while True:
        idx = data.find(RECORD_SEP, start)
        if idx == -1:
            break
        # A record starts with "WARC/1.1"; skip the version line.
        rec_start = data.find(b"WARC/1.1", start)
        if rec_start == -1 or rec_start > idx:
            break
        yield data[rec_start:idx]
        start = idx + len(RECORD_SEP)


def parse_headers(rec: bytes) -> dict:
    text = rec.decode("utf-8", errors="replace")
    lines = text.split("\r\n")
    headers = {}
    # First line is "WARC/1.1"; skip it.
    for line in lines[1:]:
        if not line:
            break
        if ":" in line:
            k, _, v = line.partition(":")
            headers[k.strip()] = v.strip()
    return headers


def _read_all_members(path: str) -> bytes:
    """Concatenate the payload of every gzip member in the file.

    A WARC written by appending one gzip member per record is N members, but
    `gzip.open(...).read()` returns only the FIRST member's payload. Reading a
    3-record WARC that way silently reports 1 record (verified live 2026-10-08),
    which would make the validator PASS a corrupt file. Walk members until EOF.
    """
    out = bytearray()
    with open(path, "rb") as fh:
        while True:
            with gzip.GzipFile(fileobj=fh, mode="rb") as gz:
                out += gz.read()
            peek = fh.read(2)
            if peek != b"\x1f\x8b":
                break
            fh.seek(-2, 1)
    return bytes(out)


def validate(path: str) -> tuple[int, int, list[str]]:
    data = _read_all_members(path)
    records = list(parse_records(data))
    fails = []
    for i, rec in enumerate(records):
        h = parse_headers(rec)
        for field in MANDATORY:
            if field not in h or not h[field]:
                fails.append(f"record {i}: missing/empty {field}")
        if "WARC-Type" in h and h["WARC-Type"] not in VALID_TYPES:
            fails.append(f"record {i}: unknown WARC-Type {h['WARC-Type']}")
        if "WARC-Date" in h and not DATE_RE.match(h["WARC-Date"]):
            fails.append(f"record {i}: bad WARC-Date {h['WARC-Date']}")
        if "WARC-Record-ID" in h and not RECORD_ID_RE.match(h["WARC-Record-ID"]):
            fails.append(f"record {i}: bad WARC-Record-ID {h['WARC-Record-ID']}")
        if "Content-Length" in h:
            try:
                cl = int(h["Content-Length"])
                if cl < 0:
                    fails.append(f"record {i}: negative Content-Length")
            except ValueError:
                fails.append(f"record {i}: bad Content-Length {h['Content-Length']}")
        if "WARC-Payload-Digest" in h and not h["WARC-Payload-Digest"].startswith("sha256:"):
            fails.append(f"record {i}: bad digest scheme {h['WARC-Payload-Digest']}")
    return len(records), len(records) - len(fails), fails


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file")
    args = ap.parse_args()
    total, ok, fails = validate(args.file)
    print(f"records={total} valid={ok}")
    for f in fails:
        print(f"FAIL: {f}", file=sys.stderr)
    if not fails:
        print("PASS: all records conform to WARC 1.1 mandatory fields", file=sys.stderr)
        return 0
    print(f"FAIL: {len(fails)} problem(s)", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
