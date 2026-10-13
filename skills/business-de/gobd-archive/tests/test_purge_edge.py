"""Edge cases for purge_decision.py: audit-open gate, pre-2025 retention, validation."""
import json
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "purge_decision.py"


def run(*args):
    r = subprocess.run([sys.executable, str(SCRIPT), *args],
                       capture_output=True, text=True)
    return r.returncode, r.stdout, r.stderr


def test_purge_blocked_during_open_audit(tmp_path):
    # a 2017 voucher: retention ended 2025-12-31, but an audit is open -> blocked
    code, out, _ = run("--type", "invoice", "--year", "2017",
                       "--approver", "M. Mustermann", "--reason", "elapsed",
                       "--open-audit")
    assert code == 1
    d = json.loads(out)
    assert d["purge_permitted"] is False
    assert d["blocking_conditions"]["no_open_audit"] is False
    assert d["record_retention_until"] == "2025-12-31"


def test_purge_blocked_before_retention_end():
    # a 2020 voucher: retention ends 2028-12-31, today is before -> blocked
    code, out, _ = run("--type", "voucher", "--year", "2020",
                       "--approver", "M. Mustermann", "--reason", "elapsed")
    assert code == 1
    d = json.loads(out)
    assert d["purge_permitted"] is False
    assert d["blocking_conditions"]["retention_end_reached"] is False


def test_purge_rejects_unknown_type():
    code, _, err = run("--type", "crypto-wallet", "--year", "2020",
                       "--approver", "M. Mustermann", "--reason", "x")
    assert code == 2
    assert "unknown document type" in err


def test_purge_rejects_empty_approver():
    code, _, err = run("--type", "invoice", "--year", "2017",
                       "--approver", "   ", "--reason", "x")
    assert code == 2
    assert "approver" in err


def test_purge_record_kept_for_full_retention(tmp_path):
    out = tmp_path / "purge.json"
    code, _, _ = run("--type", "contract", "--year", "2018",
                     "--approver", "M. Mustermann",
                     "--reason", "Retention 2024-12-31 elapsed",
                     "--out", str(out))
    assert code in (0, 1)
    rec = json.loads(out.read_text())
    # a 2018 contract (6y) ends 2024-12-31; the purge record is kept until then
    assert rec["record_retention_until"] == "2024-12-31"
    assert rec["retention_years"] == 6
