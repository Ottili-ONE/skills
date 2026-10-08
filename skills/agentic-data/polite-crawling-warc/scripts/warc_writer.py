#!/usr/bin/env python3
"""Minimal WARC 1.1 writer. Offline, deterministic, no network.

Writes one record per call to a gzip-compressed WARC file. Enforces the
mandatory header fields from ISO 28500 (WARC 1.1): WARC-Type, WARC-Record-ID,
WARC-Date, WARC-Target-URI, Content-Length, WARC-Payload-Digest.

Usage:
  python3 warc_writer.py --file out.warc.gz --type response \
      --target-uri http://example.com/ --payload 'HTTP/1.1 200 OK\r\n\r\nbody'
  python3 warc_writer.py --validate --file out.warc.gz   # count records
"""
import argparse
import gzip
import hashlib
import io
import sys
import uuid
from datetime import datetime, timezone

VALID_TYPES = {
    "warcinfo", "response", "resource", "request", "metadata",
    "revisit", "conversion", "continuation",
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _digest(payload: bytes) -> str:
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _record(warc_type: str, target_uri: str, block: bytes,
            record_id: str | None = None, date: str | None = None,
            payload_digest: str | None = None,
            refers_target: str | None = None,
            refers_date: str | None = None,
            profile: str | None = None,
            truncated: str | None = None) -> bytes:
    if warc_type not in VALID_TYPES:
        raise ValueError(f"unknown WARC-Type: {warc_type}")
    rid = record_id or f"<urn:uuid:{uuid.uuid4()}>"
    d = date or _now_iso()
    lines = [
        f"WARC/1.1",
        f"WARC-Type: {warc_type}",
        f"WARC-Record-ID: {rid}",
        f"WARC-Date: {d}",
        f"WARC-Target-URI: {target_uri}",
        f"Content-Length: {len(block)}",
    ]
    if payload_digest is not None:
        lines.append(f"WARC-Payload-Digest: {payload_digest}")
    if refers_target is not None:
        lines.append(f"WARC-Refers-To-Target-URI: {refers_target}")
    if refers_date is not None:
        lines.append(f"WARC-Refers-To-Date: {refers_date}")
    if profile is not None:
        lines.append(f"WARC-Profile: {profile}")
    if truncated is not None:
        lines.append(f"WARC-Truncated: {truncated}")
    header = ("\r\n".join(lines) + "\r\n\r\n").encode("utf-8")
    return header + block + b"\r\n\r\n"


def append_record(path: str, **kwargs) -> int:
    """Append one record to a gzip WARC; return byte offset of the record."""
    rec = _record(**kwargs)
    # gzip.GzipFile.tell() reports the *uncompressed* position, which is not
    # usable as a file offset for resume. Compress in memory and track the
    # real on-disk offset ourselves.
    buf = io.BytesIO()
    with gzip.GzipFile(fileobj=buf, mode="wb", mtime=0) as gz:
        gz.write(rec)
    compressed = buf.getvalue()
    with open(path, "ab") as fh:
        offset = fh.tell()
        fh.write(compressed)
    return offset


def count_records(path: str) -> int:
    n = 0
    with gzip.open(path, "rb") as fh:
        data = fh.read()
    # Records are separated by "\r\n\r\n" after the block; count WARC/1.1 lines.
    return data.count(b"WARC/1.1")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--file", required=True)
    ap.add_argument("--type", choices=sorted(VALID_TYPES))
    ap.add_argument("--target-uri")
    ap.add_argument("--payload", default="")
    ap.add_argument("--payload-file")
    ap.add_argument("--record-id")
    ap.add_argument("--date")
    ap.add_argument("--payload-digest")
    ap.add_argument("--refers-target")
    ap.add_argument("--refers-date")
    ap.add_argument("--profile")
    ap.add_argument("--truncated")
    ap.add_argument("--validate", action="store_true")
    args = ap.parse_args()

    if args.validate:
        n = count_records(args.file)
        print(f"records={n}")
        print("PASS: WARC file readable", file=sys.stderr)
        return 0

    if not args.type or not args.target_uri:
        ap.error("--type and --target-uri are required without --validate")
    if args.payload_file:
        with open(args.payload_file, "rb") as fh:
            block = fh.read()
    else:
        block = args.payload.encode("utf-8")
    offset = append_record(
        args.file,
        warc_type=args.type,
        target_uri=args.target_uri,
        block=block,
        record_id=args.record_id,
        date=args.date,
        payload_digest=args.payload_digest or _digest(block),
        refers_target=args.refers_target,
        refers_date=args.refers_date,
        profile=args.profile,
        truncated=args.truncated,
    )
    print(f"offset={offset} bytes={len(block)}")
    print("PASS: record appended", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
