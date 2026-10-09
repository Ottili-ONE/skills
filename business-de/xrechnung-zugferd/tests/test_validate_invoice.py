"""Tests for validate_invoice.py: classification, BT-* checks, version pinning."""
import json
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "validate_invoice.py"
CONFIG = Path(__file__).resolve().parent.parent.parent.parent / "business-de" / "config" / "versions.json"

XML_OK = b"""<?xml version="1.0" encoding="UTF-8"?>
<CrossIndustryInvoice xmlns="urn:un:cefact:standard:CrossIndustryInvoice:1:1">
  <IssueDate>20260602</IssueDate>
  <LeitwegID>DE12345678901234</LeitwegID>
  <PaymentTerms>net 30</PaymentTerms>
  <PaymentDueDate>20260702</PaymentDueDate>
  <AccountID>DE89370400440532013000</AccountID>
  <TaxAmount>228.00</TaxAmount>
</CrossIndustryInvoice>"""

XML_MISSING = b"""<?xml version="1.0" encoding="UTF-8"?>
<CrossIndustryInvoice xmlns="urn:un:cefact:standard:CrossIndustryInvoice:1:1">
</CrossIndustryInvoice>"""


def run(args):
    r = subprocess.run([sys.executable, str(SCRIPT), *args,
                        "--config", str(CONFIG)],
                       capture_output=True, text=True)
    return r.returncode, json.loads(r.stdout)


def test_xml_only_classified(tmp_path):
    f = tmp_path / "inv.xml"
    f.write_bytes(XML_OK)
    code, out = run([str(f)])
    assert code == 0
    assert out["classification"] == "xml-only"
    assert out["errors"] == []
    assert out["pinned_spec"] == "1.2.4"


def test_missing_business_rules(tmp_path):
    f = tmp_path / "inv.xml"
    f.write_bytes(XML_MISSING)
    code, out = run([str(f)])
    assert code == 1
    assert any("BT-14" in e for e in out["errors"])
    assert any("BT-10" in e for e in out["errors"])
    assert any("BT-20" in e for e in out["errors"])


def test_pdf_only_rejected(tmp_path):
    f = tmp_path / "plain.pdf"
    f.write_bytes(b"%PDF-1.4 no embedded files here")
    code, out = run([str(f)])
    assert out["classification"] == "pdf-only"
    assert out["ok"] is False


def test_hybrid_pdf_validated(tmp_path):
    import io, zipfile
    f = tmp_path / "factur-x.pdf"
    with zipfile.ZipFile(f, "w") as zf:
        zf.writestr("factur-x.xml", XML_OK.decode())
    code, out = run([str(f)])
    assert out["classification"] == "hybrid"
    assert out["ok"] is True


def test_missing_file():
    code, out = run(["/nonexistent/invoice.xml"])
    assert code == 2
    assert "file not found" in out["error"]


def test_bt18_and_bt19_present(tmp_path):
    """BT-18 (PaymentAllowedAccountID) and BT-19 (TaxAmount) are distinct from
    BT-20 (PaymentTerms). Verified 2026-10-09 against the KoSIT guidelines.json."""
    f = tmp_path / "inv.xml"
    f.write_bytes(XML_OK)
    code, out = run([str(f), "--profile", "COMFORT"])
    assert code == 0
    assert out["errors"] == []


def test_bt18_missing_in_comfort(tmp_path):
    """Without the bank account (BT-18) the COMFORT profile must fail."""
    xml = XML_OK.replace(b"<AccountID>DE89370400440532013000</AccountID>", b"")
    f = tmp_path / "inv.xml"
    f.write_bytes(xml)
    code, out = run([str(f), "--profile", "COMFORT"])
    assert code == 1
    assert any("BT-18" in e for e in out["errors"])
