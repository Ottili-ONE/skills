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
