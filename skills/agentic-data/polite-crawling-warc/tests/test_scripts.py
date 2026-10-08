"""Tests for polite-crawling-warc scripts."""
import gzip
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ROBOTS = ROOT / "scripts" / "robots.py"
WRITER = ROOT / "scripts" / "warc_writer.py"


def run(script, args, stdin=None):
    return subprocess.run(
        [sys.executable, str(script), *args],
        input=stdin, capture_output=True, text=True,
    )


def test_robots_allow_specific_overrides_disallow():
    text = "User-agent: *\nDisallow: /private/\nAllow: /public/\n"
    p = run(ROBOTS, ["--path", "/public/x"], stdin=text)
    assert p.returncode == 0, p.stderr
    assert "allowed=true" in p.stdout


def test_robots_disallowed():
    text = "User-agent: *\nDisallow: /private/\n"
    p = run(ROBOTS, ["--path", "/private/x"], stdin=text)
    assert p.returncode == 1, p.stderr
    assert "allowed=false" in p.stdout


def test_robots_empty_disallow_allows_all():
    text = "User-agent: *\nDisallow:\n"
    p = run(ROBOTS, ["--path", "/anything"], stdin=text)
    assert p.returncode == 0, p.stderr


def test_robots_default_deny_on_unparseable():
    p = run(ROBOTS, ["--path", "/x"], stdin="")
    assert p.returncode == 1


def test_warc_writer_roundtrip():
    with tempfile.TemporaryDirectory() as d:
        f = os.path.join(d, "out.warc.gz")
        p = run(WRITER, ["--file", f, "--type", "response",
                         "--target-uri", "http://example.com/", "--payload", "body"])
        assert p.returncode == 0, p.stderr
        p2 = run(WRITER, ["--file", f, "--validate"])
        assert p2.returncode == 0, p2.stderr
        assert "records=1" in p2.stdout
        with gzip.open(f, "rb") as fh:
            data = fh.read()
        assert b"WARC/1.1" in data
        assert b"WARC-Record-ID:" in data
        assert b"WARC-Date:" in data
        assert b"WARC-Payload-Digest: sha256:" in data
        assert b"Content-Length: 4" in data


def test_warc_writer_revisit_no_block():
    with tempfile.TemporaryDirectory() as d:
        f = os.path.join(d, "out.warc.gz")
        p = run(WRITER, ["--file", f, "--type", "revisit",
                         "--target-uri", "http://example.com/x",
                         "--payload", "",
                         "--payload-digest", "sha256:abc123",
                         "--profile", "http://netpreserve.org/warc/0.18/revisit/identical-payload-digest",
                         "--refers-target", "http://example.com/x"])
        assert p.returncode == 0, p.stderr
        with gzip.open(f, "rb") as fh:
            data = fh.read()
        assert b"WARC-Profile: http://netpreserve.org/warc/0.18/revisit/identical-payload-digest" in data
        assert b"WARC-Refers-To-Target-URI: http://example.com/x" in data
        assert b"Content-Length: 0" in data


def test_robots_prefix_match():
    text = "User-agent: *\nDisallow: /private/\n"
    p = run(ROBOTS, ["--path", "/private/secret"], stdin=text)
    assert p.returncode == 1, p.stderr


def test_robots_wildcard():
    text = "User-agent: *\nDisallow: *.gif$\n"
    p = run(ROBOTS, ["--path", "/img/logo.gif"], stdin=text)
    assert p.returncode == 1, p.stderr
    p2 = run(ROBOTS, ["--path", "/img/logo.png"], stdin=text)
    assert p2.returncode == 0, p2.stderr


def test_robots_most_specific_wins():
    text = "User-agent: *\nDisallow: /\nAllow: /public/\n"
    p = run(ROBOTS, ["--path", "/public/page"], stdin=text)
    assert p.returncode == 0, p.stderr
    p2 = run(ROBOTS, ["--path", "/private/page"], stdin=text)
    assert p2.returncode == 1, p2.stderr


def test_validate_warc_ok_and_bad():
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        f = os.path.join(d, "ok.warc.gz")
        run(WRITER, ["--file", f, "--type", "response",
                     "--target-uri", "http://example.com/", "--payload", "body"])
        p = run(Path(ROOT, "scripts", "validate_warc.py"), [f])
        assert p.returncode == 0, p.stderr
        assert "records=1 valid=1" in p.stdout
        # Bad: missing WARC-Payload-Digest on a revisit record.
        bad = os.path.join(d, "bad.warc.gz")
        run(WRITER, ["--file", bad, "--type", "revisit",
                     "--target-uri", "http://example.com/x", "--payload", ""])
        # remove the digest line by writing a hand-crafted bad file instead
        import gzip as gz
        raw = (b"WARC/1.1\r\nWARC-Type: response\r\nWARC-Record-ID: <urn:uuid:x>\r\n"
               b"WARC-Date: 2026-10-08T12:00:00Z\r\nWARC-Target-URI: http://e/\r\n"
               b"Content-Length: 0\r\n\r\n\r\n\r\n")
        with gz.open(bad, "wb") as fh:
            fh.write(raw)
        p2 = run(Path(ROOT, "scripts", "validate_warc.py"), [bad])
        assert p2.returncode == 1, p2.stderr
        assert "missing/empty WARC-Payload-Digest" in p2.stderr


