"""Offline, deterministic tests for the dsgvo-ai-act-labeling scripts."""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REG = ROOT / "scripts" / "process_register.py"
LABEL = ROOT / "scripts" / "disclosure_label.py"
LABEL_CHECK = ROOT / "scripts" / "label_check.py"


def run(script, *args):
    return subprocess.run([sys.executable, str(script), *args],
                          capture_output=True, text=True)



def test_register_entry_carries_recorded_at():
    """A GoBD register entry must record when it was written; the old
    script copied the caller's field and wrote `recorded_at: null`."""
    import tempfile, os
    act = {"controller": "Ottili GmbH", "purpose": "order fulfillment",
           "legal_basis": "art6_1b_contract",
           "data_subject_categories": ["customers"], "data_categories": ["name"],
           "recipients": ["carrier"], "retention_period": "10y",
           "security_measures": "TLS 1.3"}
    act_path = Path("/tmp/_dsgvo_act.json"); act_path.write_text(json.dumps(act))
    store = tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False)
    store.close()
    r = run(REG, "--activity", str(act_path), "--register", store.name)
    assert r.returncode == 0, r.stderr
    line = json.loads(Path(store.name).read_text(encoding="utf-8").strip())
    assert line.get("recorded_at"), "recorded_at must not be null"
    os.unlink(store.name)


def test_label_general_ai_has_article_95_flag():
    """General AI (Art. 95) is documented, not disclosed."""
    import tempfile, os
    sys_path = Path("/tmp/_dsgvo_sys.json")
    sys_path.write_text(json.dumps({"name": "report-ml", "ai_type": "general"}))
    r = run(LABEL, "--system", str(sys_path))
    assert r.returncode == 0, r.stderr
    data = json.loads(r.stdout)
    assert data["risk_class"] == "general"
    assert data["article_50_required"] is False
    assert data["article_95_documented"] is True
    assert data["human_review_status"] == "not-required"

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


def test_label_high_risk_writes_out_file():
    ev = Path("/tmp/_ev_out.txt"); ev.write_text("evidence")
    sys_def = {"name": "recruiter-ai", "ai_type": "high-risk",
               "human_review": {"reviewer_id": "lawyer-1", "reviewed_at": "2026-10-09",
                                "evidence_path": str(ev)}}
    p = Path("/tmp/_sys_out.json"); p.write_text(json.dumps(sys_def))
    out = Path("/tmp/_label_out.json"); out.unlink(missing_ok=True)
    r = run(LABEL, "--system", str(p), "--out", str(out))
    assert r.returncode == 0, r.stderr
    assert out.exists()
    written = json.loads(out.read_text())
    assert written["label"] == "article-50-disclosure-hr"
    assert written["retention_years"] == 10


def test_label_rejects_bad_reviewed_at():
    sys_def = {"name": "support-bot", "ai_type": "chatbot",
               "human_review": {"reviewer_id": "ops-1", "reviewed_at": "09/10/2026"}}
    p = Path("/tmp/_sys_bad_date.json"); p.write_text(json.dumps(sys_def))
    r = run(LABEL, "--system", str(p))
    assert r.returncode != 0
    assert "ISO-8601" in r.stderr


def test_label_transparency_missing_reviewer_blocks():
    sys_def = {"name": "support-bot", "ai_type": "chatbot", "human_review": {}}
    p = Path("/tmp/_sys_noreview.json"); p.write_text(json.dumps(sys_def))
    r = run(LABEL, "--system", str(p))
    assert r.returncode != 0
    assert "human-review evidence" in r.stderr


def test_label_general_ai_no_disclosure():
    sys_def = {"name": "embeddings", "ai_type": "general"}
    p = Path("/tmp/_sys_gen.json"); p.write_text(json.dumps(sys_def))
    r = run(LABEL, "--system", str(p))
    assert r.returncode == 0, r.stderr
    out = json.loads(r.stdout)
    assert out["risk_class"] == "general"
    assert out["article_50_required"] is False
    assert out["human_review_status"] == "not-required"


def test_label_unknown_ai_type_blocks():
    sys_def = {"name": "x", "ai_type": "magic-ai"}
    p = Path("/tmp/_sys_unknown.json"); p.write_text(json.dumps(sys_def))
    r = run(LABEL, "--system", str(p))
    assert r.returncode != 0


def test_label_check_missing_fields_blocks():
    """A label missing required fields must fail the check."""
    import tempfile
    from dsgvo_test_helpers import write_label
    bad = {"system": "x", "risk_class": "high", "reviewed_at": "2026-01-01T00:00:00Z",
           "reviewer": "a", "checksum": "deadbeef"}
    p = write_label(bad)
    r = run(LABEL_CHECK, "--label", str(p))
    assert r.returncode == 1, r.stderr
    out = json.loads(r.stdout)
    assert any("missing" in e for e in out["errors"])


def test_label_check_high_risk_requires_approval():
    """High-risk + human_review_status != approved is BLOCKING."""
    from dsgvo_test_helpers import write_label
    lab = {"system": "x", "risk_class": "high", "art6_status": "ok",
           "art50_status": "required", "human_review_status": "pending",
           "reviewed_at": "2026-01-01T00:00:00Z", "reviewer": "a",
           "checksum": "deadbeef"}
    p = write_label(lab)
    r = run(LABEL_CHECK, "--label", str(p))
    assert r.returncode == 1
    out = json.loads(r.stdout)
    assert any("BLOCKING" in e for e in out["errors"])


def test_label_check_checksum_tamper_detected():
    """A modified label body must fail the checksum."""
    import hashlib
    from dsgvo_test_helpers import write_label
    body = {"system": "x", "risk_class": "low", "art6_status": "n/a",
            "art50_status": "not-required", "human_review_status": "approved",
            "reviewed_at": "2026-01-01T00:00:00Z", "reviewer": "a"}
    p = write_label(body)
    chk = hashlib.sha256(p.read_bytes()).hexdigest()
    lab = json.loads(p.read_text()); lab["checksum"] = chk; p.write_text(json.dumps(lab))
    # tamper the content after computing checksum
    lab2 = json.loads(p.read_text()); lab2["risk_class"] = "high"
    p.write_text(json.dumps(lab2))
    r = run(LABEL_CHECK, "--label", str(p))
    assert r.returncode == 1
    out = json.loads(r.stdout)
    assert any("checksum" in e for e in out["errors"])
