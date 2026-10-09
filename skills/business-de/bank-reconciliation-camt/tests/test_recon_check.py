import json, subprocess, sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "recon_check.py"
TMP = Path(__file__).resolve().parent / "tmp"
TMP.mkdir(exist_ok=True)


def run(data):
    p = TMP / "r.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    return subprocess.run([sys.executable, str(SCRIPT), str(p)], capture_output=True, text=True)


def test_balanced():
    r = run({"account": "DE89", "opening": 100.0, "closing": 200.0,
             "open_items": [{"id": "INV-001", "amount": 100.0}],
             "entries": [{"amount": 100.0, "reference": "A", "date": "2026-10-09",
                          "matched": True, "open_item_id": "INV-001"}]})
    assert r.returncode == 0, r.stderr


def test_unbalanced():
    r = run({"account": "DE89", "opening": 100.0, "closing": 201.0,
             "entries": [{"amount": 100.0, "reference": "A", "date": "2026-10-09", "matched": True}]})
    assert r.returncode == 2


def test_duplicate():
    r = run({"account": "DE89", "opening": 0.0, "closing": 200.0,
             "entries": [{"amount": 100.0, "reference": "A", "date": "2026-10-09", "matched": True},
                         {"amount": 100.0, "reference": "A", "date": "2026-10-09", "matched": True}]})
    assert r.returncode == 2


def test_unallocated():
    r = run({"account": "DE89", "opening": 0.0, "closing": 100.0,
             "entries": [{"amount": 100.0, "reference": "A", "date": "2026-10-09"}]})
    assert r.returncode == 2


def test_unallocated_with_reason():
    r = run({"account": "DE89", "opening": 0.0, "closing": 100.0,
             "entries": [{"amount": 100.0, "reference": "A", "date": "2026-10-09",
                          "matched": False, "reason_code": "UNALLOCATED"}]})
    assert r.returncode == 0, r.stderr


def test_matched_without_open_item_id_rejected():
    r = run({"account": "DE89", "opening": 100.0, "closing": 200.0,
             "entries": [{"amount": 100.0, "reference": "A", "date": "2026-10-09",
                          "matched": True}]})
    assert r.returncode == 2 and "open_item_id" in r.stderr


def test_matched_with_unknown_open_item_id_rejected():
    r = run({"account": "DE89", "opening": 100.0, "closing": 200.0,
             "open_items": [{"id": "INV-001", "amount": 100.0}],
             "entries": [{"amount": 100.0, "reference": "A", "date": "2026-10-09",
                          "matched": True, "open_item_id": "INV-999"}]})
    assert r.returncode == 2 and "not in open_items" in r.stderr


def test_unknown_reason_code_rejected():
    r = run({"account": "DE89", "opening": 0.0, "closing": 100.0,
             "entries": [{"amount": 100.0, "reference": "A", "date": "2026-10-09",
                          "matched": False, "reason_code": "OPEN"}]})
    assert r.returncode == 2 and "unknown reason_code" in r.stderr


def test_unallocated_total_above_tolerance_needs_reason():
    # 0.02 unallocated, no reason code -> rejected
    r = run({"account": "DE89", "opening": 0.0, "closing": 0.02,
             "entries": [{"amount": 0.02, "reference": "A", "date": "2026-10-09",
                          "matched": False}]})
    assert r.returncode == 2


def test_unallocated_total_above_tolerance_with_reason_ok():
    r = run({"account": "DE89", "opening": 0.0, "closing": 0.02,
             "entries": [{"amount": 0.02, "reference": "A", "date": "2026-10-09",
                          "matched": False, "reason_code": "BANK_FEE"}]})
    assert r.returncode == 0, r.stderr


def test_rounding_difference_tolerated():
    # 0.005 unallocated is below the 0.01 boundary -> rounding, no reason needed
    r = run({"account": "DE89", "opening": 0.0, "closing": 0.0,
             "entries": [{"amount": 0.005, "reference": "A", "date": "2026-10-09",
                          "matched": False, "reason_code": "ROUNDING"}]})
    assert r.returncode == 0, r.stderr
