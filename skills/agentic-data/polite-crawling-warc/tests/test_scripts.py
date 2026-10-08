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