def test_robots_status_4xx_allows():
    text = "User-agent: *\nDisallow: /\n"
    p = run(ROBOTS, ["--path", "/x", "--status", "404"], stdin=text)
    assert p.returncode == 0, p.stderr
    assert "status_decision=true" in p.stdout


def test_robots_status_5xx_denies():
    text = "User-agent: *\nDisallow: /\n"
    p = run(ROBOTS, ["--path", "/x", "--status", "503"], stdin=text)
    assert p.returncode == 1, p.stderr
    assert "status_decision=false" in p.stdout
    assert "default-deny" in p.stderr


def test_robots_status_500_denies():
    p = run(ROBOTS, ["--path", "/x", "--status", "500"], stdin="User-agent: *\nDisallow: /\n")
    assert p.returncode == 1, p.stderr
    assert "status_decision=false" in p.stdout


def test_rate_limiter_runs():
    p = run(Path(ROOT, "scripts", "rate_limit.py"), ["--crawl-delay", "0.05", "--once"])
    assert p.returncode == 0, p.stderr
    assert "rate=" in p.stdout


def test_resume_state_roundtrip():
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        st = os.path.join(d, "s.json")
        p = run(Path(ROOT, "scripts", "resume_state.py"), ["--state", st, "--add", "http://x", "--offset", "42"])
        assert p.returncode == 0, p.stderr
        p2 = run(Path(ROOT, "scripts", "resume_state.py"), ["--state", st, "--load"])
        assert p2.returncode == 0, p2.stderr
        assert "http://x" in p2.stdout
        assert '"offset": 42' in p2.stdout
        p3 = run(Path(ROOT, "scripts", "resume_state.py"), ["--state", st, "--skip", "http://x"])
        assert p3.returncode == 0, p3.stderr
        p4 = run(Path(ROOT, "scripts", "resume_state.py"), ["--state", st, "--load"])
        assert p4.returncode == 0, p4.stderr
        assert '"queue": []' in p4.stdout


def test_warc_writer_revisit_requires_digest():
    """A revisit record without --payload-digest must fail: the empty-block
    digest is not the original record's digest, so emitting it would be
    non-conformant (IIPC dedup 1.0 identical-payload-digest profile)."""
    import tempfile, os
    with tempfile.TemporaryDirectory() as d:
        f = os.path.join(d, "out.warc.gz")
        p = run(WRITER, ["--file", f, "--type", "revisit",
                         "--target-uri", "http://example.com/x", "--payload", ""])
        assert p.returncode == 1, p.stderr
        assert "payload-digest" in p.stderr


def test_robots_oversize_truncates_not_denies():
    """RFC 9309 §2.5/§2.3.1.5: an oversized robots.txt is truncated to the
    500 KiB cap and the parseable rules inside the window are used. It must
    NOT be rejected wholesale (which would default-deny a site whose rules
    live in the first 500 KiB)."""
    import tempfile, os
    with tempfile.NamedTemporaryFile("wb", suffix=".txt", delete=False) as fh:
        fh.write(b"User-agent: *\nDisallow: /secret/\n")
        fh.write(b"# " + b"x" * (2 * 1024 * 1024))
        path = fh.name
    try:
        p1 = run(ROBOTS, ["--file", path, "--path", "/secret/x"], stdin=None)
        assert p1.returncode == 1, p1.stderr
        assert "allowed=false" in p1.stdout
        assert "cap" in p1.stderr.lower()
        p2 = run(ROBOTS, ["--file", path, "--path", "/public/x"], stdin=None)
        assert p2.returncode == 0, p2.stderr
        assert "allowed=true" in p2.stdout
    finally:
        os.unlink(path)


def test_warc_count_records_across_members():
    """A WARC written by appending one gzip member per record is N members, but
    gzip.open().read() returns only the first member. The counter must walk all
    members or it reports 1 record for a 2-record file."""
    import tempfile, os
    with tempfile.TemporaryDirectory() as d:
        f = os.path.join(d, "out.warc.gz")
        run(WRITER, ["--file", f, "--type", "response",
                     "--target-uri", "http://example.com/a", "--payload", "aaa"])
        run(WRITER, ["--file", f, "--type", "response",
                     "--target-uri", "http://example.com/b", "--payload", "bbb"])
        run(WRITER, ["--file", f, "--type", "response",
                     "--target-uri", "http://example.com/c", "--payload", "ccc"])
        p = run(Path(ROOT, "scripts", "validate_warc.py"), [f])
        assert p.returncode == 0, p.stderr
        assert "records=3 valid=3" in p.stdout, p.stdout
