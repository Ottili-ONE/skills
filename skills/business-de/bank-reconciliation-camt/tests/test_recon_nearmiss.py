"""Near-miss trigger tests for recon_check.py.

The traps: the strict duplicate rule (amount + reference + value date),
the "amount alone" allocation trap, and the unallocated-difference gate.
"""
import json
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "recon_check.py"
TMP = Path(__file__).resolve().parent / "tmp"
TMP.mkdir(exist_ok=True)


def run(data):
    p = TMP / "nearmiss.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    r = subprocess.run([sys.executable, str(SCRIPT), str(p)],
                       capture_output=True, text=True)
    return r.returncode, r.stderr


def test_duplicate_strict_rule_blocks():
    """A duplicate needs amount + reference + value date. Two entries that
    share amount and reference but differ in value date are NOT duplicates
    under the strict rule."""
    rc, err = run({"account": "DE89", "opening": 0.0, "closing": 200.0,
                   "entries": [
                       {"amount": 100.0, "reference": "A", "date": "2026-10-09",
                        "matched": True, "open_item_id": "INV-001"},
                       {"amount": 100.0, "reference": "A", "date": "2026-10-10",
                        "matched": True, "open_item_id": "INV-002"},
                   ]})
    # different value date -> not a strict duplicate; but INV-002 has no open item
    assert rc == 2


def test_matched_open_item_unknown_rejected():
    """A matched entry pointing at an open_item_id that does not exist is
    rejected — allocation must be to a real open item."""
    rc, err = run({"account": "DE89", "opening": 100.0, "closing": 200.0,
                   "open_items": [{"id": "INV-001", "amount": 100.0}],
                   "entries": [{"amount": 100.0, "reference": "A", "date": "2026-10-09",
                                "matched": True, "open_item_id": "INV-999"}]})
    assert rc == 2
    assert "INV-999" in err or "open item" in err.lower()


def test_unallocated_total_above_tolerance_rejected():
    """An unallocated total at/above the rounding tolerance (0.01) with no
    reason code is rejected."""
    rc, err = run({"account": "DE89", "opening": 0.0, "closing": 100.01,
                   "entries": [{"amount": 100.01, "reference": "A", "date": "2026-10-09"}]})
    assert rc == 2
    assert "unallocated" in err.lower()


def test_unallocated_with_reason_accepted():
    rc, err = run({"account": "DE89", "opening": 0.0, "closing": 100.0,
                   "entries": [{"amount": 100.0, "reference": "A", "date": "2026-10-09",
                                "matched": False, "reason_code": "UNALLOCATED"}]})
    assert rc == 0, err


def test_balance_equation_opening_plus_entries():
    """opening + sum(entries) must equal closing."""
    rc, err = run({"account": "DE89", "opening": 50.0, "closing": 250.0,
                   "entries": [{"amount": 100.0, "reference": "A", "date": "2026-10-09",
                                "matched": True, "open_item_id": "INV-001"},
                               {"amount": 100.0, "reference": "B", "date": "2026-10-09",
                                "matched": True, "open_item_id": "INV-002"}],
                   "open_items": [{"id": "INV-001", "amount": 100.0},
                                  {"id": "INV-002", "amount": 100.0}]})
    assert rc == 0, err
