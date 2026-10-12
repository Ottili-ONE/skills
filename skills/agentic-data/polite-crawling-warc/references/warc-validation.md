# WARC validation — polite-crawling-warc

A WARC file that the writer produced and the validator cannot read is the
worst kind of corruption: it looks fine. This page records the validation
contract and the known traps.

## Mandatory fields (WARC 1.1 / ISO 28500)

Every record must carry all of: `WARC-Type`, `WARC-Record-ID`, `WARC-Date`,
`WARC-Target-URI`, `Content-Length`, `WARC-Payload-Digest`.

| Field | Format | Trap |
|-------|--------|------|
| `WARC-Type` | one of warcinfo, response, resource, request, metadata, revisit, conversion, continuation | unknown type -> FAIL |
| `WARC-Record-ID` | `<urn:uuid:<hex>>` | a bare UUID without the urn wrapper is not a valid ID |
| `WARC-Date` | `YYYY-MM-DDTHH:MM:SSZ` | a date with a timezone offset or a space fails the regex |
| `Content-Length` | non-negative int | must equal the byte length of the block |
| `WARC-Payload-Digest` | `sha256:<hex>` | other schemes are not supported by this validator |

## The multi-gzip trap (verified live 2026-10-08)

`warc_writer.py` appends one gzip member per record. `gzip.open(path).read()`
returns **only the first member**. A naive validator reading a 3-record WARC
this way reports `records=1` and **passes**. Both the writer's `count_records`
and the validator's `_read_all_members` walk every member until the gzip magic
`1f 8b` disappears. Always use the member-walking reader; never `gzip.open`.

## Record splitting

Records are split on the marker `WARC/1.1\r\nWARC-Type:`. This is safe because
the writer never emits that byte sequence inside a block. The old
implementation split on the first `\r\n\r\n` after each start — which is the
header/block separator — and yielded one header-only slice per record.

## Revisit records

A `revisit` record carries no payload of its own. Its `WARC-Payload-Digest`
**must** be the digest of the *original* record's payload (IIPC dedup 1.0,
profile `http://netpreserve.org/warc/0.18/revisit/identical-payload-digest`).
The writer refuses to emit a revisit without an explicit `--payload-digest`;
defaulting to the digest of the empty block would produce a record whose digest
matches nothing.

## Validation procedure (ordered)

1. Read every gzip member into one byte buffer.
2. Split on the record marker.
3. For each record, parse headers and check every mandatory field.
4. Verify `WARC-Date` format, `WARC-Record-ID` format, `Content-Length >= 0`,
   digest scheme.
5. Count records and valid records; exit 0 only if valid == total and total > 0.

## Near-miss triggers

- A WARC with zero records -> `records=0`, exit 1 (an empty file is not a valid
  crawl output).
- A `WARC-Date` in local time without `Z` -> passes the human eye, fails the
  regex. Always emit UTC.
- `Content-Length` not matching the actual block -> the file is corrupt or was
  hand-edited. FAIL.
- A revisit with `Content-Length: 0` and no `WARC-Refers-To-Target-URI` -> the
  record cannot be linked to its original. WARN.
