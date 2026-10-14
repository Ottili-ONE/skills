"""Tests for dsgvo-ai-act-labeling scripts: classify, label_check, register."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"


def run(script, args):
    r = subprocess.run([sys.executable, str(SCRIPTS / script), *args],
                       capture_output=True, text=True)
    return r.returncode, json.loads(r.stdout) if r.stdout.strip() else {}


def test_classify_assist():
    meta = {"human_authored": True, "ai_produced_substantive_part": False,
            "published_to_inform_public": True}
    code, out = run("classify_content.py", ["--meta", _write(meta)])
    assert code == 0 and out["class"] == "assist"


def test_classify_disclose():
    meta = {"human_authored": False, "ai_produced_substantive_part": True,
            "published_to_inform_public": True}
    code, out = run("classify_content.py", ["--meta", _write(meta)])
    assert code == 0 and out["class"] == "disclose"


def test_classify_ambiguous_rejected():
    meta = {"human_authored": True}
    code, out = run("classify_content.py", ["--meta", _write(meta)])
    assert code == 1 and out["reason"] == "ambiguous"


def test_label_check_exempt(tmp_path):
    ev = tmp_path / "evidence.txt"; ev.write_text("review notes")
    (tmp_path / "evidence.txt.sha256").write_text(hashlib.sha256(ev.read_bytes()).hexdigest())
    rec = tmp_path / "rec.json"
    rec.write_text(json.dumps({
        "content_id": "c1", "reviewer": "Anna M.", "review_date": "2026-10-10",
        "review_decision": "approved",
        "editorial_responsibility_holder": "Anna M. (editor)",
        "review_evidence_path": "evidence.txt"}))
    code, out = run("label_check.py", ["--record", str(rec)])
    assert code == 0 and out["result"] == "EXEMPT"


def test_label_check_requires_review(tmp_path):
    rec = tmp_path / "rec.json"
    rec.write_text(json.dumps({
        "content_id": "c1", "reviewer": "Anna M.", "review_date": "2026-10-10",
        "review_decision": "rejected",
        "editorial_responsibility_holder": "Anna M. (editor)",
        "review_evidence_path": "missing.txt"}))
    code, out = run("label_check.py", ["--record", str(rec)])
    assert code == 1 and out["result"] == "LABEL"
    assert "human_review_done" in out["failing_conjuncts"]


def test_label_check_missing_fields(tmp_path):
    rec = tmp_path / "rec.json"
    rec.write_text(json.dumps({"content_id": "c1"}))
    code, out = run("label_check.py", ["--record", str(rec)])
    assert code == 2


def test_register_emits_row(tmp_path):
    uc = tmp_path / "uc.json"
    uc.write_text(json.dumps({
        "use_case_id": "ai-blog", "purpose": "draft blog posts",
        "data_categories": ["text"], "data_subjects": ["customers"],
        "lawful_basis": "legitimate_interest", "retention_class": "6y",
        "processor_list": []}))
    out = tmp_path / "reg.jsonl"
    code, res = run("processing_register.py", ["--use-case", str(uc), "--out", str(out)])
    assert code == 0 and out.exists()


def test_register_missing_field(tmp_path):
    uc = tmp_path / "uc.json"
    uc.write_text(json.dumps({"use_case_id": "x"}))
    code, out = run("processing_register.py", ["--use-case", str(uc), "--out", str(tmp_path / "r.jsonl")])
    assert code == 1 and "missing" in out


def _write(obj):
    import tempfile
    f = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
    json.dump(obj, f); f.close()
    return f.name
