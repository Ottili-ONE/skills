"""Tests for profile_selector.py and retention_check.py."""
import json
import subprocess
import sys
import zipfile
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
CONFIG = Path(__file__).resolve().parent.parent / "config" / "versions.json"


def run(script, *args):
    r = subprocess.run([sys.executable, str(SCRIPTS / script), *args],
                       capture_output=True, text=True)
    return r.returncode, r.stdout, r.stderr


def test_profile_b2b_comfort():
    code, out, _ = run("profile_selector.py", "--context", "b2b", "--data", "full",
                       "--recipient", "factur-x")
    assert code == 0, _
    d = json.loads(out)
    assert d["recommended_profile"] == "COMFORT"
    assert d["missing_fields"] == []
    assert d["pinned_spec"] == "1.2.4"


def test_profile_b2c_minimum_lists_comfort_fields():
    code, out, _ = run("profile_selector.py", "--context", "b2c", "--data", "minimal",
                       "--recipient", "any")
    assert code == 0
    d = json.loads(out)
    assert d["recommended_profile"] == "MINIMUM"
    assert any("BT-10" in f for f in d["missing_fields"])


def test_profile_unknown_recipient_falls_back(tmp_path):
    # recipient not in choices -> argparse error, not a crash
    code, _, err = run("profile_selector.py", "--context", "b2b", "--data", "full",
                       "--recipient", "bogus")
    assert code != 0
    assert "invalid choice" in err.lower() or "bogus" in err


def test_retention_check_passes_on_hybrid(tmp_path):
    xml = (b'<?xml version="1.0"?><CrossIndustryInvoice xmlns="urn:un:cefact:standard:CrossIndustryInvoice:1:1">'
           b'<IssueDate>20260602</IssueDate></CrossIndustryInvoice>')
    pdf = tmp_path / "inv.pdf"
    with zipfile.ZipFile(pdf, "w") as zf:
        zf.writestr("factur-x.xml", xml)
        # PDF/A-3 hybrid marker: the /EmbeddedFiles name appears in the PDF catalog
        zf.writestr("catalog.txt", b" /EmbeddedFiles /Names << /Names [ (factur-x.xml) ] >> ")
    code, out, _ = run("retention_check.py", "--archive", str(tmp_path))
    assert code == 0
    d = json.loads(out)
    assert d["retention_end"] == "2034-12-31"
    assert d["files"][0]["parses"] is True


def test_retention_check_fails_on_print_pdf(tmp_path):
    # a print-to-PDF drops the structured XML attachment -> not a valid artefact
    (tmp_path / "paper.pdf").write_bytes(b"%PDF-1.4 not an archive")
    code, out, _ = run("retention_check.py", "--archive", str(tmp_path))
    assert code == 1
    d = json.loads(out)
    assert d["files"][0]["parses"] is False
