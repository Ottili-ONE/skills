"""Tests for purge_decision.py: permitted/blocked decisions, error paths."""
import json
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "purge_decision.py"
CONFIG = Path(__file__).resolve().parent.parent.parent.parent / "business-de" / "config" / "versions.json"


def run(args):
    r = subprocess.run([sys.executable, str(SCRIPT), *args, "--config", str(CONFIG)],
                       capture_output=True, text=True)
    blob = r.stdout if r.stdout else r.stderr
    return r.returncode, json.loads(blob)


def test_purge_permitted_after_retention_end():
    # 2017 invoice: 8y retention -> end 2025-12-31; today is 2026-10-09 -> permitted
    code, out = run(["--type", "invoice", "--year", "2017",
                     "--approver", "M. Mustermann", "--reason", "Frist abgelaufen"])
    assert code == 0
    assert out["purge_permitted"] is True
    assert out["retention_end"] == "2025-12-31"
    assert out["blocking_conditions"]["retention_end_reached"] is True


def test_purge_blocked_before_retention_end():
    code, out = run(["--type", "invoice", "--year", "2020",
                     "--approver", "M. Mustermann", "--reason", "x"])
    assert code == 1
    assert out["purge_permitted"] is False
    assert out["blocking_conditions"]["retention_end_reached"] is False


def test_purge_blocked_by_open_audit():
    code, out = run(["--type", "invoice", "--year", "2017",
                     "--approver", "M. Mustermann", "--reason", "x",
                     "--open-audit"])
    assert code == 1
    assert out["purge_permitted"] is False
    assert out["blocking_conditions"]["no_open_audit"] is False


def test_unknown_type_errors():
    code, out = run(["--type", "banana", "--year", "2017",
                     "--approver", "M. Mustermann", "--reason", "x"])
    assert code == 2
    assert "unknown document type" in out["error"]


def test_missing_approver_errors():
    code, out = run(["--type", "invoice", "--year", "2017",
                     "--approver", "   ", "--reason", "x"])
    assert code == 2
    assert "approver" in out["error"]


def test_writes_record(tmp_path):
    out_file = tmp_path / "purge.json"
    code, _ = run(["--type", "invoice", "--year", "2017",
                   "--approver", "M. Mustermann", "--reason", "x",
                   "--out", str(out_file)])
    assert code == 0
    rec = json.loads(out_file.read_text(encoding="utf-8"))
    assert rec["purge_permitted"] is True
    assert "record_retention_until" in rec
