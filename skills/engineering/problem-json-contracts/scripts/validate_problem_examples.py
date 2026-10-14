#!/usr/bin/env python3
"""Offline RFC 9457 shape validator for problem+json examples.

Validates every *.example.json under --schema-dir against the rules in
references/problem-procedure.md (RFC 9457, 2023):

  * `type` is an absolute URI or an `about:` URI (never a bare string / relative URI)
  * `title` is a string <= 120 chars
  * `status` is an int and equals the HTTP status from the catalogue (or filename)
  * `detail` is a string <= 500 chars
  * `instance` is a string
  * 5xx responses carry `trace_id` and NO stack trace / connection string / SQL
  * `retry_after`, if present, is a positive integer (never an HTTP-date)
  * no envelope: the JSON object must not nest a `status` inside another object

Exit 0 all pass, 1 findings, 2 usage error.
"""
import argparse, json, os, re, sys

try:
    import yaml
except Exception:
    yaml = None

FORBIDDEN = re.compile(
    r"(stack[-_ ]?trace|connection[-_ ]?string|password|secret|BEGIN RSA|SELECT\b|"
    r"postgresql://|mysql://|jdbc:|aws_access_key)", re.I)


def load_catalogue(path):
    """Return {code: status} from a catalogue YAML/JSON file (comments allowed)."""
    if not path or not os.path.isfile(path):
        return {}
    txt = open(path, encoding="utf-8").read()
    is_yaml = path.endswith((".yaml", ".yml")) or "codes:" in txt.splitlines()[0:2]
    if is_yaml:
        if yaml is None:
            print("warning: PyYAML unavailable, catalogue not loaded", file=sys.stderr)
            return {}
        data = yaml.safe_load(txt)
    else:
        cleaned = "\n".join(
            ln for ln in txt.splitlines() if not ln.lstrip().startswith("#"))
        data = json.loads(cleaned)
    codes = data.get("codes", data) if isinstance(data, dict) else {}
    out = {}
    for code, spec in codes.items():
        if isinstance(spec, dict) and "status" in spec:
            out[code] = spec["status"]
    return out


def validate(obj, http_status, label):
    findings = []
    if not isinstance(obj, dict):
        findings.append(f"{label}: not a JSON object")
        return findings
    t = obj.get("type")
    if not isinstance(t, str) or not t:
        findings.append(f"{label}: missing `type`")
    elif not re.match(r"^(https?://|about:|urn:)", t):
        findings.append(f"{label}: `type` {t!r} is not an absolute/about/urn URI")
    title = obj.get("title")
    if not isinstance(title, str) or not title:
        findings.append(f"{label}: missing `title`")
    elif len(title) > 120:
        findings.append(f"{label}: `title` {len(title)} chars > 120")
    status = obj.get("status")
    if not isinstance(status, int):
        findings.append(f"{label}: `status` missing or not an int")
    elif status != http_status:
        findings.append(f"{label}: `status` {status} != HTTP {http_status}")
    detail = obj.get("detail")
    if not isinstance(detail, str) or not detail:
        findings.append(f"{label}: missing `detail`")
    elif len(detail) > 500:
        findings.append(f"{label}: `detail` {len(detail)} chars > 500")
    if not isinstance(obj.get("instance"), str) or not obj.get("instance"):
        findings.append(f"{label}: missing `instance`")
    for k, v in obj.items():
        if isinstance(v, dict) and "status" in v:
            findings.append(f"{label}: envelope detected - nested `status` under `{k}`")
    if isinstance(status, int) and status >= 500:
        if "trace_id" not in obj:
            findings.append(f"{label}: 5xx missing `trace_id`")
        if FORBIDDEN.search(json.dumps(obj)):
            findings.append(f"{label}: 5xx leaks internals (stack trace / connection string / SQL)")
    ra = obj.get("retry_after")
    if ra is not None:
        if not isinstance(ra, int) or ra <= 0:
            findings.append(f"{label}: `retry_after` {ra!r} must be a positive integer, not HTTP-date")
    return findings


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--schema-dir", required=True)
    ap.add_argument("--catalogue", default=None,
                    help="catalogue YAML/JSON used to look up the expected status by code")
    args = ap.parse_args()
    if not os.path.isdir(args.schema_dir):
        print(f"not a directory: {args.schema_dir}", file=sys.stderr)
        return 2
    cat = load_catalogue(args.catalogue)
    findings = []
    files = sorted(f for f in os.listdir(args.schema_dir) if f.endswith(".example.json"))
    if not files:
        print("no .example.json files found")
        return 1
    for fn in files:
        path = os.path.join(args.schema_dir, fn)
        try:
            obj = json.load(open(path, encoding="utf-8"))
        except Exception as e:
            findings.append(f"{fn}: malformed JSON: {e}")
            continue
        m = re.match(r"^(?:.*?[_-])?(\d{3})", fn)
        http = int(m.group(1)) if m else 0
        if http == 0 and cat:
            t = obj.get("type", "")
            code = t.rsplit("/", 1)[-1] if isinstance(t, str) else ""
            http = cat.get(code, 0)
        findings.extend(validate(obj, http, fn))
    if findings:
        print("FINDINGS:")
        for f in findings:
            print("  " + f)
        return 1
    print(f"OK: {len(files)} problem examples validate against RFC 9457 shape")
    return 0


if __name__ == "__main__":
    sys.exit(main())
