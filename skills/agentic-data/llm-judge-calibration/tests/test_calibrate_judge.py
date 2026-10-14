"""Tests for scripts/calibrate_judge.py (offline, deterministic)."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "calibrate_judge.py"
FIX = Path(__file__).resolve().parent / "fixtures"

# Judge/teacher provenance required for every calibration report (see the
# provenance gate in scripts/calibrate_judge.py). Distinct models with
# distinct prompt hashes: the judge is not the system under test.
PROV = (
    "--judge-model", "claude-sonnet-4",
    "--generator-model", "gpt-4.1",
    "--judge-prompt-sha", "a1b2c3d4",
    "--generator-prompt-sha", "e5f6g7h8",
)


def run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True)


def test_high_agreement_passes() -> None:
    r = run("calibrate", "--rows", str(FIX / "high.jsonl"), *PROV)
    assert r.returncode == 0, r.stderr
    assert "PASS" in r.stderr


def test_low_agreement_fails() -> None:
    r = run("calibrate", "--rows", str(FIX / "low.jsonl"), *PROV)
    assert r.returncode == 1
    assert "agreement" in r.stderr


def test_position_bias_detected() -> None:
    r = run("calibrate", "--rows", str(FIX / "biased.jsonl"), *PROV)
    assert r.returncode == 1
    assert "position bias" in r.stderr


def test_drift_detected() -> None:
    r = run("calibrate", "--rows", str(FIX / "high.jsonl"), "--baseline", str(FIX / "baseline.jsonl"), "--max-drift", "0.01", *PROV)
    assert r.returncode == 1
    assert "drift" in r.stderr


def test_json_report() -> None:
    out = FIX / "report_test.json"
    out.unlink(missing_ok=True)
    r = run("calibrate", "--rows", str(FIX / "high.jsonl"), "--json", str(out), *PROV)
    assert r.returncode == 0
    data = json.loads(out.read_text())
    assert data["ok"] is True
    assert data["krippendorff_alpha"] >= 0.6
    # provenance must be recorded in the report or the score is not auditable
    assert data["judge_model"] == "claude-sonnet-4"
    assert data["generator_model"] == "gpt-4.1"
    assert data["judge_prompt_sha"] == "a1b2c3d4"
    assert data["generator_prompt_sha"] == "e5f6g7h8"


def test_report_rejects_missing_provenance() -> None:
    r = run("calibrate", "--rows", str(FIX / "high.jsonl"))
    assert r.returncode == 1
    assert "provenance" in r.stderr
    assert "--judge-model" in r.stderr


def test_report_rejects_circular_judge_and_teacher() -> None:
    r = run(
        "calibrate", "--rows", str(FIX / "high.jsonl"),
        "--judge-model", "gpt-4.1", "--generator-model", "gpt-4.1",
        "--judge-prompt-sha", "same", "--generator-prompt-sha", "same",
    )
    assert r.returncode == 1
    assert "circular" in r.stderr


def test_report_accepts_separated_models_with_same_prompt() -> None:
    """Different model, same prompt is acceptable per the decision table
    (different model OR different prompt = acceptable)."""
    r = run(
        "calibrate", "--rows", str(FIX / "high.jsonl"),
        "--judge-model", "claude-sonnet-4", "--generator-model", "gpt-4.1",
        "--judge-prompt-sha", "same", "--generator-prompt-sha", "same",
    )
    assert r.returncode == 0, r.stderr


def test_min_items_rejects_tiny_set() -> None:
    # The shipped fixtures have 30 items; a 3-item file must be rejected.
    small = FIX / "tiny.jsonl"
    small.write_text("".join(
        json.dumps({"id": f"t{i}", "scores": [5, 5, 5], "gold": 5}) + "\n"
        for i in range(3)
    ))
    r = run("calibrate", "--rows", str(small), "--min-items", "30", *PROV)
    assert r.returncode == 1
    assert "minimum is 30" in r.stderr


def test_min_items_accepts_default() -> None:
    r = run("calibrate", "--rows", str(FIX / "high.jsonl"), *PROV)
    assert r.returncode == 0, r.stderr


def test_missing_gold_label_rejected() -> None:
    bad = FIX / "nogold.jsonl"
    bad.write_text(json.dumps({"id": "x", "scores": [5, 5, 5]}) + "\n" * 30)
    r = run("calibrate", "--rows", str(bad), *PROV)
    assert r.returncode == 1
    assert "no gold label" in r.stderr


def test_degenerate_set_rejected() -> None:
    # 30 items, every score identical -> the set spans one score and cannot be
    # calibrated (alpha would be 1.0 for a trivial reason).
    deg = FIX / "degenerate.jsonl"
    deg.write_text("".join(
        json.dumps({"id": f"d{i}", "scores": [3, 3, 3], "gold": 3}) + "\n"
        for i in range(30)
    ))
    r = run("calibrate", "--rows", str(deg), *PROV)
    assert r.returncode == 1
    assert "degenerate" in r.stderr


def test_baseline_id_alignment_rejected() -> None:
    # baseline.jsonl reuses the high ids; a baseline with different ids must be
    # rejected because drift is only meaningful on the same items.
    other = FIX / "other_ids.jsonl"
    other.write_text("".join(
        json.dumps({"id": f"z{i:02d}", "scores": [3, 3, 3], "gold": 3}) + "\n"
        for i in range(30)
    ))
    r = run(
        "calibrate", "--rows", str(FIX / "high.jsonl"),
        "--baseline", str(other), "--max-drift", "0.01", *PROV,
    )
    assert r.returncode == 1
    assert "missing from the baseline" in r.stderr


def test_baseline_drift_detected_with_aligned_ids() -> None:
    # baseline.jsonl shares the high ids but scores are shifted +1, so drift is
    # non-zero and must be detected when the threshold is tight.
    r = run(
        "calibrate", "--rows", str(FIX / "high.jsonl"),
        "--baseline", str(FIX / "baseline.jsonl"), "--max-drift", "0.01", *PROV,
    )
    assert r.returncode == 1
    assert "drift" in r.stderr


def test_rubric_lint_rejects_empty_anti_examples() -> None:
    rubric = FIX / "rubric_empty_anti.yaml"
    rubric.write_text(
        "rubric_id: empty-anti\n"
        "scale: 1-3\n"
        "points:\n"
        "  - score: 1\n"
        "    definition: poor\n"
        "    example: x\n"
        "  - score: 2\n"
        "    definition: mid\n"
        "    example: y\n"
        "    anti_examples: []\n"
        "  - score: 3\n"
        "    definition: good\n"
        "    example: z\n"
        "    anti_examples: [bad]\n"
    )
    r = run("rubric", str(rubric))
    assert r.returncode == 1
    assert "empty 'anti_examples'" in r.stderr


def test_rubric_lint_passes() -> None:
    rubric = FIX / "rubric_good.yaml"
    rubric.write_text(
        "rubric_id: task-safety-v1\n"
        "scale: 1-5\n"
        "points:\n"
        "  - score: 1\n"
        "    definition: harmful\n"
        "    example: refuses the request\n"
        "  - score: 3\n"
        "    definition: partially safe\n"
        "    example: gives a partial answer\n"
        "    anti_examples: [refuses entirely]\n"
        "  - score: 5\n"
        "    definition: safe and complete\n"
        "    example: gives the safe full answer\n"
        "    anti_examples: [omits the safety step]\n"
    )
    r = run("rubric", str(rubric))
    assert r.returncode == 0, r.stderr
    assert "PASS: rubric" in r.stderr


def test_rubric_lint_rejects_missing_examples() -> None:
    rubric = FIX / "rubric_bad.yaml"
    rubric.write_text(
        "rubric_id: bad\n"
        "scale: 1-5\n"
        "points:\n"
        "  - score: 1\n"
        "    definition: poor\n"
        "  - score: 5\n"
        "    definition: good\n"
    )
    r = run("rubric", str(rubric))
    assert r.returncode == 1
    assert "no 'example'" in r.stderr


def test_rubric_lint_rejects_noncontiguous() -> None:
    """Scores must be strictly increasing; a duplicate score is a defect."""
    rubric = FIX / "rubric_gap.yaml"
    rubric.write_text(
        "rubric_id: gap\n"
        "scale: 1-5\n"
        "points:\n"
        "  - score: 1\n"
        "    definition: poor\n"
        "    example: x\n"
        "  - score: 1\n"
        "    definition: duplicate\n"
        "    example: y\n"
        "    anti_examples: [z]\n"
    )
    r = run("rubric", str(rubric))
    assert r.returncode == 1
    assert "not strictly increasing" in r.stderr

