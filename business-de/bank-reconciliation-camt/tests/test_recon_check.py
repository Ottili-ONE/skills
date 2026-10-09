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
             "entries": [{"amount": 100.0, "reference": "A", "date": "2026-10-09", "matched": True}]})
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
                          "matched": False, "reason_code": "OPEN"}]})
    assert r.returncode == 0, r.stderr
