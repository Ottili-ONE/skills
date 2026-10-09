"""Offline, deterministic tests for the dsgvo-ai-act-labeling scripts."""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REG = ROOT / "scripts" / "process_register.py"
LABEL = ROOT / "scripts" / "disclosure_label.py"


def run(script, *args):
    return subprocess.run([sys.executable, str(script), *args],
                          capture_output=True, text=True)


def test_register_requires_art30_fields():
    act = {"controller": "Ottili GmbH", "legal_basis": "art6_1b_contract",
           "purpose": "x"}
    p = Path("/tmp/_act_missing.json"); p.write_text(json.dumps(act))
    r = run(REG, "--activity", str(p), "--register", "/tmp/_reg.jsonl")
    assert r.returncode != 0
    assert "missing fields" in r.stderr


def test_register_unknown_legal_basis():
    act = {"controller": "Ottili GmbH", "legal_basis": "bogus", "purpose": "x",
           "data_subject_categories": [], "data_categories": [], "recipients": [],
           "retention_period": "10y", "security_measures": "encryption"}
    p = Path("/tmp/_act_bad.json"); p.write_text(json.dumps(act))
    r = run(REG, "--activity", str(p), "--register", "/tmp/_reg2.jsonl")
    assert r.returncode != 0
    assert "legal basis" in r.stderr


def test_register_appends_entry():
    act = {"controller": "Ottili GmbH", "legal_basis": "art6_1b_contract",
           "purpose": "order fulfillment", "data_subject_categories": ["customers"],
           "data_categories": ["name", "address"], "recipients": ["carrier"],
           "retention_period": "10y", "security_measures": "TLS"}
    p = Path("/tmp/_act_ok.json"); p.write_text(json.dumps(act))
    q = Path("/tmp/_reg3.jsonl"); q.unlink(missing_ok=True)
    r = run(REG, "--activity", str(p), "--register", str(q))
    assert r.returncode == 0, r.stderr
    rec = json.loads(q.read_text().splitlines()[0])
    assert rec["legal_basis"] == "art6_1b_contract"
    assert rec["personal_data"] is True


def test_label_high_risk_missing_evidence_blocks():
    sys_def = {"name": "recruiter-ai", "ai_type": "high-risk", "human_review": {}}
    p = Path("/tmp/_sys_hr.json"); p.write_text(json.dumps(sys_def))
    r = run(LABEL, "--system", str(p))
    assert r.returncode != 0
    assert "BLOCKING" in r.stderr


def test_label_high_risk_approved_with_evidence():
    ev = Path("/tmp/_evidence.txt"); ev.write_text("review evidence body")
    sys_def = {"name": "recruiter-ai", "ai_type": "high-risk",
               "human_review": {"reviewer_id": "lawyer-1", "reviewed_at": "2026-10-09",
                                "evidence_path": str(ev)}}
    p = Path("/tmp/_sys_hr2.json"); p.write_text(json.dumps(sys_def))
    r = run(LABEL, "--system", str(p))
    assert r.returncode == 0, r.stderr
    out = json.loads(r.stdout)
    assert out["risk_class"] == "high-risk"
    assert out["human_review_status"] == "approved"
    assert "evidence_sha256" in out


def test_label_transparency_only():
    sys_def = {"name": "support-bot", "ai_type": "chatbot",
               "human_review": {"reviewer_id": "ops-1", "reviewed_at": "2026-10-09",
                                "evidence_path": "/tmp/_evidence.txt"}}
    p = Path("/tmp/_sys_chat.json"); p.write_text(json.dumps(sys_def))
    r = run(LABEL, "--system", str(p))
    assert r.returncode == 0, r.stderr
    out = json.loads(r.stdout)
    assert out["article_50_required"] is True
    assert out["label"] == "article-50-disclosure"


def test_label_not_ai():
    sys_def = {"name": "invoice-export", "ai_type": "none"}
    p = Path("/tmp/_sys_none.json"); p.write_text(json.dumps(sys_def))
    r = run(LABEL, "--system", str(p))
    assert r.returncode == 0, r.stderr
    out = json.loads(r.stdout)
    assert out["risk_class"] == "not-ai"
    assert out["article_50_required"] is False
