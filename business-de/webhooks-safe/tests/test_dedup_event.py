"""Tests for dedup_event.py: new vs duplicate, ledger persistence."""
import json
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "dedup_event.py"


def run(event_id, ledger):
    r = subprocess.run([sys.executable, str(SCRIPT), "--event-id", event_id,
                        "--ledger", str(ledger)], capture_output=True, text=True)
    return r.returncode, json.loads(r.stdout)


def test_new_then_duplicate(tmp_path):
    ledger = tmp_path / "l.jsonl"
    code, out = run("evt-1", ledger)
    assert code == 0 and out["result"] == "new"
    code, out = run("evt-1", ledger)
    assert code == 1 and out["result"] == "duplicate"
    code, out = run("evt-2", ledger)
    assert code == 0 and out["result"] == "new"


def test_corrupt_line_does_not_block(tmp_path):
    ledger = tmp_path / "l.jsonl"
    ledger.write_text("not json\n", encoding="utf-8")
    code, out = run("evt-1", ledger)
    assert code == 0
