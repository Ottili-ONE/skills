"""Near-miss trigger tests for dsgvo-ai-act-labeling.

The traps: an unknown legal basis must block, not be guessed; an unknown
ai_type must block, not be classified as general; a high-risk system without
human-review evidence is BLOCKING; a transparency-only system without a
reviewer is BLOCKING; and the register is append-only GoBD evidence.
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DISC = ROOT / "scripts" / "disclosure_label.py"
REG = ROOT / "scripts" / "process_register.py"


def run(script, *args):
    return subprocess.run([sys.executable, str(script), *args],
                          capture_output=True, text=True)


def test_unknown_legal_basis_blocks():
    """Exactly one Art. 6(1) basis per activity; an unrecognised basis blocks."""
    with tempfile.TemporaryDirectory() as d:
        act = Path(d) / "a.json"
        act.write_text(json.dumps({
            "controller": "Ottili GmbH", "purpose": "payroll",
            "legal_basis": "magic", "data_subject_categories": ["employees"],
            "data_categories": ["salary"], "recipients": [" payroll"],
            "retention_period": "10y", "security_measures": ["encrypted"],
        }))
        r = run(REG, "--activity", str(act), "--register", str(Path(d) / "reg.jsonl"))
        assert r.returncode == 1
        assert "magic" in r.stderr


def test_no_personal_data_still_recorded():
    """Even an activity with no personal data gets an entry, marked
    personal_data: false, so the decision is auditable."""
    with tempfile.TemporaryDirectory() as d:
        act = Path(d) / "a.json"
        act.write_text(json.dumps({
            "controller": "Ottili GmbH", "purpose": "anonymised stats",
            "legal_basis": "art6_1f_legit", "personal_data": False,
            "data_subject_categories": [], "data_categories": [],
            "recipients": [], "retention_period": "1y",
            "security_measures": ["aggregated"],
        }))
        r = run(REG, "--activity", str(act), "--register", str(Path(d) / "reg.jsonl"))
        assert r.returncode == 0, r.stderr
        entry = json.loads(r.stdout)["entry"]
        assert entry["personal_data"] is False
        assert "note" in entry


def test_unknown_ai_type_blocks():
    """Do not invent a classification for an unknown ai_type."""
    with tempfile.TemporaryDirectory() as d:
        sys_path = Path(d) / "sys.json"
        sys_path.write_text(json.dumps({"name": "X", "ai_type": "quantum-agi"}))
        r = run(DISC, "--system", str(sys_path))
        assert r.returncode == 1
        assert "quantum-agi" in r.stderr


def test_high_risk_without_evidence_is_blocking():
    """High-risk / Annex III (Art. 6) needs human review + an evidence file."""
    with tempfile.TemporaryDirectory() as d:
        sys_path = Path(d) / "sys.json"
        sys_path.write_text(json.dumps({
            "name": "hiring-bot", "ai_type": "high-risk",
            "human_review": {"reviewer_id": "H1", "reviewed_at": "2026-10-09"},
        }))
        r = run(DISC, "--system", str(sys_path))
        assert r.returncode == 1
        assert "BLOCKING" in r.stderr


def test_transparency_only_without_reviewer_is_blocking():
    """Art. 50(1)-(4) transparency systems still need human-review evidence."""
    with tempfile.TemporaryDirectory() as d:
        sys_path = Path(d) / "sys.json"
        sys_path.write_text(json.dumps({"name": "chat", "ai_type": "chatbot"}))
        r = run(DISC, "--system", str(sys_path))
        assert r.returncode == 1
        assert "human-review" in r.stderr


def test_transparency_only_with_evidence_labelled():
    with tempfile.TemporaryDirectory() as d:
        ev = Path(d) / "ev.md"
        ev.write_text("review notes")
        sys_path = Path(d) / "sys.json"
        sys_path.write_text(json.dumps({
            "name": "chat", "ai_type": "chatbot",
            "human_review": {"reviewer_id": "H1", "reviewed_at": "2026-10-09",
                             "evidence_path": str(ev)},
        }))
        r = run(DISC, "--system", str(sys_path))
        assert r.returncode == 0, r.stderr
        label = json.loads(r.stdout)
        assert label["risk_class"] == "transparency-only"
        assert label["article_50_paragraph"] == "1-4"
        assert "evidence_sha256" in label


def test_general_ai_documented_not_disclosed():
    with tempfile.TemporaryDirectory() as d:
        sys_path = Path(d) / "sys.json"
        sys_path.write_text(json.dumps({"name": "model", "ai_type": "general"}))
        r = run(DISC, "--system", str(sys_path))
        assert r.returncode == 0
        label = json.loads(r.stdout)
        assert label["article_50_required"] is False
        assert label["article_95_documented"] is True


def test_register_is_append_only():
    """Editing an entry in place breaks GoBD immutability. Superseding an
    entry appends a new one with a new recorded_at, it never mutates."""
    with tempfile.TemporaryDirectory() as d:
        reg = Path(d) / "reg.jsonl"
        act = Path(d) / "a.json"
        act.write_text(json.dumps({
            "controller": "Ottili GmbH", "purpose": "payroll",
            "legal_basis": "art6_1b_contract",
            "data_subject_categories": ["employees"], "data_categories": ["salary"],
            "recipients": ["payroll"], "retention_period": "10y",
            "security_measures": ["encrypted"],
        }))
        run(REG, "--activity", str(act), "--register", str(reg))
        n1 = len([l for l in reg.read_text().splitlines() if l.strip()])
        run(REG, "--activity", str(act), "--register", str(reg))
        n2 = len([l for l in reg.read_text().splitlines() if l.strip()])
        assert n1 == 1 and n2 == 2
